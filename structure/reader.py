"""
Windows 文本朗读：使用系统 SAPI（通过 pyttsx3），无需 CosyVoice / 无网密钥。

安装： pip install pyttsx3

中文效果依赖 Windows「设置 → 时间和语言 → 语音」中是否已添加中文语音包。

测试（在项目根目录 interviewA05 下）：
      python structure/reader.py
      python structure/reader.py --text "你好，测试朗读。" --rate 180
"""
from __future__ import annotations

import argparse


def read_aloud(
    text: str,
    *,
    rate: int | None = None,
    volume: float = 0.95,
) -> None:
    """将文本朗读出来（阻塞直到读完）。"""
    t = (text or "").strip()
    if not t:
        return

    try:
        import pyttsx3
    except ImportError as exc:
        raise ImportError("请先安装: pip install pyttsx3") from exc

    engine = pyttsx3.init()
    try:
        if rate is not None:
            engine.setProperty("rate", rate)
        engine.setProperty("volume", max(0.0, min(1.0, volume)))

        # 若系统装有中文语音，尽量选用（不同机器 id 不同，仅作启发式）
        try:
            voices = engine.getProperty("voices")
            if voices:
                for v in voices:
                    name = (getattr(v, "name", "") or "").lower()
                    if "chinese" in name or "zh" in name or "hui" in name or "kang" in name:
                        engine.setProperty("voice", v.id)
                        break
        except Exception:
            pass

        engine.say(t)
        engine.runAndWait()
    finally:
        try:
            engine.stop()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Windows TTS 测试（pyttsx3）")
    parser.add_argument(
        "--text",
        "-t",
        default="你好，这是文本朗读测试。",
        help="要朗读的文本",
    )
    parser.add_argument(
        "--rate",
        "-r",
        type=int,
        default=None,
        help="语速（可选，数值越大越快，常见约 150–220）",
    )
    parser.add_argument(
        "--volume",
        "-v",
        type=float,
        default=0.95,
        help="音量 0.0～1.0，默认 0.95",
    )
    args = parser.parse_args()
    print("正在朗读…", repr(args.text[:60] + ("…" if len(args.text) > 60 else "")))
    read_aloud(args.text, rate=args.rate, volume=args.volume)
    print("朗读结束。")


if __name__ == "__main__":
    main()
