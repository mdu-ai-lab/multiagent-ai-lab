# The request, the streamed events and the Harness handle that a route gets. A route uses
# only this handle on the model side, so the harness decides what goes into the prompt and
# which limits apply

from collections.abc import Callable, Generator, Iterator
from dataclasses import dataclass, field

from mrag import prompts
from mrag.harness.context import Turn, build_messages
from mrag.harness.limits import Deadline
from mrag.harness.settings import ProfileSettings
from mrag.llm_client import LLMClient


@dataclass(frozen=True)
class Request:
    message: str
    history: list[Turn] = field(default_factory=list)
    route: str = "chat"


@dataclass(frozen=True)
class Delta:
    # A piece of the answer text
    text: str


@dataclass(frozen=True)
class Done:
    # The whole answer and the totals of the request
    answer: str
    model_calls: int
    input_tokens: int
    output_tokens: int
    duration_ms: int


@dataclass(frozen=True)
class Error:
    # The kind of error and a short message. Answer pieces sent before it were real
    kind: str
    message: str


Event = Delta | Done | Error


@dataclass
class Harness:
    request: Request
    settings: ProfileSettings
    client: LLMClient
    deadline: Deadline

    def answer(self, system_prompt: str = "chat_system") -> Iterator[str]:
        # Streams the main model's answer within the token budget, the answer cap and the
        # time limit. Closing the stream also closes the model call
        self.deadline.check()
        system = prompts.load(system_prompt).format()
        messages = build_messages(
            system, self.request.history, self.request.message, self.settings.prompt_budget
        )
        stream = self.client.chat_stream(
            messages, max_tokens=self.settings.answer_tokens, timeout=self.deadline.remaining()
        )
        try:
            for piece in stream:
                yield piece
                self.deadline.check()
        finally:
            # The model clients return generators. Closing one stops its model call
            if isinstance(stream, Generator):
                stream.close()


# A route turns a request into answer pieces through the handle
Route = Callable[[Harness], Iterator[str]]
