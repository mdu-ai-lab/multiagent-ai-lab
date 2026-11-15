# harness.run(): the only entry of the harness. It runs the route of a request and streams
# its events: answer pieces, then Done with the request totals or Error. The request trace
# records the totals

import contextvars
from collections.abc import Generator, Mapping

from mrag import tracing
from mrag.config import get_settings
from mrag.harness.handle import Delta, Done, Error, Event, Harness, Request, Route
from mrag.harness.limits import Deadline, TimeLimitError
from mrag.harness.settings import HarnessError, for_profile
from mrag.llm_client import InputTooLongError, LLMError, ModelUnavailableError, get_client

# The first matching type names the error. InputTooLongError is also an LLMError
ERROR_KINDS: list[tuple[type[Exception], str]] = [
    (InputTooLongError, "input_too_long"),
    (ModelUnavailableError, "model_unavailable"),
    (LLMError, "model_error"),
    (TimeLimitError, "time_limit"),
    (HarnessError, "harness_error"),
]


# A generator, so a reader can close it: closing stops the model call
Events = Generator[Event, None, None]


def run(request: Request, routes: Mapping[str, Route]) -> Events:
    # Every step runs in one context. A web server can run each step in another thread with
    # a fresh copy of the context, which would lose the request trace between the steps
    return in_one_context(events(request, routes))


def in_one_context(steps: Events) -> Events:
    context = contextvars.copy_context()
    try:
        while True:
            try:
                yield context.run(next, steps)
            except StopIteration:
                return
    finally:
        context.run(steps.close)


def events(request: Request, routes: Mapping[str, Route]) -> Events:
    pieces: list[str] = []
    try:
        if request.route not in routes:
            raise HarnessError(f"Unknown route '{request.route}'")
        settings = for_profile(get_settings().profile)
        inputs = {"message": request.message, "earlier_turns": len(request.history)}
        with tracing.request(request.route, inputs) as totals:
            harness = Harness(request, settings, get_client(), Deadline(settings.time_limit_s))
            for piece in routes[request.route](harness):
                pieces.append(piece)
                yield Delta(piece)
            totals.output = "".join(pieces)
    except (LLMError, HarnessError, TimeLimitError) as error:
        kind = next(name for error_type, name in ERROR_KINDS if isinstance(error, error_type))
        yield Error(kind, str(error))
        return
    yield Done(
        "".join(pieces),
        totals.model_calls,
        totals.input_tokens,
        totals.output_tokens,
        totals.duration_ms,
    )
