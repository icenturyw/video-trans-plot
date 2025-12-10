from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PySide6 import QtCore, QtGui, QtWidgets

from src import config
from src.ui.worker import JobOptions, PipelineWorker


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Video Translator Pilot")
        self.setMinimumSize(1080, 720)
        self._thread: QtCore.QThread | None = None
        self._worker: PipelineWorker | None = None

        self._build_ui()
        self._apply_style()
        self._sync_backend_fields()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(self._build_file_section())
        layout.addWidget(self._build_options_section())

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%  已完成")
        layout.addWidget(self.progress_bar)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("进度信息会显示在这里...")
        self.log_view.setFixedHeight(180)
        layout.addWidget(self.log_view)

        self.start_btn = QtWidgets.QPushButton("开始处理")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setFixedHeight(46)
        layout.addWidget(self.start_btn)

    def _build_file_section(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("批量文件")
        h = QtWidgets.QHBoxLayout(box)
        h.setSpacing(10)

        self.file_list = QtWidgets.QListWidget()
        self.file_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        h.addWidget(self.file_list, stretch=3)

        btn_layout = QtWidgets.QVBoxLayout()
        add_btn = QtWidgets.QPushButton("添加视频")
        add_btn.clicked.connect(self._add_files)
        rem_btn = QtWidgets.QPushButton("移除选中")
        rem_btn.clicked.connect(self._remove_selected)
        clear_btn = QtWidgets.QPushButton("清空列表")
        clear_btn.clicked.connect(self.file_list.clear)

        for btn in (add_btn, rem_btn, clear_btn):
            btn.setFixedHeight(36)
            btn_layout.addWidget(btn)
        btn_layout.addStretch(1)
        h.addLayout(btn_layout, stretch=1)
        return box

    def _build_options_section(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("参数")
        grid = QtWidgets.QGridLayout(box)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(3, 3)

        grid.addWidget(QtWidgets.QLabel("输出目录"), 0, 0)
        self.output_edit = QtWidgets.QLineEdit(os.path.join(str(Path.home()), "VideoTransOutputs"))
        browse_btn = QtWidgets.QPushButton("选择")
        browse_btn.clicked.connect(self._choose_output_dir)
        grid.addWidget(self.output_edit, 0, 1, 1, 2)
        grid.addWidget(browse_btn, 0, 3)

        grid.addWidget(QtWidgets.QLabel("目标语言"), 1, 0)
        self.target_combo = QtWidgets.QComboBox()
        for lang in config.LANG_OPTIONS:
            self.target_combo.addItem(lang["label"], lang["code"])
        grid.addWidget(self.target_combo, 1, 1)

        grid.addWidget(QtWidgets.QLabel("源语言"), 1, 2)
        self.source_combo = QtWidgets.QComboBox()
        self.source_combo.addItem("自动检测", "")
        for lang in config.LANG_OPTIONS:
            self.source_combo.addItem(lang["label"], lang["code"])
        grid.addWidget(self.source_combo, 1, 3)

        grid.addWidget(QtWidgets.QLabel("Whisper 模型"), 2, 0)
        self.model_combo = QtWidgets.QComboBox()
        for name in ["tiny", "base", "small", "medium", "large", "large-v3"]:
            self.model_combo.addItem(name, name)
        self.model_combo.setCurrentText(config.DEFAULT_WHISPER_MODEL)
        grid.addWidget(self.model_combo, 2, 1)

        grid.addWidget(QtWidgets.QLabel("翻译引擎"), 2, 2)
        self.backend_combo = QtWidgets.QComboBox()
        self.backend_combo.addItem("离线 M2M100", "m2m")
        self.backend_combo.addItem("LM Studio API", "lmstudio")
        self.backend_combo.currentIndexChanged.connect(self._sync_backend_fields)
        grid.addWidget(self.backend_combo, 2, 3)

        grid.addWidget(QtWidgets.QLabel("翻译模型"), 3, 0)
        self.translation_edit = QtWidgets.QLineEdit(config.DEFAULT_TRANSLATION_MODEL)
        grid.addWidget(self.translation_edit, 3, 1, 1, 3)

        grid.addWidget(QtWidgets.QLabel("LM Studio Endpoint"), 4, 0)
        self.lm_endpoint_edit = QtWidgets.QLineEdit(config.DEFAULT_LMSTUDIO_ENDPOINT)
        grid.addWidget(self.lm_endpoint_edit, 4, 1, 1, 3)

        grid.addWidget(QtWidgets.QLabel("LM 模型"), 4, 0)
        self.lm_model_edit = QtWidgets.QLineEdit(config.DEFAULT_LMSTUDIO_MODEL)
        grid.addWidget(self.lm_model_edit, 5, 1)

        grid.addWidget(QtWidgets.QLabel("行业/领域"), 4, 2)
        self.domain_edit = QtWidgets.QLineEdit()
        self.domain_edit.setPlaceholderText("例如：金融、医疗、法律")
        grid.addWidget(self.domain_edit, 5, 3)

        grid.addWidget(QtWidgets.QLabel("字幕字体"), 5, 0)
        self.font_edit = QtWidgets.QLineEdit(config.DEFAULT_FONT)
        grid.addWidget(self.font_edit, 6, 1)

        grid.addWidget(QtWidgets.QLabel("字号"), 5, 2)
        self.font_size = QtWidgets.QSpinBox()
        self.font_size.setRange(12, 64)
        self.font_size.setValue(config.DEFAULT_FONT_SIZE)
        grid.addWidget(self.font_size, 6, 3)

        self.export_srt_cb = QtWidgets.QCheckBox("导出字幕文件")
        self.export_srt_cb.setChecked(True)
        self.keep_source_srt_cb = QtWidgets.QCheckBox("同时保存原文字幕")
        self.keep_source_srt_cb.setChecked(True)
        self.burn_cb = QtWidgets.QCheckBox("烧录字幕到视频")
        self.burn_cb.setChecked(True)

        grid.addWidget(self.export_srt_cb, 7, 0)
        grid.addWidget(self.keep_source_srt_cb, 7, 1)
        grid.addWidget(self.burn_cb, 7, 2)

        return box

    def _apply_style(self) -> None:
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#0f172a"))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#111827"))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#e5e7eb"))
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#1f2937"))
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#e5e7eb"))
        self.setPalette(palette)
        self.setStyleSheet(
            """
            QWidget { color: #e5e7eb; font-family: 'Segoe UI', 'Microsoft YaHei'; }
            QGroupBox { border: 1px solid #1f2937; border-radius: 8px; margin-top: 12px; padding: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #93c5fd; }
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #2563eb, stop:1 #1d4ed8); color: #fff;
                          border: none; border-radius: 6px; padding: 8px 12px; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1d4ed8, stop:1 #1e40af); }
            QPushButton:disabled { background: #334155; color: #9ca3af; }
            QListWidget, QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {
                background-color: #111827; border: 1px solid #1f2937; border-radius: 6px;
                padding: 6px; selection-background-color: #2563eb;
            }
            QProgressBar { border: 1px solid #1f2937; border-radius: 6px; text-align: center; }
            QProgressBar::chunk { background-color: #22c55e; border-radius: 6px; }
        """
        )

    def _add_files(self) -> None:
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "选择视频文件", "", "Video Files (*.mp4 *.mkv *.mov *.avi *.flv *.webm)"
        )
        for f in files:
            if not self._contains_file(f):
                self.file_list.addItem(f)

    def _remove_selected(self) -> None:
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def _contains_file(self, path: str) -> bool:
        for i in range(self.file_list.count()):
            if self.file_list.item(i).text() == path:
                return True
        return False

    def _choose_output_dir(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_edit.text())
        if directory:
            self.output_edit.setText(directory)

    def start_processing(self) -> None:
        files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        if not files:
            self._append_log("请先添加需要处理的视频文件。")
            return
        output_dir = self.output_edit.text().strip()
        if not output_dir:
            self._append_log("请设置输出目录。")
            return

        opts = JobOptions(
            target_lang=self.target_combo.currentData(),
            source_lang=self.source_combo.currentData() or None,
            model_size=self.model_combo.currentData(),
            output_dir=Path(output_dir),
            burn_subtitles=self.burn_cb.isChecked(),
            export_srt=self.export_srt_cb.isChecked(),
            keep_source_srt=self.keep_source_srt_cb.isChecked(),
            font=self.font_edit.text().strip() or config.DEFAULT_FONT,
            font_size=self.font_size.value(),
            translation_model=self.translation_edit.text().strip() or config.DEFAULT_TRANSLATION_MODEL,
            translation_backend=self.backend_combo.currentData(),
            lm_endpoint=self.lm_endpoint_edit.text().strip() or config.DEFAULT_LMSTUDIO_ENDPOINT,
            lm_model=self.lm_model_edit.text().strip() or config.DEFAULT_LMSTUDIO_MODEL,
            domain=self.domain_edit.text().strip(),
        )

        self.start_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self._append_log("开始任务...")

        self._thread = QtCore.QThread()
        self._worker = PipelineWorker(files, opts)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._append_log)
        self._worker.file_progress.connect(self._on_file_progress)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)

        self._thread.start()

    def _on_file_progress(self, file_path: str, percent: int) -> None:
        self.progress_bar.setValue(percent)

    def _on_error(self, message: str) -> None:
        self._append_log(f"错误：\n{message}")

    def _on_finished(self) -> None:
        self._append_log("全部处理完成")
        self.start_btn.setEnabled(True)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        self._worker = None

    def _append_log(self, text: str) -> None:
        self.log_view.appendPlainText(text)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def _sync_backend_fields(self) -> None:
        use_lm = self.backend_combo.currentData() == "lmstudio"
        self.translation_edit.setEnabled(not use_lm)
        self.lm_endpoint_edit.setEnabled(use_lm)
        self.lm_model_edit.setEnabled(use_lm)
        self.domain_edit.setEnabled(True)
