"""Background worker to run transcription + translation without blocking the UI."""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from PySide6 import QtCore

from src.config import DEFAULT_FONT, DEFAULT_FONT_SIZE, DEFAULT_TRANSLATION_MODEL
from src.pipeline.subtitles import save_srt
from src.pipeline.transcriber import transcribe_video
from src.pipeline.translator import Translator
from src.pipeline.lmstudio import LmStudioTranslator
from src.pipeline.video import burn_subtitles


@dataclass
class JobOptions:
    target_lang: str
    source_lang: Optional[str]
    model_size: str
    output_dir: Path
    burn_subtitles: bool = True
    export_srt: bool = True
    keep_source_srt: bool = True
    font: str = DEFAULT_FONT
    font_size: int = DEFAULT_FONT_SIZE
    translation_model: str = DEFAULT_TRANSLATION_MODEL
    translation_backend: str = "m2m"
    lm_endpoint: str = ""
    lm_model: str = ""
    domain: str = ""


class PipelineWorker(QtCore.QObject):
    progress = QtCore.Signal(str)
    file_progress = QtCore.Signal(str, int)
    finished = QtCore.Signal()
    error = QtCore.Signal(str)

    def __init__(self, files: List[str], options: JobOptions):
        super().__init__()
        self.files = files
        self.options = options
        self._translator: Optional[Translator] = None
        self._lm_translator: Optional[LmStudioTranslator] = None

    @QtCore.Slot()
    def run(self) -> None:
        try:
            if self.options.translation_backend == "m2m":
                self._translator = Translator(
                    model_name=self.options.translation_model,
                    progress_cb=self.progress.emit,
                )
            else:
                self._lm_translator = LmStudioTranslator(
                    endpoint=self.options.lm_endpoint,
                    model=self.options.lm_model,
                    progress_cb=self.progress.emit,
                )
            total = len(self.files)

            for idx, file_path in enumerate(self.files, start=1):
                self._handle_single(file_path)
                percent = int(idx / total * 100)
                self.file_progress.emit(file_path, percent)

        except Exception as exc:  # pragma: no cover - surfaced to UI
            trace = traceback.format_exc()
            self.error.emit(f"{exc}\n{trace}")
        finally:
            self.finished.emit()

    def _handle_single(self, file_path: str) -> None:
        file_path = str(Path(file_path).resolve())
        self.progress.emit(f"开始处理：{Path(file_path).name}")
        transcription = transcribe_video(
            file_path,
            model_size=self.options.model_size,
            language=self.options.source_lang,
            progress_cb=self.progress.emit,
        )

        source_lang = self.options.source_lang or transcription.get("language", "auto")
        target_lang = self.options.target_lang

        segments = transcription["segments"]  # type: ignore[index]
        self.progress.emit(f"翻译到 {target_lang} ...")
        if self.options.translation_backend == "m2m":
            translated_segments = self._translator.translate_segments(  # type: ignore[union-attr]
                segments, source_lang=source_lang, target_lang=target_lang
            )
        else:
            translated_segments = self._lm_translator.translate_segments(  # type: ignore[union-attr]
                segments,
                source_lang=source_lang,
                target_lang=target_lang,
                domain=self.options.domain,
            )

        output_dir = self.options.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(file_path).stem

        translated_srt = output_dir / f"{stem}_{target_lang}.srt"
        save_srt(translated_segments, str(translated_srt))
        keep_translated = self.options.export_srt or not self.options.burn_subtitles
        if keep_translated:
            self.progress.emit(f"已生成翻译字幕：{translated_srt.name}")

        if self.options.keep_source_srt:
            original_srt = output_dir / f"{stem}_source.srt"
            save_srt(segments, str(original_srt))
            self.progress.emit(f"已生成原文字幕：{original_srt.name}")

        if self.options.burn_subtitles:
            output_video = output_dir / f"{stem}_{target_lang}_sub.mp4"
            burn_subtitles(
                file_path,
                str(translated_srt),
                str(output_video),
                font=self.options.font,
                font_size=self.options.font_size,
                progress_cb=self.progress.emit,
            )
            self.progress.emit(f"压制完成：{output_video.name}")
        else:
            self.progress.emit("已跳过压制，仅输出字幕文件")
            keep_translated = True

        if not keep_translated and translated_srt.exists():
            try:
                translated_srt.unlink()
            except OSError:
                pass
