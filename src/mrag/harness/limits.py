# Limits of one request: the time limit of the profile, counted from the start of the request

import time
from dataclasses import dataclass, field


class TimeLimitError(Exception):
    pass


@dataclass
class Deadline:
    seconds: float
    start: float = field(default_factory=time.monotonic)

    def remaining(self) -> float:
        return self.seconds - (time.monotonic() - self.start)

    def check(self) -> None:
        if self.remaining() <= 0:
            raise TimeLimitError(f"The request took longer than its limit of {self.seconds:g} s")
