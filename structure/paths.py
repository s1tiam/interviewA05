"""
项目数据目录：录音、报告等统一放在仓库根目录的 data/ 下，避免散落在根路径。

导入本模块时会尝试加载项目根目录下的 .env（需 python-dotenv）。
"""
from __future__ import annotations

from pathlib import Path

# structure/ -> 项目根
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


def load_project_dotenv() -> None:
    """加载 ``<项目根>/.env`` 到环境变量（无 dotenv 或未安装则静默跳过）。"""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(PROJECT_ROOT / ".env")


load_project_dotenv()
DATA_DIR: Path = PROJECT_ROOT / "data"
RECORDS_DIR: Path = DATA_DIR / "records"
REPORTS_DIR: Path = DATA_DIR / "reports"
# 面试综合报告（LLM 生成）默认目录
USER_REPORT_DIR: Path = DATA_DIR / "userreport"


def ensure_data_dirs() -> None:
    """确保 data 子目录存在。"""
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    USER_REPORT_DIR.mkdir(parents=True, exist_ok=True)


# 供默认参数使用的字符串（与当前工作目录无关）
DEFAULT_RECORDS_DIR: str = str(RECORDS_DIR)
DEFAULT_FINAL_REPORT_PATH: str = str(USER_REPORT_DIR / "final_report.md")
