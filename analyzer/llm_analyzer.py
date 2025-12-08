import json
import os
from typing import Any, Dict, Optional

from api.analyzer import AnalyzerManager
from transport.message import Analyzer as MessageAnalyzerKind, NetworkPacketMessage, JournalMessage, Message


class LLMAnalyzer(AnalyzerManager):
    """Analyzer that leverages an LLM to assess whether packets indicate an attack.

    This implementation expects an OpenAI-compatible API to be available when the
    environment variable OPENAI_API_KEY is set and the `openai` package is
    installed. If neither is available, it will raise a RuntimeError instructing
    the user how to enable the LLM integration.
    """

    def __init__(self, model: Optional[str] = None):
        """Create a new LLM-backed analyzer.

        Args:
            model: The LLM model name to use. Defaults to a lightweight model if
                not provided.
        """
        self._model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")

    def analyze(self, message: Message) -> Dict[str, Any]:
        if not isinstance(message, (NetworkPacketMessage, JournalMessage)):
            raise TypeError("LLMAnalyzer requires a NetworkPacketMessage or JournalMessage input")

        # Prepare the prompt tailored by the message for LLM consumption.
        prompt_bytes = message.to_format_of_analyzer(MessageAnalyzerKind.LLM)
        prompt = prompt_bytes.decode("utf-8", errors="replace")

        # Compose a strict JSON response instruction to make parsing robust.
        if isinstance(message, NetworkPacketMessage):
            system_prompt = (
                "You are a network security expert. Analyze the provided packet summaries "
                "and hexdumps. Decide if the capture indicates a likely attack. "
                "Respond STRICTLY as compact JSON with keys: is_attack (boolean) and reasoning (string). "
                "Do not include markdown, code fences, or extra text."
            )
        else:
            system_prompt = (
                "You are a system security expert. Analyze the provided journalctl logs. "
                "Decide if the logs indicate suspicious or malicious activity. "
                "Respond STRICTLY as compact JSON with keys: is_attack (boolean) and reasoning (string). "
                "Do not include markdown, code fences, or extra text."
            )

        # Attempt OpenAI SDK v1 first, fall back to legacy if needed.
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "LLMAnalyzer requires OPENAI_API_KEY to be set in the environment to contact the LLM."
            )

        try:
            # Prefer modern OpenAI SDK (>=1.0)
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=api_key)
            print(f"[1] length of prompt sent to LLM: {len(prompt)}")
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            print(f"[2] length of prompt sent to LLM: {len(prompt)}")
            content = response.choices[0].message.content or "{}"
        except Exception:
            # Try legacy SDK for broader compatibility
            try:
                import openai  # type: ignore

                openai.api_key = api_key
                print(f"[3] length of prompt sent to LLM: {len(prompt)}")
                completion = openai.ChatCompletion.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0,
                )
                print(f"[4] length of prompt sent to LLM: {len(prompt)}")
                content = completion["choices"][0]["message"]["content"] or "{}"
            except Exception as e2:  # pragma: no cover - network/env dependent
                raise RuntimeError(
                    "Failed to call OpenAI API. Install the 'openai' package and ensure your key is valid."
                ) from e2

        # Parse the model output as JSON. If parsing fails, attempt a basic recovery.
        try:
            parsed = json.loads(content)
            is_attack = bool(parsed.get("is_attack"))
            reasoning = str(parsed.get("reasoning", ""))
        except Exception:
            # Non-JSON or malformed response. Provide the raw output for caller to inspect.
            is_attack = False
            reasoning = "Model did not return valid JSON. See raw_output."

        return {
            "analyzer": "LLM",
            "is_attack": is_attack,
            "reasoning": reasoning,
            "raw_output": content,
            "model": self._model,
        }
