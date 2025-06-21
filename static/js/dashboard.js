// Dashboard JavaScript for VoIP Quality Monitor

class Dashboard {
    constructor() {
        this.socket = null;
        this.mosChart = null;
        this.networkChart = null;
        this.activeCallsTable = null;
        this.historyTable = null;
        this.mosData = [];
        this.networkData = {
            jitter: [],
            packetLoss: [],
            delay: []
        };
        
        this.initializeComponents();
        this.setupWebSocket();
        this.loadInitialData();
    }
    
    initializeComponents() {
        // Initialize charts
        this.initializeCharts();
        
        // Initialize DataTables
        this.initializeDataTables();
        
        // Set up auto-refresh
        setInterval(() => {
            this.refreshSummaryStats();
        }, 30000); // Refresh every 30 seconds
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}`;
        this.socket = io(wsUrl);
        
        this.socket.on('connect', () => {
            console.log('Connected to dashboard updates');
        });
        
        this.socket.on('call_update', (calls) => {
            this.updateActiveCalls(calls);
            this.updateSummaryCards(calls);
        });
        
        this.socket.on('quality_update', (data) => {
            this.updateQualityCharts(data);
        });
        
        this.socket.on('call_started', (data) => {
            this.handleCallStarted(data);
        });
        
        this.socket.on('call_ended', (data) => {
            this.handleCallEnded(data);
            this.refreshCallHistory();
        });
    }
    
    initializeCharts() {
        // MOS Score Chart
        const mosCtx = document.getElementById('mosChart').getContext('2d');
        this.mosChart = new Chart(mosCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'MOS Score',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 1,
                        max: 5,
                        grid: {
                            color: '#e9ecef'
                        }
                    },
                    x: {
                        grid: {
                            color: '#e9ecef'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `MOS Score: ${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                elements: {
                    point: {
                        radius: 3,
                        hoverRadius: 6
                    }
                }
            }
        });
        
        // Network Quality Chart
        const networkCtx = document.getElementById('networkChart').getContext('2d');
        this.networkChart = new Chart(networkCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Jitter (ms)',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        borderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Packet Loss (%)',
                        data: [],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        borderWidth: 2,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        grid: {
                            color: '#e9ecef'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Jitter (ms)'
                        },
                        grid: {
                            color: '#e9ecef'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Packet Loss (%)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label;
                                const value = context.parsed.y.toFixed(2);
                                return `${label}: ${value}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    initializeDataTables() {
        // Initialize history table with DataTables
        this.historyTable = $('#historyTable').DataTable({
            order: [[0, 'desc']], // Sort by start time descending
            pageLength: 25,
            responsive: true,
            language: {
                emptyTable: "No call history available"
            },
            columnDefs: [
                {
                    targets: [3, 4, 5], // MOS columns
                    render: function(data, type, row) {
                        if (type === 'display' && data > 0) {
                            const mosClass = getMosClass(data);
                            return `<span class="mos-score ${mosClass}">${data.toFixed(2)}</span>`;
                        }
                        return data;
                    }
                },
                {
                    targets: [6], // Packet loss column
                    render: function(data, type, row) {
                        if (type === 'display') {
                            return `${data.toFixed(2)}%`;
                        }
                        return data;
                    }
                },
                {
                    targets: [7], // Jitter column
                    render: function(data, type, row) {
                        if (type === 'display') {
                            return `${data.toFixed(1)}ms`;
                        }
                        return data;
                    }
                },
                {
                    targets: [8], // Quality column
                    render: function(data, type, row) {
                        if (type === 'display') {
                            const avgMos = row[3];
                            const quality = getQualityCategory(avgMos);
                            const qualityClass = getQualityClass(quality);
                            return `<span class="quality-badge ${qualityClass}">${quality}</span>`;
                        }
                        return data;
                    }
                }
            ]
        });
    }
    
    loadInitialData() {
        // Load initial summary stats
        this.refreshSummaryStats();
        
        // Load call history
        this.refreshCallHistory();
        
        // Load active calls
        this.refreshActiveCalls();
    }
    
    refreshSummaryStats() {
        fetch('/api/stats/summary')
            .then(response => response.json())
            .then(data => {
                this.updateSummaryStats(data);
            })
            .catch(error => {
                console.error('Error loading summary stats:', error);
            });
    }
    
    refreshCallHistory() {
        fetch('/api/calls/history?limit=100')
            .then(response => response.json())
            .then(data => {
                this.updateCallHistory(data);
            })
            .catch(error => {
                console.error('Error loading call history:', error);
            });
    }
    
    refreshActiveCalls() {
        fetch('/api/calls/active')
            .then(response => response.json())
            .then(data => {
                this.updateActiveCalls(data);
            })
            .catch(error => {
                console.error('Error loading active calls:', error);
            });
    }
    
    updateSummaryStats(data) {
        document.getElementById('active-calls').textContent = data.active_calls || 0;
        document.getElementById('calls-today').textContent = data.today?.call_count || 0;
        
        const avgMos = data.today?.avg_mos || 0;
        const avgPacketLoss = data.today?.avg_packet_loss || 0;
        
        document.getElementById('avg-mos').textContent = avgMos.toFixed(1);
        document.getElementById('avg-packet-loss').textContent = avgPacketLoss.toFixed(1) + '%';
    }
    
    updateSummaryCards(activeCalls) {
        document.getElementById('active-calls').textContent = activeCalls.length;
        
        if (activeCalls.length > 0) {
            const avgMos = activeCalls
                .filter(call => call.current_mos > 0)
                .reduce((sum, call) => sum + call.current_mos, 0) / activeCalls.length;
            
            const avgPacketLoss = activeCalls
                .reduce((sum, call) => sum + (call.packet_loss_rate || 0), 0) / activeCalls.length;
                
            document.getElementById('avg-mos').textContent = avgMos.toFixed(1);
            document.getElementById('avg-packet-loss').textContent = avgPacketLoss.toFixed(1) + '%';
        }
    }
    
    updateActiveCalls(calls) {
        const tbody = document.getElementById('activeCallsBody');
        
        if (calls.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No active calls</td></tr>';
            return;
        }
        
        tbody.innerHTML = calls.map(call => {
            const duration = this.formatDuration(call.start_time);
            const mosScore = call.current_mos || 0;
            const mosClass = getMosClass(mosScore);
            const packetLoss = call.packet_loss_rate || 0;
            const jitter = call.current_jitter || 0;
            
            return `
                <tr>
                    <td><code>${call.call_id.substring(0, 8)}</code></td>
                    <td>${this.truncateString(call.from, 20)}</td>
                    <td>${duration}</td>
                    <td><span class="mos-score ${mosClass}">${mosScore.toFixed(2)}</span></td>
                    <td>${packetLoss.toFixed(2)}%</td>
                    <td>${jitter.toFixed(1)}ms</td>
                    <td><span class="call-status ${call.status}">${call.status}</span></td>
                </tr>
            `;
        }).join('');
    }
    
    updateCallHistory(calls) {
        this.historyTable.clear();
        
        calls.forEach(call => {
            const startTime = new Date(call.start_time).toLocaleString();
            const duration = this.formatDurationSeconds(call.duration);
            const avgMos = call.avg_mos || 0;
            const minMos = call.min_mos || 0;
            const maxMos = call.max_mos || 0;
            const packetLoss = call.packet_loss_rate || 0;
            const avgJitter = call.avg_jitter || 0;
            
            this.historyTable.row.add([
                startTime,
                this.truncateString(call.from, 25),
                duration,
                avgMos,
                minMos,
                maxMos,
                packetLoss,
                avgJitter,
                '' // Quality column (rendered by DataTables)
            ]);
        });
        
        this.historyTable.draw();
    }
    
    updateQualityCharts(data) {
        const timestamp = new Date().toLocaleTimeString();
        const metrics = data.metrics;
        
        // Update MOS chart
        if (this.mosChart.data.labels.length > 20) {
            this.mosChart.data.labels.shift();
            this.mosChart.data.datasets[0].data.shift();
        }
        
        this.mosChart.data.labels.push(timestamp);
        this.mosChart.data.datasets[0].data.push(metrics.mos_score);
        this.mosChart.update('none');
        
        // Update network chart
        if (this.networkChart.data.labels.length > 20) {
            this.networkChart.data.labels.shift();
            this.networkChart.data.datasets[0].data.shift(); // Jitter
            this.networkChart.data.datasets[1].data.shift(); // Packet Loss
        }
        
        this.networkChart.data.labels.push(timestamp);
        this.networkChart.data.datasets[0].data.push(metrics.jitter);
        this.networkChart.data.datasets[1].data.push(metrics.packet_loss_rate);
        this.networkChart.update('none');
    }
    
    handleCallStarted(data) {
        console.log('Call started:', data.call_id);
        this.refreshActiveCalls();
    }
    
    handleCallEnded(data) {
        console.log('Call ended:', data.call_id);
        this.refreshActiveCalls();
    }
    
    formatDuration(startTime) {
        const start = new Date(startTime);
        const now = new Date();
        const diff = Math.floor((now - start) / 1000);
        
        const hours = Math.floor(diff / 3600);
        const minutes = Math.floor((diff % 3600) / 60);
        const seconds = diff % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }
    
    formatDurationSeconds(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    truncateString(str, maxLength) {
        if (str.length <= maxLength) {
            return str;
        }
        return str.substring(0, maxLength - 3) + '...';
    }
}

// Utility functions
function getMosClass(mos) {
    if (mos >= 4.0) return 'mos-excellent';
    if (mos >= 3.5) return 'mos-good';
    if (mos >= 3.0) return 'mos-fair';
    if (mos >= 2.0) return 'mos-poor';
    return 'mos-bad';
}

function getQualityCategory(mos) {
    if (mos >= 4.0) return 'Excellent';
    if (mos >= 3.5) return 'Good';
    if (mos >= 3.0) return 'Fair';
    if (mos >= 2.0) return 'Poor';
    return 'Bad';
}

function getQualityClass(quality) {
    const classMap = {
        'Excellent': 'quality-excellent',
        'Good': 'quality-good',
        'Fair': 'quality-fair',
        'Poor': 'quality-poor',
        'Bad': 'quality-bad'
    };
    return classMap[quality] || 'quality-bad';
}

// Global function for refresh button
function refreshHistory() {
    if (window.dashboard) {
        window.dashboard.refreshCallHistory();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new Dashboard();
});
