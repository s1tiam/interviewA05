const express = require('express');
const router = express.Router();
const analysisService = require('../services/analysisService');
const upload = require('../middleware/upload');

// 分析面试表现
router.post('/analyze', (req, res) => {
    try {
        const { position, conversationHistory, userAnswers } = req.body;
        const analysis = analysisService.analyzeInterview(position, conversationHistory, userAnswers);
        res.json({ success: true, data: analysis });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 生成评估报告
router.post('/report', (req, res) => {
    try {
        const { position, analysisData } = req.body;
        const report = analysisService.generateReport(position, analysisData);
        res.json({ success: true, data: report });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 上传语音文件进行分析
router.post('/voice-analysis', upload.single('audio'), (req, res) => {
    try {
        const { position } = req.body;
        const audioPath = req.file.path;
        const analysis = analysisService.analyzeVoice(audioPath, position);
        res.json({ success: true, data: analysis });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 获取能力提升建议
router.post('/improvement', (req, res) => {
    try {
        const { position, analysisData, userHistory } = req.body;
        const improvement = analysisService.getImprovementSuggestions(position, analysisData, userHistory);
        res.json({ success: true, data: improvement });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 获取历史面试记录
router.get('/history', (req, res) => {
    try {
        const { userId } = req.query;
        const history = analysisService.getInterviewHistory(userId);
        res.json({ success: true, data: history });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

module.exports = router;