"""Application configuration and shared constants."""

from __future__ import annotations

from typing import Dict, List

# Friendly language list for UI and translation backends (M2M100 codes).
LANG_OPTIONS: List[Dict[str, str]] = [
    {"label": "简体中文", "code": "zh"},
    {"label": "英语", "code": "en"},
    {"label": "日语", "code": "ja"},
    {"label": "韩语", "code": "ko"},
    {"label": "法语", "code": "fr"},
    {"label": "德语", "code": "de"},
    {"label": "西班牙语", "code": "es"},
    {"label": "俄语", "code": "ru"},
    {"label": "葡萄牙语", "code": "pt"},
    {"label": "意大利语", "code": "it"},
    {"label": "阿拉伯语", "code": "ar"},
]

# Default fonts for subtitle burn-in.
DEFAULT_FONT = "Microsoft YaHei UI"
DEFAULT_FONT_SIZE = 32

# Default Whisper model size.
DEFAULT_WHISPER_MODEL = "medium"

# Hugging Face model for offline translation.
DEFAULT_TRANSLATION_MODEL = "facebook/m2m100_418M"

# LM Studio API defaults (OpenAI-compatible).
DEFAULT_LMSTUDIO_ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_LMSTUDIO_MODEL = "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF"
