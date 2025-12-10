"""Subtitle helpers: build and save SRT files from segments."""

from __future__ import annotations

import os
from datetime import timedelta
from typing import List

import srt


def segments_to_srt_text(segments: List[dict]) -> str:
    subtitles = [
        srt.Subtitle(
            index=i + 1,
            start=timedelta(seconds=seg["start"]),
            end=timedelta(seconds=seg["end"]),
            content=seg["text"],
        )
        for i, seg in enumerate(segments)
    ]
    return srt.compose(subtitles)


def save_srt(segments: List[dict], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    srt_text = segments_to_srt_text(segments)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(srt_text)
    return output_path
