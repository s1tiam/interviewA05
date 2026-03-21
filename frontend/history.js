class HistoryPage {
    constructor() {
        this.init();
    }

    init() {
        this.loadHistory();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('back-to-home').addEventListener('click', () => {
            window.location.href = 'index.html';
        });
    }

    async loadHistory() {
        try {
            const response = await fetch('http://localhost:3001/api/analysis/history?userId=test-user');
            if (!response.ok) {
                throw new Error('API call failed');
            }
            const data = await response.json();
            this.renderHistory(data.data);
            this.generateGrowthChart(data.data);
        } catch (error) {
            console.error('Error loading history:', error);
            // 显示模拟数据
            const mockData = [
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
                },
                {
                    id: 'history_3',
                    position: 'web-frontend',
                    date: '2024-01-25',
                    score: 78,
                    status: 'completed'
                },
                {
                    id: 'history_4',
                    position: 'java-backend',
                    date: '2024-01-30',
                    score: 88,
                    status: 'completed'
                }
            ];
            this.renderHistory(mockData);
            this.generateGrowthChart(mockData);
        }
    }

    renderHistory(history) {
        const historyList = document.getElementById('history-list');
        if (history.length === 0) {
            historyList.innerHTML = '<p>暂无面试历史记录</p>';
            return;
        }

        let html = '<table class="history-table">';
        html += '<tr><th>日期</th><th>岗位</th><th>得分</th><th>状态</th></tr>';

        history.forEach(item => {
            html += `
                <tr>
                    <td>${item.date}</td>
                    <td>${item.position === 'java-backend' ? 'Java后端开发工程师' : 'Web前端开发工程师'}</td>
                    <td>${item.score}</td>
                    <td>${item.status === 'completed' ? '已完成' : '进行中'}</td>
                </tr>
            `;
        });

        html += '</table>';
        historyList.innerHTML = html;
    }

    generateGrowthChart(history) {
        const ctx = document.getElementById('growth-chart').getContext('2d');
        
        // 按日期排序
        const sortedHistory = [...history].sort((a, b) => new Date(a.date) - new Date(b.date));
        
        const labels = sortedHistory.map(item => item.date);
        const scores = sortedHistory.map(item => item.score);
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '面试得分',
                    data: scores,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '面试能力成长趋势'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 60,
                        max: 100,
                        title: {
                            display: true,
                            text: '得分'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '日期'
                        }
                    }
                }
            }
        });
    }
}

// 初始化页面
new HistoryPage();