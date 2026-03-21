const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const multer = require('multer');
const path = require('path');

// 加载环境变量
dotenv.config();

// 初始化Express应用
const app = express();
const PORT = process.env.PORT || 3001;

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 静态文件服务
app.use('/frontend', express.static(path.join(__dirname, 'frontend')));

// 上传文件配置
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/');
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});

const upload = multer({ storage });

// 路由
const interviewRoutes = require('./routes/interview');
const analysisRoutes = require('./routes/analysis');

app.use('/api/interview', interviewRoutes);
app.use('/api/analysis', analysisRoutes);

// 健康检查
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', message: 'AI Interview System is running' });
});

// 根路径
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend', 'index.html'));
});

// 404处理
app.use((req, res) => {
    res.status(404).json({ error: 'Not Found' });
});

// 错误处理
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Internal Server Error' });
});

// 启动服务器
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

module.exports = app;