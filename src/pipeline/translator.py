"""Text translation using Hugging Face M2M100 (offline-friendly)."""

from __future__ import annotations

from typing import Callable, Iterable, List, Optional

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ProgressFn = Optional[Callable[[str], None]]


class Translator:
    def __init__(
        self,
        model_name: str = "facebook/m2m100_418M",
        device: Optional[str] = None,
        progress_cb: ProgressFn = None,
    ) -> None:
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.progress_cb = progress_cb
        self._tokenizer: Optional[AutoTokenizer] = None
        self._model: Optional[AutoModelForSeq2SeqLM] = None

    def _log(self, text: str) -> None:
        if self.progress_cb:
            self.progress_cb(text)

    def _ensure_model(self) -> None:
        if self._tokenizer is None or self._model is None:
            self._log(f"加载翻译模型 {self.model_name} ({self.device})...")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self._model.to(self.device)

    def translate_texts(
        self,
        texts: Iterable[str],
        source_lang: str,
        target_lang: str,
        max_batch: int = 6,
    ) -> List[str]:
        self._ensure_model()
        assert self._tokenizer and self._model
        self._tokenizer.src_lang = source_lang
        device = torch.device(self.device)

        outputs: List[str] = []
        batch: List[str] = []

        def flush_batch() -> None:
            nonlocal outputs, batch
            if not batch:
                return
            inputs = self._tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(device)
            generated_tokens = self._model.generate(
                **inputs,
                forced_bos_token_id=self._tokenizer.get_lang_id(target_lang),
                max_length=512,
            )
            outputs.extend(self._tokenizer.batch_decode(generated_tokens, skip_special_tokens=True))
            batch = []

        for text in texts:
            batch.append(text)
            if len(batch) >= max_batch:
                flush_batch()
        flush_batch()
        return outputs

    def translate_segments(
        self,
        segments: List[dict],
        source_lang: str,
        target_lang: str,
    ) -> List[dict]:
        texts = [seg["text"] for seg in segments]
        translated = self.translate_texts(texts, source_lang, target_lang)
        merged: List[dict] = []
        for seg, new_text in zip(segments, translated):
            merged.append(
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": new_text.strip(),
                }
            )
        return merged
