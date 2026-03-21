const http = require('http');
const fs = require('fs');
const path = require('path');

// 测试服务器是否正常启动
function testServer() {
    console.log('测试服务器启动...');
    
    const options = {
        hostname: 'localhost',
        port: 3001,
        path: '/api/health',
        method: 'GET'
    };

    const req = http.request(options, (res) => {
        console.log(`服务器状态码: ${res.statusCode}`);
        res.on('data', (chunk) => {
            console.log('服务器响应:', chunk.toString());
        });
        res.on('end', () => {
            console.log('服务器测试完成');
            testAPIEndpoints();
        });
    });

    req.on('error', (e) => {
        console.error('服务器测试失败:', e.message);
        console.log('尝试启动服务器...');
        startServer();
    });

    req.end();
}

// 测试API端点
function testAPIEndpoints() {
    console.log('\n测试API端点...');
    
    // 测试获取面试岗位列表
    testEndpoint('/api/interview/positions', 'GET');
    
    // 测试获取面试问题
    testEndpoint('/api/interview/questions', 'POST', {
        position: 'java-backend',
        questionType: 'technical'
    });
    
    // 测试分析面试表现
    testEndpoint('/api/analysis/analyze', 'POST', {
        position: 'java-backend',
        conversationHistory: [],
        userAnswers: []
    });
}

// 测试单个API端点
function testEndpoint(path, method, data = null) {
    const options = {
        hostname: 'localhost',
        port: 3001,
        path: path,
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    const req = http.request(options, (res) => {
        console.log(`\n测试端点 ${path}:`);
        console.log(`状态码: ${res.statusCode}`);
        res.on('data', (chunk) => {
            console.log('响应:', chunk.toString());
        });
    });

    req.on('error', (e) => {
        console.error(`测试端点 ${path} 失败:`, e.message);
    });

    if (data) {
        req.write(JSON.stringify(data));
    }
    req.end();
}

// 启动服务器
function startServer() {
    const serverPath = path.join(__dirname, '..', 'server.js');
    if (fs.existsSync(serverPath)) {
        console.log('启动服务器...');
        const { exec } = require('child_process');
        exec('node server.js', { cwd: path.join(__dirname, '..') }, (error, stdout, stderr) => {
            if (error) {
                console.error('启动服务器失败:', error);
                return;
            }
            console.log('服务器启动输出:', stdout);
            if (stderr) {
                console.error('服务器启动错误:', stderr);
            }
            // 等待服务器启动
            setTimeout(testServer, 2000);
        });
    } else {
        console.error('服务器文件不存在');
    }
}

// 运行测试
testServer();