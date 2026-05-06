"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from multi_agent_research_lab.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    metadata: dict[str, object] = field(default_factory=dict)


class LLMClient:
    """Provider-agnostic LLM client.

    Provider order:
    1. local GGUF model through llama-cpp-python,
    2. deterministic heuristic fallback.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with production-safe fallback."""

        if self.settings.local_llm_enabled:
            local_response = self._try_local_model(system_prompt, user_prompt)
            if local_response is not None:
                return local_response

        logger.info(
            "llm.model provider=heuristic_fallback "
            "reason=local_llm_disabled_or_unavailable"
        )
        return self._heuristic_complete(system_prompt, user_prompt)

    def _try_local_model(self, system_prompt: str, user_prompt: str) -> LLMResponse | None:
        model_path = Path(self.settings.local_model_path)
        if not model_path.is_absolute():
            model_path = Path.cwd() / model_path
        if not model_path.exists():
            logger.warning("llm.model provider=local_gguf status=missing path=%s", model_path)
            return None

        try:
            logger.info(
                "llm.model provider=local_gguf path=%s n_ctx=%s n_gpu_layers=%s max_tokens=%s",
                model_path,
                self.settings.local_model_n_ctx,
                self.settings.local_model_n_gpu_layers,
                self.settings.local_model_max_tokens,
            )
            llm = _load_llama_model(
                str(model_path),
                self.settings.local_model_n_ctx,
                self.settings.local_model_n_gpu_layers,
            )
            prompt = _format_prompt(system_prompt, user_prompt)
            result = llm(
                prompt,
                max_tokens=self.settings.local_model_max_tokens,
                temperature=self.settings.local_model_temperature,
                stop=["<|im_end|>", "</s>"],
            )
        except Exception as exc:
            logger.warning("llm.model provider=local_gguf status=failed error=%s", exc)
            return None

        choice = result["choices"][0]
        raw_text = str(choice.get("text", ""))
        text = _clean_model_output(raw_text)
        usage = result.get("usage", {})
        if not text:
            logger.warning(
                "llm.model provider=local_gguf status=empty_final_answer fallback=heuristic"
            )
            fallback = self._heuristic_complete(system_prompt, user_prompt)
            return LLMResponse(
                content=fallback.content,
                input_tokens=usage.get("prompt_tokens") or fallback.input_tokens,
                output_tokens=usage.get("completion_tokens") or fallback.output_tokens,
                cost_usd=0.0,
                metadata={
                    "provider": "heuristic_fallback",
                    "fallback_from": "local_gguf",
                    "model_path": str(model_path),
                },
            )

        logger.info(
            "llm.model provider=local_gguf status=ok model=%s input_tokens=%s output_tokens=%s",
            model_path.name,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        return LLMResponse(
            content=text,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            cost_usd=0.0,
            metadata={
                "provider": "local_gguf",
                "model_path": str(model_path),
                "model_name": model_path.name,
                "n_ctx": self.settings.local_model_n_ctx,
                "n_gpu_layers": self.settings.local_model_n_gpu_layers,
            },
        )

    def _heuristic_complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        words = (system_prompt + " " + user_prompt).split()
        summary = " ".join(user_prompt.split()[:120])
        content = (
            "Local heuristic fallback response:\n"
            f"{summary}\n\n"
            "Key reminder: configure LOCAL_MODEL_PATH to enable the local GGUF model."
        )
        return LLMResponse(
            content=content,
            input_tokens=len(words),
            output_tokens=len(content.split()),
            cost_usd=0.0,
            metadata={"provider": "heuristic_fallback"},
        )


def _format_prompt(system_prompt: str, user_prompt: str) -> str:
    no_think_user_prompt = user_prompt
    if "/no_think" not in no_think_user_prompt:
        no_think_user_prompt = f"{no_think_user_prompt}\n\n/no_think"
    return (
        "<|im_start|>system\n"
        "Do not reveal chain-of-thought. Do not write <think> tags. "
        "Answer directly and concisely. /no_think\n"
        f"{system_prompt}\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"{no_think_user_prompt}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
        "<think>\n\n</think>\n\n"
    )


def _clean_model_output(text: str) -> str:
    without_complete_think = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    if "<think>" in without_complete_think and "</think>" not in without_complete_think:
        without_complete_think = without_complete_think.split("<think>", maxsplit=1)[0]
    return without_complete_think.replace("</think>", "").strip()


@lru_cache(maxsize=2)
def _load_llama_model(model_path: str, n_ctx: int, n_gpu_layers: int) -> object:
    from llama_cpp import Llama

    return Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
    )
