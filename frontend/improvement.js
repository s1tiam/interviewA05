class ImprovementPage {
    constructor() {
        this.init();
    }

    init() {
        this.loadImprovementData();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('back-to-home').addEventListener('click', () => {
            window.location.href = 'index.html';
        });
    }

    async loadImprovementData() {
        try {
            // 模拟API调用，获取用户的面试分析数据
            const analysisData = {
                scores: {
                    technicalKnowledge: 85,
                    communication: 75,
                    problemSolving: 80,
                    positionFit: 90
                },
                improvements: [
                    '加强对前沿技术的了解和应用',
                    '提高表达的流畅度和自信心',
                    '增加项目经验的具体案例分享'
                ]
            };

            const userHistory = [
                {
                    id: 'history_1',
                    position: 'java-backend',
                    date: '2024-01-15',
                    score: 75,
                    status: 'completed'
                },
                {
                    id: 'history_2',
                    position: 'java-backend',
                    date: '2024-01-20',
                    score: 82,
                    status: 'completed'
                }
            ];

            // 调用后端API获取提升建议
            const response = await fetch('http://localhost:3001/api/analysis/improvement', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    position: 'java-backend',
                    analysisData: analysisData,
                    userHistory: userHistory
                })
            });

            if (!response.ok) {
                throw new Error('API call failed');
            }

            const data = await response.json();
            this.renderAbilityAnalysis(analysisData);
            this.renderImprovementSuggestions(data.data);
            this.renderPracticePlan(data.data);
        } catch (error) {
            console.error('Error loading improvement data:', error);
            // 显示默认数据
            const defaultData = {
                scores: {
                    technicalKnowledge: 85,
                    communication: 75,
                    problemSolving: 80,
                    positionFit: 90
                },
                improvements: [
                    '加强对前沿技术的了解和应用',
                    '提高表达的流畅度和自信心',
                    '增加项目经验的具体案例分享'
                ],
                suggestions: [
                    '加强Java SE/EE、Spring Boot/Spring Cloud、MyBatis/Hibernate等核心技术的学习',
                    '多进行口语练习，提高表达能力',
                    '定期进行模拟面试练习',
                    '关注后端领域的最新技术发展',
                    '积累更多项目经验，特别是与目标岗位相关的项目'
                ]
            };
            this.renderAbilityAnalysis(defaultData);
            this.renderImprovementSuggestions(defaultData);
            this.renderPracticePlan(defaultData);
        }
    }

    renderAbilityAnalysis(data) {
        const abilityAnalysis = document.getElementById('ability-analysis');
        let html = '<div class="score-card">';
        
        html += `
            <div class="score-item">
                <div class="score-value">${data.scores.technicalKnowledge}</div>
                <div class="score-label">技术知识</div>
            </div>
            <div class="score-item">
                <div class="score-value">${data.scores.communication}</div>
                <div class="score-label">表达能力</div>
            </div>
            <div class="score-item">
                <div class="score-value">${data.scores.problemSolving}</div>
                <div class="score-label">问题解决</div>
            </div>
            <div class="score-item">
                <div class="score-value">${data.scores.positionFit}</div>
                <div class="score-label">岗位匹配</div>
            </div>
        `;
        
        html += '</div>';
        abilityAnalysis.innerHTML = html;
    }

    renderImprovementSuggestions(data) {
        const suggestions = document.getElementById('improvement-suggestions');
        if (data.suggestions && data.suggestions.length > 0) {
            let html = '<ul class="improvement-list">';
            data.suggestions.forEach(suggestion => {
                html += `<li>${suggestion}</li>`;
            });
            html += '</ul>';
            suggestions.innerHTML = html;
        } else {
            suggestions.innerHTML = '<p>暂无提升建议</p>';
        }
    }

    renderPracticePlan(data) {
        const practicePlan = document.getElementById('practice-plan');
        const plan = this.generatePracticePlan(data);
        
        let html = '<div class="plan-weekly">';
        plan.forEach((week, index) => {
            html += `
                <div class="plan-week">
                    <h3>第${index + 1}周</h3>
                    <ul class="improvement-list">
                        ${week.map(task => `<li>${task}</li>`).join('')}
                    </ul>
                </div>
            `;
        });
        html += '</div>';
        
        practicePlan.innerHTML = html;
    }

    generatePracticePlan(data) {
        // 根据用户的分析结果生成个性化的练习计划
        return [
            [
                '复习核心技术知识（Java基础、Spring框架）',
                '进行1次模拟面试练习',
                '学习一个新技术点（如微服务架构）'
            ],
            [
                '练习算法题，提高问题解决能力',
                '进行1次模拟面试练习',
                '阅读技术博客和文档，了解前沿技术'
            ],
            [
                '参与开源项目或个人项目，积累实际经验',
                '进行1次模拟面试练习',
                '总结学习成果，制定下周计划'
            ],
            [
                '复习之前学习的技术点',
                '进行1次完整的模拟面试',
                '评估进步情况，调整学习计划'
            ]
        ];
    }
}

// 初始化页面
new ImprovementPage();