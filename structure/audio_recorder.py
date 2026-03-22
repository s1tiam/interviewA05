from __future__ import annotations

import argparse
import math
import queue
import tempfile
import time
from pathlib import Path
from typing import Literal

import numpy as np

from .paths import DEFAULT_RECORDS_DIR, ensure_data_dirs

try:
    import sounddevice as sd
except ImportError as exc:  # pragma: no cover
    raise ImportError("缺少依赖 sounddevice，请先执行: pip install sounddevice") from exc

try:
    import soundfile as sf
except ImportError as exc:  # pragma: no cover
    raise ImportError("缺少依赖 soundfile，请先执行: pip install soundfile") from exc


AudioFormat = Literal["wav", "mp3"]


def _rms_db(chunk: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.square(chunk), dtype=np.float64)))
    if rms <= 1e-8:
        return -100.0
    return 20.0 * math.log10(rms)


def _export_mp3_from_wav(wav_path: Path, mp3_path: Path) -> None:
    try:
        from pydub import AudioSegment
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "导出 mp3 需要 pydub 和 ffmpeg。"
            "请安装: pip install pydub，并确保系统可用 ffmpeg。"
        ) from exc

    audio = AudioSegment.from_wav(str(wav_path))
    audio.export(str(mp3_path), format="mp3")


def is_round_finished(
    *,
    answer_duration_seconds: float,
    silence_tail_seconds: float,
    min_round_seconds: float,
    silence_threshold_seconds: float,
) -> bool:
    """
    轮次结束判定：
    1) 回答总时长达到最小要求
    2) 结尾静音超过阈值
    """
    enough_duration = answer_duration_seconds >= min_round_seconds
    enough_silence = silence_tail_seconds >= silence_threshold_seconds
    return enough_duration and enough_silence


def record_until_silence(
    *,
    output_dir: str | Path = ".",
    filename_prefix: str = "recording",
    sample_rate: int = 16000,
    channels: int = 1,
    silence_threshold_db: float = -40.0,
    silence_duration_seconds: float = 1.0,
    min_record_seconds: float = 0.5,
    max_record_seconds: float = 300.0,
    chunk_seconds: float = 0.1,
    output_format: AudioFormat = "wav",
    require_voice_before_stop: bool = True,
) -> Path:
    """
    录制麦克风音频，检测到连续静音达到阈值后自动停止并输出音频文件。
    """
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    frame_size = max(1, int(sample_rate * chunk_seconds))
    chunks: list[np.ndarray] = []
    audio_queue: queue.Queue[np.ndarray] = queue.Queue()
    silent_for = 0.0
    heard_voice = False
    start = time.time()

    def callback(indata: np.ndarray, frames: int, _time, status) -> None:
        if status:
            # 不中断流程，仅保留最后一次状态信息用于定位环境问题。
            pass
        audio_queue.put(indata.copy())

    with sd.InputStream(
        samplerate=sample_rate,
        channels=channels,
        dtype="float32",
        blocksize=frame_size,
        callback=callback,
    ):
        while True:
            elapsed = time.time() - start
            if elapsed >= max_record_seconds:
                break

            try:
                chunk = audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            chunks.append(chunk)
            chunk_duration = len(chunk) / float(sample_rate)
            db = _rms_db(chunk)

            if db < silence_threshold_db:
                silent_for += chunk_duration
            else:
                heard_voice = True
                silent_for = 0.0

            can_stop = elapsed >= min_record_seconds and silent_for >= silence_duration_seconds
            if require_voice_before_stop:
                can_stop = can_stop and heard_voice
            if can_stop:
                break

    if not chunks:
        raise RuntimeError("未采集到任何音频数据，请检查麦克风或权限。")

    audio = np.concatenate(chunks, axis=0)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    wav_path = output_root / f"{filename_prefix}_{timestamp}.wav"
    sf.write(str(wav_path), audio, sample_rate)

    if output_format == "wav":
        return wav_path

    if output_format == "mp3":
        mp3_path = output_root / f"{filename_prefix}_{timestamp}.mp3"
        with tempfile.TemporaryDirectory() as _tmp:
            _export_mp3_from_wav(wav_path, mp3_path)
        wav_path.unlink(missing_ok=True)
        return mp3_path

    raise ValueError(f"不支持的输出格式: {output_format}")


def main() -> None:
    parser = argparse.ArgumentParser(description="本地录音测试：连续静音达到阈值后自动停止。")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_RECORDS_DIR,
        help=f"输出目录，默认项目下 data/records（当前: {DEFAULT_RECORDS_DIR}）",
    )
    parser.add_argument("--prefix", default="test_recording", help="文件名前缀")
    parser.add_argument("--sample-rate", type=int, default=16000, help="采样率，默认 16000")
    parser.add_argument("--channels", type=int, default=1, help="声道数，默认 1")
    parser.add_argument("--silence-threshold-db", type=float, default=-40.0, help="静音阈值(dB)")
    parser.add_argument("--silence-seconds", type=float, default=1.0, help="静音持续秒数")
    parser.add_argument("--min-seconds", type=float, default=0.5, help="最短录音秒数")
    parser.add_argument("--max-seconds", type=float, default=60.0, help="最长录音秒数")
    parser.add_argument("--chunk-seconds", type=float, default=0.1, help="分块时长秒数")
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["wav", "mp3"],
        default="wav",
        help="输出格式: wav 或 mp3",
    )
    parser.add_argument(
        "--no-require-voice",
        action="store_true",
        help="不要求先检测到有人声即可触发静音停止",
    )
    args = parser.parse_args()
    ensure_data_dirs()

    print("开始录音：请说话，随后保持静音触发自动停止...")
    audio_path = record_until_silence(
        output_dir=args.output_dir,
        filename_prefix=args.prefix,
        sample_rate=args.sample_rate,
        channels=args.channels,
        silence_threshold_db=args.silence_threshold_db,
        silence_duration_seconds=args.silence_seconds,
        min_record_seconds=args.min_seconds,
        max_record_seconds=args.max_seconds,
        chunk_seconds=args.chunk_seconds,
        output_format=args.output_format,
        require_voice_before_stop=not args.no_require_voice,
    )
    print(f"录音完成，文件已保存：{audio_path}")


if __name__ == "__main__":
    main()
