"""
实现的接口
1. POST /api/interview/start - 启动面试，创建面试实例
2. POST /api/interview/next-question - 获取下一个面试问题
3. POST /api/interview/submit-answer - 提交音频回答并进行分析
4. GET /api/interview/result - 获取当前分析结果
5. POST /api/interview/finish - 结束面试并生成报告

启动命令
1. 确保安装了必要的依赖：
   
   ```
   pip install fastapi uvicorn 
   python-multipart
   ```
2. 启动 FastAPI 服务：
   
   ```
   python app/main.py
   ```
3. 服务将在 http://0.0.0.0:8000 上运行，您可以通过以下地址访问 API 文档：
   
   ```
   http://localhost:8000/docs
   ```

注意事项
- 服务默认在 8000 端口运行，如果需要更改端口，请修改 main.py 中的 uvicorn.run 配置
- 在生产环境中，建议修改 CORS 配置，将 allow_origins 设置为具体的前端域名
- 确保项目的依赖项都已安装
"""

import sys
from pathlib import Path

# 把项目根目录加入 Python 模块搜索路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import tempfile
from pathlib import Path

# 导入项目模块
from structure.Interviewer import Interviewer
from structure.models import InterviewConfig, RoundResult, FinalReport

# 创建 FastAPI 应用
app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量存储面试实例
interview_instances: Dict[str, Interviewer] = {}

# 统一响应模型
class ResponseModel(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

# 请求模型
class StartInterviewRequest(BaseModel):
    target_job: str = "目标岗位"
    llm_backend: str = "deepseek"
    llm_model: Optional[str] = None

class SubmitAnswerRequest(BaseModel):
    interview_id: str

# 启动面试
@app.post("/api/interview/start")
async def start_interview(request: StartInterviewRequest):
    try:
        # 创建面试实例
        interviewer = Interviewer(
            target_job=request.target_job,
            llm_backend=request.llm_backend,
            llm_model=request.llm_model
        )
        
        # 生成唯一的面试 ID
        interview_id = f"interview_{id(interviewer)}"
        interview_instances[interview_id] = interviewer
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "interview_id": interview_id,
                "target_job": request.target_job
            }
        )
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"启动面试失败: {str(e)}",
            data=None
        )

# 获取下一题
@app.post("/api/interview/next-question")
async def next_question(interview_id: str = Form(...)):
    try:
        if interview_id not in interview_instances:
            return ResponseModel(
                code=404,
                message="面试实例不存在",
                data=None
            )
        
        interviewer = interview_instances[interview_id]
        
        # 生成下一个问题
        keyword = interviewer.build_keyword()
        raw_rag = interviewer.executeRAG(keyword)
        rag_context = raw_rag
        round_input = interviewer.bulid_question(rag_context)
        
        question = round_input["question"]
        answer = round_input["answer"]
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "question": question
            }
        )
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"获取下一题失败: {str(e)}",
            data=None
        )

# 提交音频回答
@app.post("/api/interview/submit-answer")
async def submit_answer(
    interview_id: str = Form(...),
    audio: UploadFile = File(...)
):
    try:
        if interview_id not in interview_instances:
            return ResponseModel(
                code=404,
                message="面试实例不存在",
                data=None
            )
        
        interviewer = interview_instances[interview_id]
        
        # 保存上传的音频文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 设置上一轮回答的音频路径
            interviewer._last_answer_audio = temp_file_path
            
            # 转换录音为文本
            user_ans = interviewer.Recordtransforming()
            
            # 获取最近的问题
            question = ""
            for item in reversed(interviewer.context):
                if item.get("role") == "question generator":
                    question = item.get("content", {}).get("question", "")
                    break
            
            # 并行进行语义分析和情感分析
            import asyncio
            await asyncio.gather(
                asyncio.to_thread(interviewer.senmantic_analysis, user_ans, question),
                asyncio.to_thread(interviewer.emotional_analysis, user_ans["content"]),
            )
            
            return ResponseModel(
                code=200,
                message="success",
                data={
                    "transcript": user_ans["content"]
                }
            )
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"提交回答失败: {str(e)}",
            data=None
        )

# 获取当前分析结果
@app.get("/api/interview/result")
async def get_result(interview_id: str):
    try:
        if interview_id not in interview_instances:
            return ResponseModel(
                code=404,
                message="面试实例不存在",
                data=None
            )
        
        interviewer = interview_instances[interview_id]
        
        # 提取最近的分析结果
        semantic_result = None
        emotion_result = None
        transcript = None
        
        for item in reversed(interviewer.context):
            if item.get("role") == "semantic analyst":
                semantic_result = item
            elif item.get("role") == "emotional analyser":
                emotion_result = item
            elif item.get("role") == "interviewee":
                transcript = item.get("content", "")
            
            if semantic_result and emotion_result and transcript:
                break
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "transcript": transcript,
                "semantic_analysis": semantic_result,
                "emotion_analysis": emotion_result
            }
        )
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"获取分析结果失败: {str(e)}",
            data=None
        )

# 结束面试并生成报告
@app.post("/api/interview/finish")
async def finish_interview(interview_id: str = Form(...)):
    try:
        if interview_id not in interview_instances:
            return ResponseModel(
                code=404,
                message="面试实例不存在",
                data=None
            )
        
        interviewer = interview_instances[interview_id]
        
        # 生成最终报告
        report_path = Path("data/userreport") / f"{interview_id}_report.md"
        interviewer.build_final_report(str(report_path))
        
        # 读取报告内容
        report_content = report_path.read_text(encoding="utf-8")
        
        # 清理面试实例
        del interview_instances[interview_id]
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "report": report_content,
                "report_path": str(report_path)
            }
        )
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"结束面试失败: {str(e)}",
            data=None
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)