class AIIntreviewSystem {
    constructor() {
        this.currentState = 'initial';
        this.selectedPosition = '';
        this.messages = [];
        this.recognition = null;
        this.isRecording = false;
        this.init();
    }

    init() {
        this.renderInitialScreen();
        this.initializeVoiceRecognition();
        this.setupNavButtons();
    }

    setupNavButtons() {
        const historyBtn = document.getElementById('history-btn');
        const improvementBtn = document.getElementById('improvement-btn');

        if (historyBtn) {
            historyBtn.addEventListener('click', () => {
                window.location.href = 'history.html';
            });
        }

        if (improvementBtn) {
            improvementBtn.addEventListener('click', () => {
                window.location.href = 'improvement.html';
            });
        }
    }

    renderInitialScreen() {
        const mainContent = document.getElementById('main-content');
        mainContent.innerHTML = `
            <div class="section">
                <h2>选择面试岗位</h2>
                <div class="form-group">
                    <label for="position">请选择目标岗位：</label>
                    <select id="position">
                        <option value="">-- 请选择 --</option>
                        <option value="java-backend">Java后端开发工程师</option>
                        <option value="web-frontend">Web前端开发工程师</option>
                    </select>
                </div>
                <button id="start-interview">开始模拟面试</button>
            </div>
        `;

        document.getElementById('start-interview').addEventListener('click', () => {
            this.startInterview();
        });
    }

    startInterview() {
        const positionSelect = document.getElementById('position');
        this.selectedPosition = positionSelect.value;

        if (!this.selectedPosition) {
            alert('请选择面试岗位');
            return;
        }

        this.currentState = 'interview';
        this.messages = [];
        this.renderInterviewScreen();
        this.sendMessage('system', '面试开始，我将作为面试官与你进行交流。请准备好回答问题。');
        this.getNextQuestion();
    }

    renderInterviewScreen() {
        const mainContent = document.getElementById('main-content');
        mainContent.innerHTML = `
            <div class="section">
                <h2>模拟面试 - ${this.getSelectedPositionName()}</h2>
                <div class="interview-container">
                    <div class="chat-messages" id="chat-messages">
                        <!-- 消息将在这里动态添加 -->
                    </div>
                    <div class="voice-controls">
                        <button id="start-voice" class="voice-btn">开始语音输入</button>
                        <button id="stop-voice" class="voice-btn" disabled>停止语音输入</button>
                    </div>
                    <div class="input-area">
                        <input type="text" id="user-input" placeholder="请输入你的回答...">
                        <button id="send-btn">发送</button>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendUserMessage();
        });

        document.getElementById('user-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendUserMessage();
            }
        });

        document.getElementById('start-voice').addEventListener('click', () => {
            this.startVoiceRecognition();
        });

        document.getElementById('stop-voice').addEventListener('click', () => {
            this.stopVoiceRecognition();
        });
    }

    getSelectedPositionName() {
        const positionMap = {
            'java-backend': 'Java后端开发工程师',
            'web-frontend': 'Web前端开发工程师'
        };
        return positionMap[this.selectedPosition] || '';
    }

    sendMessage(sender, content) {
        const message = {
            sender,
            content,
            timestamp: new Date().toLocaleTimeString()
        };
        this.messages.push(message);
        this.renderMessages();
    }

    renderMessages() {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';

        this.messages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${msg.sender === 'ai' ? 'ai' : 'user'}`;
            messageDiv.innerHTML = `
                <div class="message-content">${msg.content}</div>
                <div class="message-time">${msg.timestamp}</div>
            `;
            chatMessages.appendChild(messageDiv);
        });

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    sendUserMessage() {
        const userInput = document.getElementById('user-input');
        const content = userInput.value.trim();

        if (content) {
            this.sendMessage('user', content);
            userInput.value = '';
            this.processUserResponse(content);
        }
    }

    async processUserResponse(response) {
        // 模拟AI思考过程
        this.sendMessage('ai', '正在思考...');

        try {
            // 调用后端API获取AI回复
            const aiResponse = await this.getAIResponse(response);
            this.messages.pop(); // 移除"正在思考..."消息
            this.sendMessage('ai', aiResponse);

            // 检查是否面试结束
            if (aiResponse.includes('面试结束') || aiResponse.includes('评估报告')) {
                await this.generateAnalysisReport();
            }
        } catch (error) {
            console.error('Error processing response:', error);
            this.messages.pop();
            this.sendMessage('ai', '抱歉，处理你的回答时出现了错误，请重试。');
        }
    }

    async getAIResponse(userInput) {
        try {
            const response = await fetch('http://localhost:3001/api/interview/answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    position: this.selectedPosition,
                    question: this.messages[this.messages.length - 2]?.content || '',
                    answer: userInput,
                    conversationHistory: this.messages
                })
            });
            
            if (!response.ok) {
                throw new Error('API call failed');
            }
            
            const data = await response.json();
            return data.data.response;
        } catch (error) {
            console.error('Error calling API:', error);
            // 模拟API调用，实际项目中会调用后端服务
            return new Promise((resolve) => {
                setTimeout(() => {
                    const responses = [
                        '你的回答很有见地，能详细解释一下吗？',
                        '这个问题很重要，你是如何理解的？',
                        '很好，我们继续下一个问题。',
                        '你提到了一个关键点，能展开说明吗？',
                        '面试结束，现在开始生成评估报告...'
                    ];
                    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
                    resolve(randomResponse);
                }, 1000);
            });
        }
    }

    async getNextQuestion() {
        try {
            const response = await fetch('http://localhost:3001/api/interview/questions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    position: this.selectedPosition,
                    questionType: 'technical'
                })
            });
            
            if (!response.ok) {
                throw new Error('API call failed');
            }
            
            const data = await response.json();
            const questions = data.data;
            if (questions && questions.length > 0) {
                const randomQuestion = questions[Math.floor(Math.random() * questions.length)].question;
                this.sendMessage('ai', randomQuestion);
            }
        } catch (error) {
            console.error('Error getting questions:', error);
            // 模拟获取下一个问题
            const questions = {
                'java-backend': [
                    '请解释一下Java中的多线程机制？',
                    'Spring Boot的核心特性有哪些？',
                    '如何设计一个高并发的系统？',
                    '数据库索引的工作原理是什么？'
                ],
                'web-frontend': [
                    '请解释一下React中的虚拟DOM？',
                    'CSS Flexbox和Grid的区别是什么？',
                    '如何优化前端性能？',
                    '前端安全防护措施有哪些？'
                ]
            };

            const positionQuestions = questions[this.selectedPosition] || [];
            if (positionQuestions.length > 0) {
                const randomQuestion = positionQuestions[Math.floor(Math.random() * positionQuestions.length)];
                this.sendMessage('ai', randomQuestion);
            }
        }
    }

    initializeVoiceRecognition() {
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'zh-CN';

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('user-input').value = transcript;
            };

            this.recognition.onend = () => {
                this.isRecording = false;
                document.getElementById('start-voice').disabled = false;
                document.getElementById('stop-voice').disabled = true;
            };
        }
    }

    startVoiceRecognition() {
        if (this.recognition) {
            this.isRecording = true;
            document.getElementById('start-voice').disabled = true;
            document.getElementById('stop-voice').disabled = false;
            this.recognition.start();
        } else {
            alert('你的浏览器不支持语音识别功能');
        }
    }

    stopVoiceRecognition() {
        if (this.recognition) {
            this.recognition.stop();
        }
    }

    async generateAnalysisReport() {
        const mainContent = document.getElementById('main-content');
        mainContent.innerHTML = `
            <div class="section">
                <h2>面试评估报告</h2>
                <div class="loading">正在生成评估报告...</div>
            </div>
        `;

        try {
            const response = await fetch('http://localhost:3001/api/analysis/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    position: this.selectedPosition,
                    conversationHistory: this.messages,
                    userAnswers: this.messages.filter(msg => msg.sender === 'user').map(msg => msg.content)
                })
            });

            if (!response.ok) {
                throw new Error('API call failed');
            }

            const analysisData = await response.json();
            const reportResponse = await fetch('http://localhost:3001/api/analysis/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    position: this.selectedPosition,
                    analysisData: analysisData.data
                })
            });

            if (!reportResponse.ok) {
                throw new Error('API call failed');
            }

            const report = await reportResponse.json();
            this.renderAnalysisReport(report.data);
        } catch (error) {
            console.error('Error generating report:', error);
            // 显示默认报告
            this.renderDefaultAnalysisReport();
        }
    }

    renderAnalysisReport(report) {
        const mainContent = document.getElementById('main-content');
        mainContent.innerHTML = `
            <div class="section">
                <h2>面试评估报告</h2>
                <div class="analysis-report">
                    <h3>综合评分</h3>
                    <div class="score-card">
                        <div class="score-item">
                            <div class="score-value">${report.scores.technicalKnowledge || 85}</div>
                            <div class="score-label">技术知识</div>
                        </div>
                        <div class="score-item">
                            <div class="score-value">${report.scores.communication || 80}</div>
                            <div class="score-label">表达能力</div>
                        </div>
                        <div class="score-item">
                            <div class="score-value">${report.scores.problemSolving || 75}</div>
                            <div class="score-label">逻辑思维</div>
                        </div>
                        <div class="score-item">
                            <div class="score-value">${report.scores.positionFit || 90}</div>
                            <div class="score-label">岗位匹配度</div>
                        </div>
                    </div>

                    <h3>亮点分析</h3>
                    <ul class="improvement-list">
                        ${report.highlights.map(highlight => `<li>${highlight}</li>`).join('')}
                    </ul>

                    <div class="improvement-section">
                        <h3>改进建议</h3>
                        <ul class="improvement-list">
                            ${report.improvements.map(improvement => `<li>${improvement}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="improvement-section">
                        <h3>能力提升计划</h3>
                        <ul class="improvement-list">
                            ${report.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                        </ul>
                    </div>

                    <button id="restart-interview">重新开始面试</button>
                    <button id="back-to-home">返回首页</button>
                </div>
            </div>
        `;

        document.getElementById('restart-interview').addEventListener('click', () => {
            this.startInterview();
        });

        document.getElementById('back-to-home').addEventListener('click', () => {
            this.currentState = 'initial';
            this.renderInitialScreen();
        });
    }

    renderDefaultAnalysisReport() {
        const mainContent = document.getElementById('main-content');
        mainContent.innerHTML = `
            <div class="section">
                <h2>面试评估报告</h2>
                <div class="analysis-report">
                    <h3>综合评分</h3>
                    <div class="score-card">
                        <div class="score-item">
                            <div class="score-value">85</div>
                            <div class="score-label">技术知识</div>
                        </div>
                        <div class="score-item">
                            <div class="score-value">80</div>
                            <div class="score-label">表达能力</div>
                        </div>
                        <div class="score-item">
                            <div class="score-value">75</div>
                            <div class="score-label">逻辑思维</div>
                        </div>
                        <div class="score-item">
                            <div class="score-value">90</div>
                            <div class="score-label">岗位匹配度</div>
                        </div>
                    </div>

                    <h3>亮点分析</h3>
                    <ul class="improvement-list">
                        <li>技术知识掌握扎实，能清晰解释核心概念</li>
                        <li>回答问题思路清晰，逻辑连贯</li>
                        <li>对岗位要求理解准确，能结合自身经验</li>
                    </ul>

                    <div class="improvement-section">
                        <h3>改进建议</h3>
                        <ul class="improvement-list">
                            <li>加强对前沿技术的了解和应用</li>
                            <li>提高表达的流畅度和自信心</li>
                            <li>增加项目经验的具体案例分享</li>
                        </ul>
                    </div>

                    <div class="improvement-section">
                        <h3>能力提升计划</h3>
                        <ul class="improvement-list">
                            <li>每周学习一个新技术点，重点关注${this.getSelectedPositionName()}领域</li>
                            <li>进行模拟面试练习，提高表达能力</li>
                            <li>参与开源项目，积累实际项目经验</li>
                        </ul>
                    </div>

                    <button id="restart-interview">重新开始面试</button>
                    <button id="back-to-home">返回首页</button>
                </div>
            </div>
        `;

        document.getElementById('restart-interview').addEventListener('click', () => {
            this.startInterview();
        });

        document.getElementById('back-to-home').addEventListener('click', () => {
            this.currentState = 'initial';
            this.renderInitialScreen();
        });
    }
}

// 初始化系统
new AIIntreviewSystem();