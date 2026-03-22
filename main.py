#!/usr/bin/env python3
"""
Interviewer 全流程测试（项目根目录 interviewA05 下运行）。

默认 **全真**：DeepSeek 等真实 LLM、pyttsx3 朗读、麦克风录音、Whisper 转写（需本机环境与依赖）。

  python main.py
  python main.py --rounds 2

无密钥 / 无麦克风 / CI 时用干跑：

  python main.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 保证从任意工作目录运行都能找到 structure
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 尽早加载项目根 .env（DEEPSEEK_API_KEY 等）
import structure.paths  # noqa: F401

from structure.Interviewer import Interviewer
from structure.paths import DEFAULT_RECORDS_DIR, USER_REPORT_DIR, ensure_data_dirs
from structure.stt_whisper import WhisperSTT


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interviewer 流程测试：默认全真（LLM+朗读+录音+Whisper），--dry-run 为干跑",
    )
    parser.add_argument("--rounds", type=int, default=1, help="执行 new_round 次数，默认 1")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干跑：假 LLM、不朗读、不录麦克风、假 Whisper（无需 API 与硬件）",
    )
    parser.add_argument(
        "--llm-backend",
        default="deepseek",
        help="真实模式下的 registry 后端，默认 deepseek（需 .env 中 DEEPSEEK_API_KEY）",
    )
    parser.add_argument(
        "--report",
        default=str(USER_REPORT_DIR / "test_interviewer_report.md"),
        help="build_final_report 输出路径",
    )
    args = parser.parse_args()
    ensure_data_dirs()

    iv = Interviewer(
            stt_service=WhisperSTT(),
            semantic_evaluator=None,
            emotion_evaluator=None,
            llm=None,
            llm_backend=args.llm_backend,
            target_job="后端开发（测试）",
            rag_top_k=3,
        )
    mode = "真实 LLM + pyttsx3 朗读"

    print("=== Interviewer 测试 ===")
    print(mode)
    print(f"llm_backend={args.llm_backend}  rounds={args.rounds}\n")
    iv.execute_all()

    print("\n完成。")

if __name__ == "__main__":
    main()
