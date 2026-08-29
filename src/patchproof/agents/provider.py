from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ModelResponse:
    text: str
    raw: Any | None = None

    input_tokens: int | None = None
    output_tokens: int | None = None

    model: str | None = None


class ModelProvider(ABC):
    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
    ) -> ModelResponse:
        raise NotImplementedError
