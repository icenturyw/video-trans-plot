"""Video utilities built on top of FFmpeg."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Optional

from src.config import DEFAULT_FONT, DEFAULT_FONT_SIZE


def _escape_for_subtitles(path: Path) -> str:
    """
    FFmpeg subtitles filter expects colon-separated args; escape ':' and quotes.
    Windows drive letter colon must be escaped as well.
    """
    return path.as_posix().replace(":", r"\:").replace("'", r"\\'")


def burn_subtitles(
    video_path: str,
    srt_path: str,
    output_path: str,
    font: str = DEFAULT_FONT,
    font_size: int = DEFAULT_FONT_SIZE,
    progress_cb: Optional[callable] = None,
) -> str:
    """
    Burn an SRT file into a video using FFmpeg.
    """
    def _log(msg: str) -> None:
        if progress_cb:
            progress_cb(msg)

    input_path = Path(video_path).resolve()
    subtitle_path = Path(srt_path).resolve()
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    subtitle_arg = _escape_for_subtitles(subtitle_path)
    style = (
        f"Fontname={font},Fontsize={font_size},PrimaryColour=&H00FFFFFF&,"
        f"Outline=1,BorderStyle=3,BackColour=&H50000000&"
    )
    vf = f"subtitles='{subtitle_arg}':charenc=UTF-8:force_style='{style}'"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        vf,
        "-c:a",
        "copy",
        str(output),
    ]

    _log("调用 FFmpeg 进行压制...")
    subprocess.run(cmd, check=True)
    _log("压制完成")
    return str(output)
