"""Whisper transcription helper."""

from __future__ import annotations

import os
from typing import Callable, Dict, List, Optional

import torch
import whisper


ProgressFn = Optional[Callable[[str], None]]


def _log(message: str, cb: ProgressFn) -> None:
    if cb:
        cb(message)


def transcribe_video(
    video_path: str,
    model_size: str = "medium",
    language: Optional[str] = None,
    device: Optional[str] = None,
    progress_cb: ProgressFn = None,
) -> Dict[str, object]:
    """
    Run Whisper on a single video and return detected language plus segments.

    Returns:
        {"language": "en", "segments": [{"start": 0.0, "end": 1.2, "text": "..."}]}
    """
    resolved = os.path.abspath(video_path)
    _log(f"加载 Whisper 模型 ({model_size})...", progress_cb)
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = whisper.load_model(model_size, device=device)

    _log("开始语音识别...", progress_cb)
    result = model.transcribe(resolved, language=language, verbose=False)
    segments = [
        {
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "text": str(seg["text"]).strip(),
        }
        for seg in result.get("segments", [])
    ]

    _log("识别完成", progress_cb)
    return {"language": result.get("language", language), "segments": segments}
