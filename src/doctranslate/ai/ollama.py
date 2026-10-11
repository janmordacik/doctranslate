"""Local Ollama provider and model-specific prompt strategies."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Mapping

from .context_backend import (
    AgentCapability,
    AgentTurnRequest,
    AgentTurnResponse,
    ContextualCapability,
    ContextualRequest,
    ContextualResult,
    decode_agent_turn_response,
    decode_contextual_results,
    require_agent_capability,
    require_contextual_capability,
)
from .contracts import BackendError

from .providers import HttpAiBackend
from .translation import Prompt, translate_prompt


_LANGUAGE_NAMES = {
    "en": "English",
    "cs": "Czech",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "pl": "Polish",
    "sk": "Slovak",
}


def is_translategemma_model(model: str) -> bool:
    """Return whether an Ollama tag belongs to the TranslateGemma family."""
    return model.strip().casefold().split("@", 1)[0].startswith("translategemma:")


def _language_name(code: str) -> str:
    normalized = code.strip().lower().replace("_", "-")
    return _LANGUAGE_NAMES.get(normalized, normalized)


@dataclass(frozen=True)
class OllamaPromptStrategy:
    """Versioned prompt contract selected from the concrete Ollama model tag."""

    strategy_id: str
    revision: str

    def build(self, source_language: str, target_language: str, text: str, *, structured: bool = False) -> str:
        source_code = source_language.strip().lower()
        target_code = target_language.strip().lower()
        source_name = _language_name(source_code)
        target_name = _language_name(target_code)
        prompt = (
            f"You are a professional {source_name} ({source_code}) to {target_name} ({target_code}) translator. "
            f"Your goal is to accurately convey the meaning and nuances of the original {source_name} text "
            f"while adhering to {target_name} grammar, vocabulary, and cultural sensitivities.\n"
        )
        if structured:
            prompt += (
                "Return only one JSON object with exactly the same document block and fragment IDs. "
                "Translate only the natural-language string values; do not add explanations, Markdown or HTML. "
                "Keep numeric tokens, placeholders, identifiers and the JSON structure unchanged. "
                f"Please translate the following {source_name} document data into {target_name}:\n\n"
            )
        else:
            prompt += (
                f"Produce only the {target_name} translation, without any additional explanations or commentary. "
                f"Please translate the following {source_name} text into {target_name}:\n\n"
            )
        return prompt + text


TRANSLATEGEMMA_STRATEGY = OllamaPromptStrategy(
    strategy_id="ollama-translategemma",
    revision="translategemma-prompt-v1",
)


def prompt_strategy_for_model(model: str) -> OllamaPromptStrategy | None:
    """Resolve TranslateGemma's prompt strategy, or None for legacy Ollama models."""
    return TRANSLATEGEMMA_STRATEGY if is_translategemma_model(model) else None


class OllamaBackend(HttpAiBackend):
    """Local Ollama backend kept behind the same provider-neutral contract."""

    provider_id = "ollama"
    name = "Ollama"

    def __init__(
        self,
        model: str,
        *,
        base_url: str = "http://localhost:11434",
        agent_tools_enabled: bool = False,
        **kwargs,
    ):
        super().__init__(model, base_url=base_url, **kwargs)
        # This flag is explicit configuration, not model-name autodetection.
        self.agent_tools_enabled = agent_tools_enabled

    def _call_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        *,
        target_variant: str = "auto",
    ) -> str:
        prompt = self._build_prompt(text, source_language, target_language, target_variant)
        strategy = prompt_strategy_for_model(self.model)
        data = prompt.user
        content = (
            strategy.build(source_language, target_language, data)
            if strategy is not None
            else (
                f"Translate from {source_language} to {target_language}. "
                "Return only the translation.\n\n" + data
            )
        )
        content = prompt.system + "\n\n" + content
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [{
                "role": "user",
                "content": content,
            }],
        }
        value = self._post("/api/chat", payload)
        if not isinstance(value, dict):
            raise self._invalid()
        message = value.get("message")
        if not isinstance(message, dict):
            raise self._invalid()
        return self._string(message.get("content"), "message.content")

    def contextual_capability(self) -> ContextualCapability:
        """Advertise the structured chat capability used by advanced mode."""
        if not self.model.strip():
            return ContextualCapability(False, "Ollama model ID is empty")
        strategy = prompt_strategy_for_model(self.model)
        revision = strategy.revision if strategy is not None else "ollama-contextual-v1"
        return ContextualCapability(True, prompt_revision=revision)


    def agent_capability(self) -> AgentCapability:
        """Expose agent turns only after an explicit provider/model smoke test."""
        if not self.agent_tools_enabled:
            return AgentCapability(
                False,
                "Ollama agent turns are disabled until an explicit smoke test succeeds",
            )
        return AgentCapability(True)

    def request_turn(self, request: AgentTurnRequest) -> AgentTurnResponse:
        """Send one strict JSON agent turn; orchestration remains outside the provider."""
        require_agent_capability(self)
        if not isinstance(request, AgentTurnRequest):
            raise BackendError("invalid_schema", "Agent request has an invalid type")
        if not 1 <= request.max_output_tokens <= 16384:
            raise BackendError("limit_exceeded", "max_output_tokens must be between 1 and 16384")
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "Return exactly one JSON object. Use either "
                    '{"type":"final","text":"..."} or '
                    '{"type":"tool","call_id":"id","name":"allowed tool",'
                    '"arguments":{}}. Never combine final and tool fields. '
                    "Call only a listed tool; do not add explanations."
                ),
            }
        ]
        for message in request.messages:
            if not isinstance(message, Mapping):
                raise BackendError("invalid_schema", "Agent messages must be objects")
            role = message.get("role")
            content = message.get("content")
            if not isinstance(role, str) or not isinstance(content, str) or not content.strip():
                raise BackendError("invalid_schema", "Agent messages require role and content")
            messages.append({"role": role, "content": content})
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": messages,
            "tools": [
                {"name": name, "schema": dict(schema)}
                for name, schema in request.tools.items()
            ],
            "options": {"num_predict": request.max_output_tokens},
        }
        value = self._post("/api/chat", payload)
        if not isinstance(value, dict) or not isinstance(value.get("message"), dict):
            raise self._invalid()
        content = value["message"].get("content")
        if not isinstance(content, str):
            raise self._invalid()
        return decode_agent_turn_response(content, tuple(request.tools))

    def translate_batch(self, requests, envelope) -> tuple[ContextualResult, ...]:
        """Send source and bounded memory as separate JSON fields."""
        require_contextual_capability(self)
        if not requests:
            return ()
        source = {
            "language": envelope.source_language,
            "segments": [
                {
                    "id": request.segment_id,
                    "text": request.text,
                    "markup": request.markup,
                    "attributes": dict(request.attributes),
                }
                for request in requests
            ],
        }
        context = envelope.to_mapping()["context"]
        strategy = prompt_strategy_for_model(self.model)
        instructions = envelope.instructions.strip()
        if not instructions and strategy is not None:
            instructions = strategy.build(
                envelope.source_language, envelope.target_language, "", structured=True
            ).strip()
        if not instructions:
            instructions = "Translate the source segments and return only the requested JSON structure."
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "source": source,
                            "target_language": envelope.target_language,
                            "context": context,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        value = self._post("/api/chat", payload)
        if not isinstance(value, dict) or not isinstance(value.get("message"), dict):
            raise self._invalid()
        content = value["message"].get("content")
        if not isinstance(content, str):
            raise self._invalid()
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError as exc:
            raise self._invalid() from exc
        return decode_contextual_results(decoded, requests)
    def _call_precomposed(self, prompt: Prompt) -> str:
        value = self._post(
            "/api/chat",
            {"model": self.model, "stream": False,
             "messages": [{"role": "user", "content": translate_prompt(prompt)}]},
        )
        if not isinstance(value, dict) or not isinstance(value.get("message"), dict):
            raise self._invalid()
        return self._string(value["message"].get("content"), "message.content")

    @staticmethod
    def _invalid():
        from .contracts import BackendError
        return BackendError("invalid_response", "Ollama response has no message.content")
