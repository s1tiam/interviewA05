# AI模拟面试与能力提升系统

## 项目简介

本项目是一个基于AI的模拟面试系统，旨在帮助计算机专业学生提升面试能力。系统支持针对不同岗位的模拟面试，提供多模态交互方式，并生成详细的面试评估报告和能力提升建议。

## 功能特点

### 1. 岗位化题库与知识库
- 支持Java后端和Web前端两个岗位的面试题库
- 包含技术知识、项目经历、场景题、行为题等多种类型的题目
- 建立了相关知识库，包含核心技术栈、常见面试考点、优秀回答范例等

### 2. 多模态交互式模拟面试
- 支持文字和语音两种输入方式
- AI面试官具备多轮对话能力，能根据回答进行智能追问
- 控制面试节奏，提供自然、流畅的面试体验

### 3. 面试表现多维度分析
- 内容分析：深度分析回答的技术正确性、知识深度、逻辑严谨性、岗位匹配度
- 表达分析：评估语速、清晰度、自信度等表达表现
- 综合报告：生成结构化评估报告，包含各维度得分、亮点与不足分析、改进建议

### 4. 能力提升反馈
- 根据评估结果，推荐提升建议和练习计划
- 记录面试历史，可视化展示能力成长曲线

## 技术栈

### 后端
- **Python + FastAPI**：提供现代、高性能的API服务
- **Node.js + Express**：传统后端服务
- **OpenAI API**：用于对话管理和内容分析
- **本地 Whisper**：用于语音转文字
- **FunASR**：用于语音识别
- **Transformers**：用于情感分析（superb/wav2vec2-base-superb-er模型）
- **本地文件存储**：题库和知识库

### 前端
- HTML5 + CSS3 + JavaScript
- Chart.js：用于生成能力成长曲线
- Web Speech API：用于语音识别

## 项目结构

```
interviewA05/
├── app/
│   └── main.py                  # FastAPI 后端接口
├── CosyVoice/                   # 语音合成子项目
├── data/
│   ├── records/                 # 录音文件目录
│   ├── userreport/              # 面试报告目录
│   ├── interview_questions.json # 面试题库
│   └── knowledge_base.json      # 知识库
├── frontend/
│   ├── index.html               # 主页面
│   ├── history.html             # 面试历史页面
│   ├── improvement.html         # 能力提升页面
│   ├── styles.css               # 样式文件
│   ├── app.js                   # 主页面逻辑
│   ├── history.js               # 历史页面逻辑
│   └── improvement.js           # 提升页面逻辑
├── middleware/
│   └── upload.js                # 文件上传中间件
├── routes/
│   ├── interview.js             # 面试相关路由
│   └── analysis.js              # 分析相关路由
├── services/
│   ├── interviewService.js      # 面试服务
│   └── analysisService.js       # 分析服务
├── structure/
│   ├── Emotion/
│   │   └── EmotionEvaluator.py  # 情感分析模块
│   ├── LLM/
│   │   ├── BlueShirtChat.py     # BlueShirt API客户端
│   │   ├── Deepseek.py          # Deepseek API客户端
│   │   ├── Ollama.py            # Ollama本地LLM客户端
│   │   ├── OpenAI.py            # OpenAI API客户端
│   │   ├── __init__.py
│   │   └── registry.py          # LLM客户端注册器
│   ├── Semantic/
│   │   ├── ffmpeg/              # FFmpeg工具
│   │   ├── RecordToText.py      # 语音转文字模块
│   │   └── __init__.py
│   ├── Interviewer.py           # 面试引擎
│   ├── __init__.py
│   ├── audio_recorder.py        # 音频录制模块
│   ├── models.py                # 数据模型
│   ├── paths.py                 # 路径管理
│   ├── reader.py                # 文本朗读模块
│   └── stt_whisper.py           # Whisper语音转文字
├── test/
│   └── test_server.js           # 测试脚本
├── .env                         # 环境变量
├── .gitignore
├── README.md                    # 项目说明
├── main.py                      # 主入口文件
├── package.json                 # Node.js项目配置
├── requirements.txt             # Python依赖配置
├── server.js                    # Node.js服务器
└── 更新与工具日志.md           # 更新日志
```

## 安装与运行

### 1. 安装 Node.js 依赖

```bash
npm install
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在`.env`文件中配置相关API Key：

```
OPENAI_API_KEY=your_openai_api_key
PORT=3001
NODE_ENV=development
```

### 4. 启动服务器

#### 启动 Node.js 服务器

```bash
npm start
```

#### 启动 FastAPI 服务器

```bash
python app/main.py
```

### 5. 访问系统

- Node.js 服务：`http://localhost:3001`
- FastAPI 服务：`http://localhost:8000`
- FastAPI API 文档：`http://localhost:8000/docs`

## API 接口说明

FastAPI 后端提供以下核心接口：

1. **POST /api/interview/start** - 启动面试
   - 参数：`target_job`（目标岗位）、`llm_backend`（LLM后端）、`llm_model`（LLM模型）
   - 返回：面试ID和目标岗位

2. **POST /api/interview/next-question** - 获取下一题
   - 参数：`interview_id`（面试ID）
   - 返回：下一个面试问题

3. **POST /api/interview/submit-answer** - 提交音频回答
   - 参数：`interview_id`（面试ID）、`audio`（音频文件）
   - 返回：转录文本

4. **GET /api/interview/result** - 获取当前分析结果
   - 参数：`interview_id`（面试ID）
   - 返回：转录文本、语义分析结果、情感分析结果

5. **POST /api/interview/finish** - 结束面试并生成报告
   - 参数：`interview_id`（面试ID）
   - 返回：面试报告内容和路径

## 使用指南

1. **选择面试岗位**：在首页选择Java后端或Web前端岗位
2. **开始面试**：点击"开始模拟面试"按钮
3. **回答问题**：可以通过文字输入或语音输入回答问题
4. **查看评估报告**：面试结束后，系统会生成详细的评估报告
5. **查看面试历史**：点击"面试历史"按钮查看历史记录和能力成长曲线
6. **获取提升建议**：点击"能力提升"按钮获取个性化的提升建议和练习计划

## 注意事项

- 本系统使用OpenAI API进行对话管理和内容分析，需要有效的API Key
- 语音识别功能依赖于浏览器的Web Speech API，部分浏览器可能不支持
- 系统会在本地存储面试历史和评估数据
- 情感分析模块依赖于PyTorch和Transformers库
- 语音转文字功能依赖于本地Whisper模型或FunASR

## 未来优化方向

- 增加更多岗位的题库和知识库
- 集成更多语音识别和情感分析技术
- 开发移动端应用，提供更便捷的使用体验
- 增加社交功能，允许用户分享面试经验和学习资源

## 贡献

欢迎对本项目提出建议和贡献！