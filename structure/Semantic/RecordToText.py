# -*- coding: utf-8 -*-
import sys
import os
import pathlib
from contextlib import contextmanager
from contextlib import redirect_stderr
from contextlib import redirect_stdout

# ============ 1. 首先设置 FFmpeg 路径（必须在导入 funasr 之前） ============
# 获取当前脚本所在目录
script_dir = pathlib.Path(__file__).parent.resolve()

# 在脚本目录下创建 ffmpeg 文件夹
ffmpeg_dir = script_dir / "ffmpeg"
ffmpeg_bin = ffmpeg_dir / "bin"

# 检查 FFmpeg 是否存在，如果不存在则自动下载
if not (ffmpeg_bin / "ffmpeg.exe").exists():
    print(f"FFmpeg 未找到，正在下载到: {ffmpeg_bin}")
    import urllib.request
    import zipfile
    import shutil

    ffmpeg_dir.mkdir(parents=True, exist_ok=True)

    # 下载 FFmpeg
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = ffmpeg_dir / "ffmpeg.zip"

    try:
        urllib.request.urlretrieve(url, zip_path)
        print("下载完成，正在解压...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(ffmpeg_dir)

        # 移动 bin 目录到正确位置
        extracted = list(ffmpeg_dir.glob("ffmpeg-*"))[0]
        if not ffmpeg_bin.exists():
            shutil.move(extracted / "bin", ffmpeg_bin.parent)
            shutil.rmtree(extracted)

        zip_path.unlink()
        print(f"FFmpeg 安装完成: {ffmpeg_bin}")
    except Exception as e:
        print(f"FFmpeg 自动下载失败: {e}")
        print("请手动下载并解压到: {ffmpeg_bin.parent}")

# 将 FFmpeg 路径添加到当前进程的 PATH（必须在导入 funasr 之前）
os.environ['PATH'] = str(ffmpeg_bin) + os.pathsep + os.environ.get('PATH', '')

# ============ 2. 现在再导入其他模块 ============
from funasr import AutoModel

current_file_dir = os.path.dirname(os.path.abspath(__file__))
structure_dir = os.path.dirname(current_file_dir)
project_root = os.path.dirname(structure_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from structure.LLM.registry import get_llm
from dotenv import load_dotenv

load_dotenv()

# 运行示例: python structure/Semantic/RecordToText.py
WSPrompt = (
"""
### 面试问题
{question}

### 候选人回答（文本）
{answer}

### 标准参考答案
{true_qa_ans}

"""
)
systemprompt="""
你是一位专业的AI面试官评估专家。请根据候选人的回答，从以下四个维度进行量化评分（每个维度满分100分），并输出纯字符串结果。
### 评分维度说明

请根据以下四项评分标准对回答进行评分，每一项均分为四档，请严格按照档位对应的评分要求进行评判：

1. 内容性（0-100分）
高（90-100分）：回答内容质量优异，体现学生突出的综合能力。具体表现为：内容中提及高含金量奖项（如国家级竞赛、国际奖项）、国家级项目或活动经历、顶尖院校背景、专业排名前列、显著突出的学习成绩，或具有深度且成果可验证的项目/科研经历。回答始终紧扣问题核心，所有信息均与问题直接相关，未出现任何偏离主题或答非所问的内容。
中（80-89分）：回答内容质量良好，体现学生较强的综合能力。内容中提及省级及以上奖项、校级以上重点项目、较好院校背景、良好学习成绩，或具有较丰富的项目/实践经历。回答总体上围绕问题展开，但存在少量与问题关联不紧密的内容，或个别表述略有偏离，未严重影响整体理解。
低（65-79分）：回答内容质量一般，学生能力表现不够突出。内容中仅提及校级奖项、常规课程项目、普通院校背景、中等成绩，或项目经历较为简单。回答部分内容与问题相关，但存在较多偏离主题或关联性较弱的内容，整体相关性不足。
拉（0-64分）：回答内容质量较差，无法体现学生能力优势。内容中缺乏有效的能力证明材料，或所提及的奖项、项目、背景等含金量低、关联性弱。回答大量内容与问题无关，或明显答非所问，未能回应问题的核心要求。

2. 结构清晰性（0-100分）
高（90-100分）：回答具有明确的逻辑结构（如总分总、时间顺序、要点并列等），层次分明，衔接词使用得当（如首先、其次、最后），信息组织清晰易懂。
中（80-89分）：回答有一定结构，逻辑层次基本清晰，衔接词使用较为自然，整体条理性较好。
低（65-79分）：回答结构不够清晰，逻辑层次存在混乱，衔接词使用不足或不自然，整体条理性一般，理解有一定困难。
拉（0-64分）：回答缺乏逻辑结构，内容杂乱无章，前后跳跃，难以把握信息脉络。

3. 完整性（0-100分）
高（90-100分）：回答全面覆盖问题所涉及的关键要素，无重要信息遗漏。对于提及的项目、奖项或经历，提供了充分的客观验证信息，包括具体时间（如年份、月份）、地点（如学校、城市、赛事举办地）、经过（如参与角色、具体工作内容）、结果（如获奖等级、项目产出、成果应用）等关键要素，信息真实可追溯，无明显说谎或夸大嫌疑。
中（80-89分）：回答覆盖了绝大部分关键要素，仅有个别次要信息缺失或展开稍显不足。对于提及的项目、奖项或经历，提供了大部分客观信息（如时间、结果等），但存在少量信息缺失（如具体地点、经过细节等），整体可信度较高，真实性可基本确认。
低（65-79分）：回答覆盖了部分关键要素，但存在多处重要信息缺失或展开不足。对于提及的项目、奖项或经历，仅提供了笼统描述（如“参加过某个比赛”“做过一个项目”），缺乏具体时间、地点、经过、结果等客观验证信息，存在一定夸大或模糊表述，真实性存疑，需要进行追问核实。
拉（0-64分）：回答明显过于简短，缺失多个关键信息，未能满足问题的基本信息需求。对于提及的项目、奖项或经历，完全缺乏客观验证要素，或存在明显矛盾、不符合常理的表述，高度疑似说谎或虚构，必须进行追问确认。

4. 语言专业性（0-100分）
高（90-100分）：术语使用准确（如“C++”而非“c--”；由于语音识别不完善，“c++”识别为“四加加”时可忽略，这不是面试者错误），表达专业严谨，语法规范，无口语化或随意表达。
中（80-89分）：术语使用基本正确，存在极少量不规范表达或轻微语法问题，整体语言专业性良好。
低（65-79分）：术语使用存在一定错误，或存在少量口语化表达及语法问题，语言专业性一般，对理解有轻微影响。
拉（0-64分）：存在明显术语错误、大量口语化表达或语法问题，语言表达随意、不规范，严重影响内容的专业性和可信度。

### 输出格式（纯文字，不要包含其他符号）
  内容相关性: score1: 整数, reason: 简要说明评分理由
  结构清晰性: score2: 整数, reason: 简要说明评分理由
  完整性: score3: 整数, reason: 简要说明评分理由
  语言专业性: score4: 整数, reason: 简要说明评分理由
  summary: 一句话总结
  建议追问：若有得分低于60的项目或者得分高于85的项目，给出你的一个建议追问问题，问题必须紧扣回答，不要偏离主题。若无，则此处回复“无，下一个问题”
"""

_asr_model_cache = {}


@contextmanager
def _mute_funasr_io():
    """
    屏蔽 FunASR / ModelScope / torchaudio / tqdm 等写入终端的提示、进度条与日志。
    使用独立 devnull，避免 stdout/stderr 指向同一对象导致行为异常。
    """
    with open(os.devnull, "w", encoding="utf-8", errors="replace") as out, open(
        os.devnull, "w", encoding="utf-8", errors="replace"
    ) as err:
        with redirect_stdout(out), redirect_stderr(err):
            yield


def run_funasr(wav_path, model='paraformer-zh'):

    try:
        # 首次 import 时也会打印 ffmpeg/torchaudio 提示，一并静音
        with _mute_funasr_io():
            from funasr import AutoModel
    except ModuleNotFoundError as e:
        name = getattr(e, "name", "") or ""
        msg = str(e).lower()
        if name == "torchaudio" or "torchaudio" in msg:
            raise ImportError(
                "FunASR 依赖 torchaudio：请先安装与 PyTorch 版本匹配的 torch / torchaudio。\n"
                "  CPU 示例：pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu\n"
                "  再执行：pip install funasr\n"
                "  说明：https://pytorch.org/get-started/locally/"
            ) from e
        if name == "funasr" or "funasr" in msg:
            raise ImportError("请先安装 FunASR：pip install funasr") from e
        raise ImportError(f"缺少依赖: {e}。若使用 FunASR，请安装 funasr 及其依赖（含 torchaudio）。") from e
    except ImportError as e:
        raise ImportError("请先安装 funasr 包: pip install funasr") from e

    if model not in _asr_model_cache:
        try:
            with _mute_funasr_io():
                # disable_update：跳过联网检查版本；log_level：降低 logging.basicConfig 输出
                try:
                    _asr_model_cache[model] = AutoModel(
                        model=model,
                        disable_update=True,
                        log_level="CRITICAL",
                    )
                except TypeError:
                    _asr_model_cache[model] = AutoModel(
                        model=model,
                        disable_update=True,
                    )
        except Exception:
            return ""
    asr_model = _asr_model_cache[model]

    try:
        with _mute_funasr_io():
            result = asr_model.generate(input=wav_path)
        text = ''
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get('text', '')
        elif isinstance(result, dict):
            text = result.get('text', '')
        return text
    except Exception:
        return ""

def build_wait_send_text(WSPrompt, question, user_ans, true_qa_ans=None):
    """将 WSPrompt 中的 {question}/{answer}/{true_qa_ans} 占位符替换为实际内容。"""
    tqa = true_qa_ans if true_qa_ans is not None else ""
    return WSPrompt.format(question=question, answer=user_ans, true_qa_ans=tqa)

def RecordtoText(wav_path):
    user_ans = run_funasr(wav_path)
    return user_ans


def SemanticAnalysis(llm,user_ans, question, true_qa_ans=None ):
    wait_send_text = build_wait_send_text(WSPrompt, question, user_ans, true_qa_ans)
    system_prompt = """你是面试评估专家，请严格按照以下格式输出评分结果，必须包含所有四项：

    内容相关性: score1: [0-100的整数]
    结构清晰性: score2: [0-100的整数]
    完整性: score3: [0-100的整数]
    语言专业性: score4: [0-100的整数]
    
    然后为每项提供简要说明，最后给出一句话总结。
    
    权重配置：
    - 内容相关性权重: 0.3
    - 结构清晰性权重: 0.2
    - 完整性权重: 0.25
    - 语言专业性权重: 0.25"""
    system_prompt+=systemprompt
    response = llm.execute(wait_send_text, systemprompt=system_prompt)
    
    # 权重配置（可直接修改）
    weights = {
        'score1': 0.5,   # 内容相关性
        'score2': 0.25,   # 结构清晰性
        'score3': 0.1,  # 完整性
        'score4': 0.15   # 语言专业性
    }
    
    # 解析四项得分
    scores = {'score1': None, 'score2': None, 'score3': None, 'score4': None}
    for line in response.splitlines():
        line = line.strip()
        for key in scores.keys():
            if f"{key}:" in line:
                try:
                    # 提取 score1: 后面的数字
                    idx = line.find(f"{key}:")
                    if idx != -1:
                        # 从 score1: 后面开始查找数字
                        rest = line[idx + len(key) + 1:].strip()
                        # 提取第一个数字
                        num_str = ""
                        for char in rest:
                            if char.isdigit():
                                num_str += char
                            elif num_str:  # 已经开始收集数字，遇到非数字就停止
                                break
                        if num_str:
                            scores[key] = int(num_str)
                except:
                    pass
    
    # 计算加权平均分
    score = None
    if all(v is not None for v in scores.values()):
        weighted_sum = sum(scores[key] * weights[key] for key in scores.keys())
        score = round(weighted_sum)
    result2={"role":"semantic analyst","content":response,"score":score}
    print(result2)
    return result2

if __name__=="__main__":
    path=r"""E:\D\interviewA05\data\records\answer_20260323_175756.wav"""
    ans1=RecordtoText(path)
    print("转译完成。",ans1)
    llm=get_llm(llmname="deepseek")
    ans2=SemanticAnalysis(llm,ans1,"简单介绍一下自己。")
    print(ans1)