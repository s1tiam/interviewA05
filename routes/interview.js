const express = require('express');
const router = express.Router();
const interviewService = require('../services/interviewService');

// 获取面试岗位列表
router.get('/positions', (req, res) => {
    try {
        const positions = interviewService.getPositions();
        res.json({ success: true, data: positions });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 获取面试问题
router.post('/questions', (req, res) => {
    try {
        const { position, questionType } = req.body;
        const questions = interviewService.getQuestions(position, questionType);
        res.json({ success: true, data: questions });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 处理用户回答
router.post('/answer', (req, res) => {
    try {
        const { position, question, answer, conversationHistory } = req.body;
        const response = interviewService.processAnswer(position, question, answer, conversationHistory);
        res.json({ success: true, data: response });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 开始新面试
router.post('/start', (req, res) => {
    try {
        const { position } = req.body;
        const interview = interviewService.startInterview(position);
        res.json({ success: true, data: interview });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 结束面试
router.post('/end', (req, res) => {
    try {
        const { interviewId } = req.body;
        const result = interviewService.endInterview(interviewId);
        res.json({ success: true, data: result });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

module.exports = router;