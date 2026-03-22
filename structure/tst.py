# -*- coding: utf-8 -*-
"""
运行：在项目根目录执行 ``python -m structure.tst`` 或 ``python structure/tst.py``。

流程：麦克风录音 → 保存到 ``data/records`` → 使用 ``RecordToText.run_funasr`` 转写。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from structure.audio_recorder import record_until_silence
from structure.paths import DEFAULT_RECORDS_DIR, ensure_data_dirs
from structure.Semantic.RecordToText import run_funasr


def main() -> None:
    parser = argparse.ArgumentParser(description="录音并 FunASR 转写（RecordToText）")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_RECORDS_DIR,
        help="录音文件输出目录，默认 data/records",
    )
    parser.add_argument("--prefix", default="tst", help="文件名前缀")
    parser.add_argument("--max-seconds", type=float, default=60.0, help="最长录音秒数")
    parser.add_argument(
        "--no-require-voice",
        action="store_true",
        help="不要求先检测到有人声即可因静音停止",
    )
    args = parser.parse_args()

    ensure_data_dirs()
    print("开始录音：请说话，随后保持静音触发自动停止...")
    wav_path = record_until_silence(
        output_dir=args.output_dir,
        filename_prefix=args.prefix,
        sample_rate=16000,
        channels=1,
        max_record_seconds=args.max_seconds,
        require_voice_before_stop=not args.no_require_voice,
    )
    print(f"录音已保存: {wav_path}")

    text = run_funasr(str(wav_path))
    print("转写结果:")
    print(text if text else "（无识别文本，请检查 FunASR 依赖与麦克风内容）")


if __name__ == "__main__":
    main()
