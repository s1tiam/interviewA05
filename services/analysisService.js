const fs = require('fs');
const path = require('path');
const { OpenAI } = require('openai');

// 加载知识库
const knowledgePath = path.join(__dirname, '..', 'data', 'knowledge_base.json');
const knowledgeData = JSON.parse(fs.readFileSync(knowledgePath, 'utf8'));

// 初始化OpenAI客户端
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

class AnalysisService {
    constructor() {
        this.interviewHistory = new Map();
    }

    // 分析面试表现
    async analyzeInterview(position, conversationHistory, userAnswers) {
        try {
            // 构建系统提示
            const systemPrompt = this.buildAnalysisPrompt(position);
            
            // 构建对话历史
            const messages = [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: JSON.stringify({
                    conversationHistory,
                    userAnswers
                })
                }
            ];

            // 调用OpenAI API进行分析
            const response = await openai.chat.completions.create({
                model: 'gpt-3.5-turbo',
                messages: messages,
                temperature: 0.7,
                max_tokens: 1000
            });

            // 解析分析结果
            const analysis = JSON.parse(response.choices[0].message.content);
            return analysis;
        } catch (error) {
            console.error('Error analyzing interview:', error);
            // 生成默认分析结果
            return this.generateDefaultAnalysis(position);
        }
    }

    // 生成评估报告
    generateReport(position, analysisData) {
        const knowledge = knowledgeData[position];
        
        return {
            position: position === 'java-backend' ? 'Java后端开发工程师' : 'Web前端开发工程师',
            overallScore: analysisData.overallScore || 80,
            scores: analysisData.scores || {
                technicalKnowledge: 85,
                communication: 80,
                problemSolving: 75,
                positionFit: 90
            },
            highlights: analysisData.highlights || [
                '技术知识掌握扎实',
                '回答问题思路清晰',
                '对岗位要求理解准确'
            ],
            improvements: analysisData.improvements || [
                '加强对前沿技术的了解',
                '提高表达的流畅度',
                '增加项目经验的具体案例'
            ],
            suggestions: this.generateImprovementSuggestions(position, analysisData),
            timestamp: new Date().toISOString()
        };
    }

    // 分析语音
    analyzeVoice(audioPath, position) {
        // 模拟语音分析，实际项目中可以集成语音识别API
        return {
            speechRate: '适中',
            clarity: '清晰',
            confidence: '自信',
            suggestions: [
                '保持当前的语速和清晰度',
                '在回答复杂问题时可以适当放慢语速'
            ]
        };
    }

    // 获取能力提升建议
    getImprovementSuggestions(position, analysisData, userHistory) {
        const knowledge = knowledgeData[position];
        const suggestions = [];

        // 根据分析结果生成针对性建议
        if (analysisData.scores && analysisData.scores.technicalKnowledge < 80) {
            suggestions.push(`加强${knowledge.core_tech.slice(0, 3).join('、')}等核心技术的学习`);
        }

        if (analysisData.scores && analysisData.scores.communication < 80) {
            suggestions.push('多进行口语练习，提高表达能力');
        }

        if (analysisData.scores && analysisData.scores.problemSolving < 80) {
            suggestions.push('多做算法题和系统设计题，提高问题解决能力');
        }

        // 添加通用建议
        suggestions.push('定期进行模拟面试练习');
        suggestions.push(`关注${position === 'java-backend' ? '后端' : '前端'}领域的最新技术发展`);
        suggestions.push('积累更多项目经验，特别是与目标岗位相关的项目');

        return suggestions;
    }

    // 获取历史面试记录
    getInterviewHistory(userId) {
        // 模拟历史记录，实际项目中可以存储在数据库中
        return [
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
    }

    // 构建分析提示
    buildAnalysisPrompt(position) {
        const knowledge = knowledgeData[position];
        return `你是一位专业的面试分析师，负责评估候选人的面试表现。请根据以下信息分析候选人的面试表现：

岗位：${position === 'java-backend' ? 'Java后端开发工程师' : 'Web前端开发工程师'}

核心技术栈：${knowledge.core_tech.join(', ')}

评估标准：${Object.entries(knowledge.evaluation_criteria).map(([key, value]) => `${key}: ${value}`).join('\n')}

请对候选人的回答进行分析，包括以下方面：
1. 技术知识掌握程度
2. 表达能力和沟通技巧
3. 问题解决能力
4. 与岗位的匹配度

请生成一个JSON格式的分析结果，包含以下字段：
- overallScore: 综合评分（0-100）
- scores: 各维度评分
- highlights: 亮点
- improvements: 需要改进的地方
- suggestions: 改进建议`;
    }

    // 生成默认分析结果
    generateDefaultAnalysis(position) {
        return {
            overallScore: 80,
            scores: {
                technicalKnowledge: 85,
                communication: 80,
                problemSolving: 75,
                positionFit: 90
            },
            highlights: [
                '技术知识掌握扎实',
                '回答问题思路清晰',
                '对岗位要求理解准确'
            ],
            improvements: [
                '加强对前沿技术的了解',
                '提高表达的流畅度',
                '增加项目经验的具体案例'
            ],
            suggestions: [
                '定期进行模拟面试练习',
                '关注相关领域的最新技术发展',
                '积累更多项目经验'
            ]
        };
    }

    // 生成改进建议
    generateImprovementSuggestions(position, analysisData) {
        const suggestions = [];

        // 根据分析结果生成针对性建议
        if (analysisData.improvements) {
            analysisData.improvements.forEach(improvement => {
                suggestions.push(`针对"${improvement}"，建议你加强相关知识的学习和实践`);
            });
        }

        // 添加通用建议
        suggestions.push('制定学习计划，定期复习核心知识点');
        suggestions.push('多参加技术社区活动，扩展技术视野');
        suggestions.push('寻找实习或项目机会，积累实际经验');

        return suggestions;
    }
}

module.exports = new AnalysisService();