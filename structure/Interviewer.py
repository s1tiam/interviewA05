from __future__ import annotations

#from encodings.punycode import selective_find
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Sequence
import re
from .LLM.registry import LLMClient, get_llm
from .paths import DEFAULT_FINAL_REPORT_PATH, DEFAULT_RECORDS_DIR, USER_REPORT_DIR, ensure_data_dirs
from .reader import read_aloud
from .stt_whisper import WhisperSTT
from .audio_recorder import is_round_finished as audio_round_finished
from .audio_recorder import record_until_silence

class Interviewer:
    """
    第4部分：结构驱动器（interviewer）
    - 多轮实时交互主流程
    - 回答结束判定（基于时长 + 尾部静音）
    - 串联 #2 语义评估 与 #3 情感评估
    - 决策“追问 / 进入下一题”
    - 生成最终汇总报告
    """

    def __init__(
        self,
        *,
        stt_service=None,
        semantic_evaluator=None,
        emotion_evaluator=None,
        rag_retriever: Callable[[str, int], Sequence[str]] | None = None,
        llm: LLMClient | Any | None = None,
        llm_backend: str = "deepseek",
        llm_model: str | None = None,
        keyword_generator: Any | None = None,
        question_generator: Any | None = None,
        target_job: str = "目标岗位",
        rag_top_k: int = 3,
    ) -> None:
        self.stt = stt_service if stt_service is not None else WhisperSTT()
        """#2 默认用本地 Whisper；也可传入自定义 transcribe(audio_path)->str"""

        self.semantic = semantic_evaluator
        """2部分工具：语音转字符串"""
        self.emotion = emotion_evaluator
        """3部分工具：语义分析，产生[本问题的]情感分析报告"""

        self.rag_retriever = rag_retriever

        if llm is not None:
            self.llm = llm
        elif keyword_generator is not None:
            self.llm = keyword_generator
        elif question_generator is not None:
            self.llm = question_generator
        else:
            self.llm = get_llm(llm_backend, model=llm_model)
        """统一 LLM 入口（来自 LLM/registry 或兼容旧 execute 接口）"""
        self.targetjob = target_job
        """候选人的目标职位"""
        self.rag_top_k = rag_top_k
        """rag所用的topk的k值"""
        self.context=[]
        """历史累计，每处理一轮会往里面放放。"""
        self._last_answer_audio: str | None = None
        """上一轮用户回答录音路径（供 STT / 情感分析使用）"""
        ensure_data_dirs()

    def get_sound(
        self,
        *,
        output_dir: str = DEFAULT_RECORDS_DIR,
        filename_prefix: str = "answer",
        silence_threshold_db: float = -40.0,
        silence_duration_seconds: float = 1.0,
        output_format: str = "wav",
    ) -> str:
        """
        函数：开启录制，录制下被试者的回答；
        """
        audio_path = record_until_silence(
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            silence_threshold_db=silence_threshold_db,
            silence_duration_seconds=silence_duration_seconds,
            output_format=output_format,
        )
        return str(audio_path)

    def collect_historical_context(self) -> str:
        """
        统一格式化历史上下文：
        - 近2轮：详细结果
        - 更早轮次：仅内容与情感分析
        """
        if not isinstance(self.context, list) or not self.context:
            return "【近2轮详细结果】\n- （无）\n【更早轮次(仅内容+情感分析)】\n- （无）"

        recent_detailed = self.context[-2:]
        earlier_filtered = [
            item for item in self.context[:-2] if item.get("role") in {"interviewee", "emotional analyser"}
        ]

        def _format_context_block(items: list[dict], title: str) -> str:
            if not items:
                return f"{title}\n- （无）"
            lines = [title]
            for idx, item in enumerate(items, start=1):
                lines.append(f"- [{idx}] role: {item.get('role', 'unknown')}")
                lines.append(f"  content: {item.get('content', '')}")
            return "\n".join(lines)

        recent_text = _format_context_block(recent_detailed, "【近2轮详细结果】")
        earlier_text = _format_context_block(earlier_filtered, "【更早轮次(仅内容+情感分析)】")
        return f"{recent_text}\n{earlier_text}"

    def build_keyword(
        self,
    ) -> tuple[str, list[str], str]:
        history_text =self.collect_historical_context()
        #TODO:在此处决策：是否进行追问。如果进行追问，考虑增设特别格式或者接入后续prompt

        #TODO:需要传递一些[追问]的参数：如果你要使用大模型判断是否要对用户的回应进行追问，尝试使它返回</Followup>并解析。

        prompt = f"""
            你是一位专业的面试官，现在你面对着一个面试{self.targetjob}的面试者。
            交流历史:{history_text}
            请根据上下文内容,以关键词形式给出你将要向考察者提问的问题/知识点/关键点。
            只允许使用以下格式输出你的查询意图:
            </keyword>词1,词2,词3</keyword>
            "请严格按 </keyword>...</keyword> 返回，不要输出额外解释。"
            """

        raw = self.llm.execute(prompt)

        keyword_match = re.search(r"</keyword>(.*?)</keyword>", raw, flags=re.IGNORECASE | re.DOTALL)

        body = keyword_match.group(1) if keyword_match else raw
        parts = re.split(r"[,\n;；、]+", body)
        keywords = [p.strip() for p in parts if p.strip()]
        keywords = keywords[: self.rag_top_k * 2]

        self.context.append({"role": "keyword generator", "content": {"keywords": keywords}})

        return keywords

    def executeRAG(self,keywords):
        #TODO:根据keywords从数据库中获取结果.
        pass

    def bulid_question(self,rag_context,followup):
        historical_context=self.collect_historical_context()
        prompt4asking=f"""
        你是一位专业的面试官，现在你面对着一个面试{self.targetjob}的面试者。
        本轮{followup}追问轮次。（追问轮次需要依据）
        请你根据之前对面试者的了解，综合职位的专业要求，向面试者提供问题。
        你的问题会经过数据库的查找与匹配来增强你的专业性。
        历史上下文：
        {historical_context}
        你必须优先参考下面检索到的资料（如果有）：
        {rag_context}
        请你以
        </question>问题</question>
        </answer>答案</answer>
        的格式返回你的问题和答案。它们会交由其他的智能体评判。
        """
        raw = self.llm.execute(prompt4asking)

        question_match = re.search(r"</question>(.*?)</question>", raw, flags=re.IGNORECASE | re.DOTALL)
        answer_match = re.search(r"</answer>(.*?)</answer>", raw, flags=re.IGNORECASE | re.DOTALL)
        question = question_match.group(1).strip() if question_match else ""
        answer = answer_match.group(1).strip() if answer_match else ""

        result = {"question": question, "answer": answer}
        if not isinstance(self.context, list):
            self.context = []
        self.context.append({"role": "question generator", "content": result})
        print("关键词:",result)
        return result

    def senmantic_analysis(self):
        """
        #2 初步：语音转文本（Whisper），结果写入 context。
        完整「语义打分」可在有 InterviewContext / 题目文本时再接入 self.semantic.evaluate。
        """
        path = self._last_answer_audio
        if not path:
            return
        p = Path(path)
        if not p.is_file():
            return
        text = self.stt.transcribe(str(p))
        if not isinstance(self.context, list):
            self.context = []
        self.context.append(
            {
                "role": "semantic analyser",
                "content": {"transcript": text, "audio_path": str(p)},
            }
        )
        print("转译内容:",text)

    def emotional_analysis(self):
        #TODO:分析用户原声中的情感倾向（#3内容）
        pass

    def reader(self, question: str) -> None:
        """Windows 下朗读文本（系统 TTS，见 tts_windows.read_aloud）。"""
        print("问题", question)
        read_aloud(question)

    def new_round(self):
        keyword=self.build_keyword()
        """根据大模型生成的关键词（格式： List[keywords]）进行数据库检索，获取rag_context字段（字符串形式）"""
        raw_rag=self.executeRAG(keyword)
        #TODO: 将结果后处理，得到字符串形式的rag_context
        rag_context=raw_rag
        roundinput=self.bulid_question(rag_context, "")
        """获取到本轮需要的问题和答案"""
        question=roundinput["question"]
        answer=roundinput["answer"]
        self.reader(question)
        """开始录音"""
        self._last_answer_audio = self.get_sound(
            output_dir=DEFAULT_RECORDS_DIR,
            filename_prefix="answer",
            silence_threshold_db=-40.0,
            silence_duration_seconds=1.0,
            output_format="wav",
        )
        """获取用户原声。"""

        """将【回答内容】和【专业性/清晰性报告】写入上下文context"""
        self.senmantic_analysis()

        """将【回答的情感倾向】写入上下文context"""
        self.emotional_analysis()

    def build_final_report(
        self,
        output_path: str = DEFAULT_FINAL_REPORT_PATH,
    ):
        # 相对路径统一写到 data/userreport/；绝对路径则按调用方指定
        p = Path(output_path)
        if p.is_absolute():
            out = p
        else:
            out = USER_REPORT_DIR / p.name
        out.parent.mkdir(parents=True, exist_ok=True)

        ev_lines: list[str] = [
            f"目标岗位: {self.targetjob}",
        ]

        if isinstance(self.context, list) and self.context:
            ev_lines.append("【补充：Interviewer 内部 context 片段（最近若干条）】")
            for item in self.context:
                ev_lines.append(f"- role={item.get('role')}: {item.get('content')}")
        evidence = "\n".join(ev_lines)

        llm_prompt = f"""你是一位资深技术面试与职业辅导顾问。下面是一次面试的全部客观记录（含每轮语义/情感评估器的输出）。
        请**自行综合判断**，不要简单复述分数；要指出可改进点、优势、以及面向「{self.targetjob}」的发展路径。
        
        【面试证据】
        {evidence}
        
        请**严格**按下列标签输出（每个块用同名闭合标签包裹），使用中文：
        
        </knowledge_defects>
        （多条，每行一条，以 - 开头；知识/原理/经验上的不足或缺口）
        </knowledge_defects>
        
        </performance_defects>
        （多条；表达、结构、自信度、语速与临场表现等）
        </performance_defects>
        
        </strengths>
        （多条；候选人已展现的优势）
        </strengths>
        
        </development_direction>
        （一段连贯文字：未来 3–12 个月建议的发展重心与能力栈）
        </development_direction>
        
        </recommendations>
        （多条；可执行的学习/练习优先级，从最重要到次要）
        </recommendations>
        
        </summary>
        （一段总括：当前短板、机会点、对候选人的鼓励性总结）
        </summary>
        
        除上述标签外不要输出其它说明文字。
        """
        raw_llm = self.llm.execute(llm_prompt)
        kd_text = (
            m.group(1).strip()
            if (m := re.search(r"</knowledge_defects>(.*?)</knowledge_defects>", raw_llm, flags=re.IGNORECASE | re.DOTALL))
            else ""
        )
        pd_text = (
            m.group(1).strip()
            if (m := re.search(r"</performance_defects>(.*?)</performance_defects>", raw_llm, flags=re.IGNORECASE | re.DOTALL))
            else ""
        )
        st_text = (
            m.group(1).strip()
            if (m := re.search(r"</strengths>(.*?)</strengths>", raw_llm, flags=re.IGNORECASE | re.DOTALL))
            else ""
        )
        dev_text = (
            m.group(1).strip()
            if (m := re.search(r"</development_direction>(.*?)</development_direction>", raw_llm, flags=re.IGNORECASE | re.DOTALL))
            else ""
        )
        rec_text = (
            m.group(1).strip()
            if (m := re.search(r"</recommendations>(.*?)</recommendations>", raw_llm, flags=re.IGNORECASE | re.DOTALL))
            else ""
        )
        sum_text = (
            m.group(1).strip()
            if (m := re.search(r"</summary>(.*?)</summary>", raw_llm, flags=re.IGNORECASE | re.DOTALL))
            else ""
        )

        knowledge_defects: list[str] = []
        for ln in kd_text.splitlines():
            s = ln.strip()
            if not s:
                continue
            knowledge_defects.append(s[1:].strip() if s.startswith(("-", "•", "·")) else s)
        performance_defects: list[str] = []
        for ln in pd_text.splitlines():
            s = ln.strip()
            if not s:
                continue
            performance_defects.append(s[1:].strip() if s.startswith(("-", "•", "·")) else s)
        strengths_llm: list[str] = []
        for ln in st_text.splitlines():
            s = ln.strip()
            if not s:
                continue
            strengths_llm.append(s[1:].strip() if s.startswith(("-", "•", "·")) else s)
        recommendations_llm: list[str] = []
        for ln in rec_text.splitlines():
            s = ln.strip()
            if not s:
                continue
            recommendations_llm.append(s[1:].strip() if s.startswith(("-", "•", "·")) else s)

        s1 = "## 一、知识性缺陷\n\n" + (
            "\n".join(f"- {b}" for b in knowledge_defects) if knowledge_defects else "（无）"
        ) + "\n"
        s2 = "## 二、表现缺陷\n\n" + (
            "\n".join(f"- {b}" for b in performance_defects) if performance_defects else "（无）"
        ) + "\n"
        s3 = "## 三、优势\n\n" + (
            "\n".join(f"- {b}" for b in strengths_llm) if strengths_llm else "（无）"
        ) + "\n"
        s4 = "## 四、发展方向\n\n" + (dev_text.strip() or "（无）") + "\n"
        s5 = "## 五、学习与实践建议\n\n" + (
            "\n".join(f"- {b}" for b in recommendations_llm) if recommendations_llm else "（无）"
        ) + "\n"
        s6 = "## 六、总结\n\n" + (sum_text.strip() or "（无）") + "\n"

        report_body = f"""# 面试综合报告
        {s1}{s2}{s3}{s4}{s5}{s6}
        """
        out.write_text(report_body, encoding="utf-8")
        print(report_body)

    def execute_all(self):
        self.reader("请你介绍一下自己。")
        self.get_sound(
            output_dir=DEFAULT_RECORDS_DIR,
            filename_prefix="answer",
            silence_threshold_db=-40.0,
            silence_duration_seconds=1.0,
            output_format="wav",
        )
        """获取用户回答。"""
        for i in range(0,2):
            self.new_round()
            #进行固定5轮的提问。
            #TODO：【加分项】在此处可以考虑增加”面试节奏控制“？
            #TODO：可考虑增加【追问不算轮数】的机制。

        self.build_final_report(DEFAULT_FINAL_REPORT_PATH)
        

