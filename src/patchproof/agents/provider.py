from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


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


class OpenAIProvider(ModelProvider):
    def __init__(
        self,
        model: str | None = None,
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set"
            )

        self.model = (
            model
            or os.getenv(
                "PATCHPROOF_MODEL",
                "gpt-5.6-terra",
            )
        )

        self.client = OpenAI(
            api_key=api_key,
        )

    def generate(
        self,
        messages: list[dict[str, str]],
    ) -> ModelResponse:
        input_text = "\n\n".join(
            f"{message['role'].upper()}:\n"
            f"{message['content']}"
            for message in messages
        )

        response = self.client.responses.create(
            model=self.model,
            input=input_text,
        )

        usage = getattr(
            response,
            "usage",
            None,
        )

        input_tokens = (
            getattr(
                usage,
                "input_tokens",
                None,
            )
            if usage
            else None
        )

        output_tokens = (
            getattr(
                usage,
                "output_tokens",
                None,
            )
            if usage
            else None
        )

        return ModelResponse(
            text=response.output_text,
            raw=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
        )
