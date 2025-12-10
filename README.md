# Video-Trans-Pilot

本地 Whisper + FFmpeg 的批量视频翻译器（PySide6 GUI）。

## 功能
- 批量选择视频，自动转写 → 翻译 → 导出字幕 → 烧录字幕。
- 导出翻译字幕，支持可选保留原文字幕。
- Whisper 模型、目标/源语言、字幕字体/字号可选。
- 翻译默认使用 `facebook/m2m100_418M`（离线），也可切换 LM Studio API 并指定行业领域增强术语准确性。

## 开源说明
- 该项目可直接开源到 GitHub，欢迎 issue/PR。
- 建议仓库包含本 README、`requirements.txt`、`src/` 代码，并添加合适的开源许可证（如 MIT）。
- 如需示例截图，可在 UI 运行后自行截取放入仓库的 `docs/` 或 `assets/`。

## 环境
- Python 3.13（已在 `D:\code\translator\venv` 里测试）
- FFmpeg 已在系统 PATH。
- GPU 可用时自动走 CUDA。

## 安装
```powershell
# 可选：进入项目目录
cd D:\code\Video-Trans-Pilot

# 激活已有虚拟环境
D:\code\translator\venv\Scripts\activate

# 安装依赖（包含 CUDA 版 torch）
pip install -r requirements.txt
```

首次运行会自动下载 Whisper 和翻译模型，取决于网络，需耐心等待。

## 运行
```powershell
python -m src.app
```

## 使用步骤
1. 点击 “添加视频” 选择一个或多个视频文件。
2. 设置输出目录、目标语言/源语言（默认自动检测）、Whisper 模型大小、字体/字号。
3. 选择翻译引擎：
   - 离线 M2M100：无需网络，模型较大。
   - LM Studio API：确保本地 LM Studio 开启 OpenAI 兼容端口（默认 `http://127.0.0.1:1234/v1/chat/completions`），填写模型名称和行业/领域（如“金融”）以优化术语。
4. 勾选是否导出字幕文件、保留原文字幕、是否烧录到视频。
5. 点击 “开始处理”，底部日志与进度条会显示实时状态。

## 产物
- `输出目录/视频名_target.srt`：翻译字幕。
- `输出目录/视频名_source.srt`：原文字幕（如果勾选保留）。
- `输出目录/视频名_target_sub.mp4`：内嵌翻译字幕的视频（如果勾选烧录）。

## 注意
- 翻译模型与 Whisper 模型较大，首次下载/加载需要时间和显存，请预留空间。
- 若要更换翻译模型，可在界面输入其他 Seq2Seq 模型名（需支持多语言，如 m2m100/nllb）；使用 LM Studio 时请确保模型已在本地加载。
