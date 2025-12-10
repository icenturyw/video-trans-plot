"""LM Studio API translator (OpenAI-compatible chat completions)."""

from __future__ import annotations

import json
from typing import Callable, List, Optional

import requests

ProgressFn = Optional[Callable[[str], None]]


class LmStudioTranslator:
    def __init__(
        self,
        endpoint: str,
        model: str,
        progress_cb: ProgressFn = None,
        temperature: float = 0.2,
        batch_size: int = 12,
    ) -> None:
        self.endpoint = endpoint
        self.model = model
        self.progress_cb = progress_cb
        self.temperature = temperature
        self.batch_size = batch_size

    def _log(self, text: str) -> None:
        if self.progress_cb:
            self.progress_cb(text)

    def translate_segments(
        self,
        segments: List[dict],
        source_lang: str,
        target_lang: str,
        domain: str = "",
    ) -> List[dict]:
        out: List[dict] = []
        for i in range(0, len(segments), self.batch_size):
            batch = segments[i : i + self.batch_size]
            translated = self._translate_batch(batch, source_lang, target_lang, domain)
            out.extend(translated)
        return out

    def _translate_batch(
        self,
        batch: List[dict],
        source_lang: str,
        target_lang: str,
        domain: str,
    ) -> List[dict]:
        instructions = (
            f"You are a professional translator for {domain or 'general'} domain content. "
            f"Translate from {source_lang} to {target_lang}. "
            "Keep meaning precise and concise; no explanations; output only translated lines."
        )
        numbered = [f"{idx+1}|{seg['text']}" for idx, seg in enumerate(batch)]
        user_prompt = (
            "Translate each line after the pipe and return the translations in the same order, "
            "one per line as 'index|translated'.\n"
            + "\n".join(numbered)
        )
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": user_prompt},
            ],
        }
        self._log(f"LM Studio 翻译 {len(batch)} 条...")
        resp = requests.post(self.endpoint, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        translated: List[str] = []
        for line in lines:
            if "|" in line:
                translated.append(line.split("|", 1)[1].strip())
            else:
                translated.append(line.strip())

        # Fallback if the model returned fewer lines
        while len(translated) < len(batch):
            translated.append("")

        merged: List[dict] = []
        for seg, new_text in zip(batch, translated):
            merged.append(
                {"start": seg["start"], "end": seg["end"], "text": new_text.strip()}
            )
        return merged
