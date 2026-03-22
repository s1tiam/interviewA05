"""
#2 语音转文本（初步）：使用 OpenAI Whisper 本地推理。

说明：
- **reader.py / pyttsx3 是 TTS（朗读），不能做 ASR**，与本模块无关。
- 安装： pip install openai-whisper
  （首次运行会下载模型，体积较大；建议 GPU，CPU 亦可较慢）
- Windows 上若未安装 **ffmpeg**，Whisper 默认 ``load_audio`` 会报 WinError 2。
  本模块对 **.wav / .flac / .ogg** 会优先用 **soundfile** 读入并重采样到 16kHz，无需 ffmpeg。
  其它格式仍依赖 ffmpeg，请安装并加入 PATH：https://ffmpeg.org/

测试：
  python structure/stt_whisper.py path/to/audio.wav
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np


def _load_waveform_16k_mono(path: Path) -> np.ndarray | None:
    """
    用 soundfile 读 wav/flac/ogg，转单声道 float32，重采样到 16kHz。
    失败则返回 None，交由 whisper.load_audio（ffmpeg）处理。
    """
    try:
        import soundfile as sf
    except ImportError:
        return None
    try:
        data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    except Exception:
        return None
    if data.size == 0:
        return np.zeros(1600, dtype=np.float32)
    if data.ndim > 1:
        data = data.mean(axis=1)
    data = np.asarray(data, dtype=np.float32)
    if sr == 16000:
        return np.ascontiguousarray(data)
    if sr <= 0:
        return None
    n_out = max(1, int(round(len(data) * 16000 / sr)))
    x_old = np.arange(len(data), dtype=np.float64)
    x_new = np.linspace(0.0, float(len(data) - 1), n_out)
    out = np.interp(x_new, x_old, data).astype(np.float32)
    return np.ascontiguousarray(out)


class WhisperSTT:
    """兼容 Interviewer 期望：提供 transcribe(audio_path) -> str。"""

    def __init__(self, model_size: str = "base", *, language: str | None = "zh") -> None:
        """
        model_size: tiny / base / small / medium / large（越大越准越慢）
        language: 传给 whisper，如 \"zh\"；None 表示自动检测
        """
        self._model_size = model_size
        self._language = language
        self._model: Any = None

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        try:
            import whisper
        except ImportError as exc:
            raise ImportError(
                "语音转文字需要安装 Whisper：pip install openai-whisper"
            ) from exc
        self._model = whisper.load_model(self._model_size)

    def transcribe(self, audio_path: str) -> str:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(f"音频不存在: {audio_path}")

        self._ensure_model()
        try:
            import torch
        except ImportError as exc:
            raise ImportError("Whisper 依赖 PyTorch，请安装 torch") from exc

        fp16 = bool(torch.cuda.is_available())
        kwargs: dict[str, Any] = {"fp16": fp16}
        if self._language:
            kwargs["language"] = self._language

        suffix = path.suffix.lower()
        audio_input: str | np.ndarray
        if suffix in {".wav", ".flac", ".ogg"}:
            arr = _load_waveform_16k_mono(path)
            if arr is not None:
                audio_input = arr
            else:
                audio_input = str(path)
        else:
            audio_input = str(path)

        try:
            result = self._model.transcribe(audio_input, **kwargs)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Whisper 需要解码音频：当前格式可能依赖系统里的 ffmpeg（需安装并加入 PATH）。"
                "录音请使用 .wav（如 audio_recorder 默认），或安装 ffmpeg。"
            ) from exc

        text = (result.get("text") or "").strip()
        return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Whisper 语音转文字测试")
    parser.add_argument("audio", nargs="?", help="wav/mp3 等音频路径")
    parser.add_argument(
        "--model",
        "-m",
        default="base",
        help="Whisper 模型名：tiny/base/small/medium/large",
    )
    parser.add_argument(
        "--lang",
        "-l",
        default="zh",
        help="语言代码，如 zh；传 auto 表示不指定",
    )
    args = parser.parse_args()
    if not args.audio:
        parser.error("请提供音频文件路径，例如：python structure/stt_whisper.py data/records/xxx.wav")

    lang = None if args.lang.lower() == "auto" else args.lang
    stt = WhisperSTT(model_size=args.model, language=lang)
    text = stt.transcribe(args.audio)
    print(text)


if __name__ == "__main__":
    main()
