const fs = require('fs');
const path = require('path');
const { OpenAI } = require('openai');

// 加载题库和知识库
const questionsPath = path.join(__dirname, '..', 'data', 'interview_questions.json');
const knowledgePath = path.join(__dirname, '..', 'data', 'knowledge_base.json');

const questionsData = JSON.parse(fs.readFileSync(questionsPath, 'utf8'));
const knowledgeData = JSON.parse(fs.readFileSync(knowledgePath, 'utf8'));

// 初始化OpenAI客户端
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

class InterviewService {
    constructor() {
        this.activeInterviews = new Map();
    }

    // 获取面试岗位列表
    getPositions() {
        return Object.keys(questionsData);
    }

    // 获取面试问题
    getQuestions(position, questionType) {
        if (!questionsData[position]) {
            throw new Error('Invalid position');
        }

        const questions = questionsData[position][questionType] || [];
        // 随机选择3个问题
        const shuffled = questions.sort(() => 0.5 - Math.random());
        return shuffled.slice(0, 3);
    }

    // 开始新面试
    startInterview(position) {
        const interviewId = `interview_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const interview = {
            id: interviewId,
            position,
            startTime: new Date().toISOString(),
            questions: [],
            answers: [],
            status: 'active'
        };

        // 生成初始问题
        const initialQuestions = this.getQuestions(position, 'technical');
        interview.questions = initialQuestions;

        this.activeInterviews.set(interviewId, interview);
        return interview;
    }

    // 处理用户回答
    async processAnswer(position, question, answer, conversationHistory) {
        try {
            // 构建系统提示
            const systemPrompt = this.buildSystemPrompt(position);
            
            // 构建对话历史
            const messages = [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: question },
                { role: 'assistant', content: answer }
            ];

            // 调用OpenAI API获取回复
            const response = await openai.chat.completions.create({
                model: 'gpt-3.5-turbo',
                messages: messages,
                temperature: 0.7,
                max_tokens: 500
            });

            return {
                response: response.choices[0].message.content,
                followUp: this.generateFollowUpQuestion(position, question, answer)
            };
        } catch (error) {
            console.error('Error processing answer:', error);
            // 生成默认回复
            return {
                response: '你的回答很有见地，我们继续下一个问题。',
                followUp: null
            };
        }
    }

    // 结束面试
    endInterview(interviewId) {
        const interview = this.activeInterviews.get(interviewId);
        if (!interview) {
            throw new Error('Interview not found');
        }

        interview.status = 'completed';
        interview.endTime = new Date().toISOString();
        this.activeInterviews.delete(interviewId);

        return interview;
    }

    // 构建系统提示
    buildSystemPrompt(position) {
        const knowledge = knowledgeData[position];
        return `你是一位专业的${position === 'java-backend' ? 'Java后端' : 'Web前端'}面试官，负责对候选人进行技术面试。请根据以下信息进行面试：

核心技术栈：${knowledge.core_tech.join(', ')}

常见面试考点：${knowledge.common_topics.join(', ')}

评估标准：${Object.entries(knowledge.evaluation_criteria).map(([key, value]) => `${key}: ${value}`).join('\n')}

请保持专业、友好的态度，根据候选人的回答进行追问，并控制面试节奏。`;
    }

    // 生成追问问题
    generateFollowUpQuestion(position, question, answer) {
        // 简单实现：从题库中随机选择一个相关的追问
        const questions = questionsData[position];
        const allQuestions = [...(questions.technical || []), ...(questions.project || []), ...(questions.behavioral || [])];
        
        const relatedQuestions = allQuestions.filter(q => 
            q.question !== question && 
            q.keywords.some(keyword => answer.includes(keyword))
        );

        if (relatedQuestions.length > 0) {
            const randomIndex = Math.floor(Math.random() * relatedQuestions.length);
            return relatedQuestions[randomIndex].question;
        }

        return null;
    }
}

module.exports = new InterviewService();