// Simplified Dashboard JavaScript for VoIP Quality Monitor

class Dashboard {
    constructor() {
        this.mosChart = null;
        this.networkChart = null;
        this.pollingInterval = null;
        this.lastCallIds = null;
        this.initializeCharts();
        this.loadInitialData();
        this.setupPolling();
        this.setupRefreshTimer();
    }
    
    setupPolling() {
        console.log('Setting up HTTP polling for real-time updates');
        
        // Clear any existing polling
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        // Poll every 2 seconds for updates
        this.pollingInterval = setInterval(() => {
            this.pollForUpdates();
        }, 2000);
        
        // Initial poll
        this.pollForUpdates();
    }
    
    pollForUpdates() {
        // Poll active calls and update counter
        fetch('/api/calls/active')
            .then(response => response.json())
            .then(data => {
                this.updateActiveCalls(data);
            })
            .catch(error => console.log('Active calls polling error:', error));
        
        // Poll summary stats
        fetch('/api/stats/summary')
            .then(response => response.json())
            .then(data => {
                this.updateSummaryStats(data);
            })
            .catch(error => console.log('Stats polling error:', error));
            
        // Poll gateway status
        fetch('/api/gateway/status')
            .then(response => response.json())
            .then(data => {
                this.updateGatewayStatus(data);
            })
            .catch(error => console.log('Gateway polling error:', error));
    }
    
    setupRefreshTimer() {
        // Refresh data every 30 seconds
        setInterval(() => {
            this.loadCallHistory();
            this.loadSummaryStats();
            this.refreshGatewayStatus();
            this.refreshRegisteredDevices();
        }, 30000);
    }
    
    loadInitialData() {
        this.loadActiveCalls();
        this.loadCallHistory();
        this.loadSummaryStats();
        this.refreshGatewayStatus();
        this.refreshRegisteredDevices();
    }
    
    loadActiveCalls() {
        fetch('/api/calls/active')
            .then(response => response.json())
            .then(data => this.updateActiveCalls(data))
            .catch(error => console.error('Error loading active calls:', error));
    }
    
    loadCallHistory() {
        fetch('/api/calls/history')
            .then(response => response.json())
            .then(data => this.updateCallHistory(data))
            .catch(error => console.error('Error loading call history:', error));
    }
    
    loadSummaryStats() {
        fetch('/api/stats/summary')
            .then(response => response.json())
            .then(data => this.updateSummaryStats(data))
            .catch(error => console.error('Error loading summary stats:', error));
    }
    
    initializeCharts() {
        // Initialize MOS Chart
        const mosCtx = document.getElementById('mosChart');
        if (mosCtx) {
            this.mosChart = new Chart(mosCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'MOS Score',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1,
                        fill: true
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
                            title: {
                                display: true,
                                text: 'MOS Score'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
        }

        // Initialize Network Quality Chart
        const networkCtx = document.getElementById('networkChart');
        if (networkCtx) {
            this.networkChart = new Chart(networkCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Packet Loss (%)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        yAxisID: 'y'
                    }, {
                        label: 'Jitter (ms)',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        yAxisID: 'y1'
                    }]
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
                            display: true,
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Packet Loss (%)'
                            },
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Jitter (ms)'
                            },
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    }
                }
            });
        }
    }

    setupPolling() {
        // More frequent polling for real-time updates
        setInterval(() => {
            this.refreshActiveCalls();
            this.refreshGatewayStatus();
        }, 2000); // Poll every 2 seconds for active data
        
        setInterval(() => {
            this.refreshSummaryStats();
            this.refreshRegisteredDevices();
        }, 5000); // Poll every 5 seconds for less critical data
        
        setInterval(() => {
            this.refreshCallHistory();
        }, 10000); // Poll every 10 seconds for history
    }
    
    setupRefreshTimer() {
        // Refresh every 30 seconds
        setInterval(() => {
            this.refreshSummaryStats();
        }, 30000);
    }
    
    loadInitialData() {
        this.refreshActiveCalls();
        this.refreshCallHistory();
        this.refreshSummaryStats();
        this.refreshGatewayStatus();
        this.refreshRegisteredDevices();
    }
    
    refreshActiveCalls() {
        fetch('/api/calls/active')
            .then(response => response.json())
            .then(data => this.updateActiveCalls(data))
            .catch(error => console.error('Error loading active calls:', error));
    }
    
    refreshCallHistory() {
        fetch('/api/calls/history')
            .then(response => response.json())
            .then(data => this.updateCallHistory(data))
            .catch(error => console.error('Error loading call history:', error));
    }
    
    refreshSummaryStats() {
        fetch('/api/stats/summary')
            .then(response => response.json())
            .then(data => this.updateSummaryStats(data))
            .catch(error => console.error('Error loading summary stats:', error));
    }
    
    refreshGatewayStatus() {
        fetch('/api/gateway/status')
            .then(response => response.json())
            .then(data => this.updateGatewayStatus(data))
            .catch(error => console.error('Error loading gateway status:', error));
    }
    
    refreshRegisteredDevices() {
        fetch('/api/devices/registered')
            .then(response => response.json())
            .then(data => this.updateRegisteredDevices(data))
            .catch(error => console.error('Error loading registered devices:', error));
    }
    
    updateDashboard(data) {
        if (data.active_calls) {
            this.updateActiveCalls(data.active_calls);
        }
        if (data.summary_stats) {
            this.updateSummaryStats(data.summary_stats);
        }
    }
    
    updateActiveCalls(calls) {
        const tbody = document.getElementById('activeCallsBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        // Update Active Calls counter in top-left card
        const activeCallsElement = document.getElementById('active-calls');
        if (activeCallsElement) {
            activeCallsElement.textContent = calls.length;
        }
        
        if (calls.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No active calls</td></tr>';
            return;
        }
        
        calls.forEach(call => {
            const row = document.createElement('tr');
            const codec = call.codec || 'G.711';
            const codecClass = codec === 'Opus' ? 'bg-primary' : 'bg-secondary';
            
            row.innerHTML = `
                <td>${this.truncateString(call.call_id, 20)}</td>
                <td>${call.from_address || 'N/A'}</td>
                <td>${call.to_address || 'N/A'}</td>
                <td>${this.formatDuration(call.start_time)}</td>
                <td><span class="badge ${codecClass}">${codec}</span></td>
                <td><span class="badge ${this.getMosClass(call.current_mos || 0)}">${(call.current_mos || 0).toFixed(2)}</span></td>
                <td>${(call.packet_loss_rate || 0).toFixed(2)}%</td>
                <td>${(call.jitter || 0).toFixed(2)}ms</td>
                <td><span class="badge ${this.getQualityClass(this.getQualityCategory(call.current_mos || 0))}">${this.getQualityCategory(call.current_mos || 0)}</span></td>
            `;
            tbody.appendChild(row);
        });
        
        // Update charts with real-time data from active calls
        this.updateChartsFromActiveCalls(calls);
    }
    
    updateCallHistory(calls) {
        const tbody = document.getElementById('historyBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (calls.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No call history</td></tr>';
            return;
        }
        
        calls.forEach(call => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(call.start_time).toLocaleString()}</td>
                <td>${call.from_address || 'N/A'}</td>
                <td>${this.formatDurationSeconds(call.duration || 0)}</td>
                <td><span class="badge ${this.getMosClass(call.avg_mos || 0)}">${(call.avg_mos || 0).toFixed(2)}</span></td>
                <td><span class="badge ${this.getMosClass(call.min_mos || 0)}">${(call.min_mos || 0).toFixed(2)}</span></td>
                <td><span class="badge ${this.getMosClass(call.max_mos || 0)}">${(call.max_mos || 0).toFixed(2)}</span></td>
                <td>${(call.packet_loss_rate || 0).toFixed(2)}%</td>
                <td>${(call.avg_jitter || 0).toFixed(2)}ms</td>
                <td><span class="badge ${this.getQualityClass(this.getQualityCategory(call.avg_mos || 0))}">${this.getQualityCategory(call.avg_mos || 0)}</span></td>
            `;
            tbody.appendChild(row);
        });
    }
    
    updateSummaryStats(data) {
        // Update summary cards with real-time data
        const elements = {
            'calls-today': data.today_calls || 0,  // Correct ID for "Total Calls Today"
            'active-calls': data.active_calls || 0,
            'avg-mos': (data.current_avg_mos || data.last_24h?.avg_mos || 0).toFixed(2),
            'avg-packet-loss': (data.current_avg_packet_loss || data.last_24h?.avg_packet_loss || 0).toFixed(2) + '%'
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                console.log(`Updated ${id} to ${value}`);
            }
        });
        
        // Update MOS badge color
        const mosElement = document.getElementById('avgMos');
        if (mosElement) {
            const mosValue = parseFloat(mosElement.textContent);
            mosElement.className = `h4 mb-0 badge ${this.getMosClass(mosValue)}`;
        }
        
        // Update charts with real-time data
        if (data.current_avg_mos > 0) {
            this.updateCharts({
                mos_score: data.current_avg_mos,
                packet_loss_rate: data.current_avg_packet_loss,
                jitter: data.current_avg_jitter || 0
            });
        }
    }
    
    updateGatewayStatus(data) {
        const statusElement = document.getElementById('gateway-status');
        const cardElement = document.getElementById('gateway-status-card');
        
        if (statusElement && cardElement) {
            // Check if there are active calls to determine connection status
            const activeCalls = document.getElementById('activeCallsBody');
            const hasActiveCalls = activeCalls && activeCalls.children.length > 0 && 
                                 !activeCalls.innerHTML.includes('No active calls');
            
            if (data.gateway_connected || hasActiveCalls) {
                const extensions = data.registered_extensions || 0;
                statusElement.textContent = hasActiveCalls ? 
                    `Connesso (chiamata attiva)` : 
                    `Connesso (${extensions} int.)`;
                cardElement.className = 'card bg-success text-white';
            } else {
                statusElement.textContent = 'Disconnesso';
                cardElement.className = 'card bg-danger text-white';
            }
        }
    }
    
    updateRegisteredDevices(devices) {
        const tbody = document.getElementById('devicesTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (devices.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted">
                        Gateway non connesso
                    </td>
                </tr>
            `;
            return;
        }
        
        devices.forEach(device => {
            const row = document.createElement('tr');
            const isExpired = new Date(device.expires) < new Date();
            
            row.innerHTML = `
                <td><strong>${device.extension}</strong></td>
                <td><code style="font-size: 0.8em;">${device.contact.replace('sip:', '').split('@')[0]}</code></td>
                <td><span class="badge ${device.transport === 'TCP' ? 'bg-primary' : 'bg-info'}">${device.transport}</span></td>
                <td><span class="badge ${isExpired ? 'bg-danger' : 'bg-success'}">${isExpired ? 'Scaduto' : 'Attivo'}</span></td>
            `;
            tbody.appendChild(row);
        });
    }
    
    addSipMessage(data) {
        const sipMessages = document.getElementById('sipMessages');
        if (!sipMessages) return;
        
        console.log('Received SIP message:', data); // Debug log
        
        // Clear the "waiting" message if it exists
        if (sipMessages.innerHTML.includes('In attesa di messaggi SIP')) {
            sipMessages.innerHTML = '';
        }
        
        const timestamp = data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        const direction = data.direction === 'incoming' ? '⬇️' : '⬆️';
        const color = data.direction === 'incoming' ? 'text-primary' : 'text-success';
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-2 ${color}`;
        messageDiv.innerHTML = `
            <div class="fw-bold d-flex justify-content-between">
                <span>
                    <span class="badge bg-secondary">${timestamp}</span>
                    ${direction} ${data.direction.toUpperCase()} 
                </span>
                <small class="text-muted">${data.remote_addr || 'unknown'} (${data.transport || 'UDP'})</small>
            </div>
            <pre class="mt-1 mb-0" style="font-size: 11px; white-space: pre-wrap; background: rgba(0,0,0,0.05); padding: 8px; border-radius: 4px;">${data.message}</pre>
        `;
        
        sipMessages.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        const container = document.getElementById('sipMessagesContainer');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
        
        // Keep only last 50 messages
        while (sipMessages.children.length > 50) {
            sipMessages.removeChild(sipMessages.firstChild);
        }
    }
    
    // Utility functions
    formatDuration(startTime) {
        if (!startTime) return '0s';
        const now = new Date();
        const start = new Date(startTime);
        const duration = Math.floor((now - start) / 1000);
        return this.formatDurationSeconds(duration);
    }
    
    formatDurationSeconds(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    }
    
    truncateString(str, maxLength) {
        if (!str) return 'N/A';
        return str.length <= maxLength ? str : str.substring(0, maxLength) + '...';
    }
    
    getMosClass(mos) {
        if (mos >= 4.0) return 'bg-success';
        if (mos >= 3.5) return 'bg-warning';
        if (mos >= 2.5) return 'bg-danger';
        return 'bg-secondary';
    }
    
    getQualityCategory(mos) {
        if (mos >= 4.0) return 'Excellent';
        if (mos >= 3.5) return 'Good';
        if (mos >= 2.5) return 'Fair';
        if (mos >= 1.0) return 'Poor';
        return 'No Data';
    }
    
    getQualityClass(quality) {
        const classes = {
            'Excellent': 'bg-success',
            'Good': 'bg-info',
            'Fair': 'bg-warning',
            'Poor': 'bg-danger',
            'No Data': 'bg-secondary'
        };
        return classes[quality] || 'bg-secondary';
    }
    
    showStatus(message, type = 'info') {
        console.log(`Status (${type}): ${message}`);
        // Could add toast notifications here if needed
    }
    
    addSipMessage(data) {
        const sipContainer = document.getElementById('sipMessages');
        const isFirstMessage = sipContainer.querySelector('.text-muted');
        
        if (isFirstMessage) {
            sipContainer.innerHTML = '';
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'sip-message mb-2 p-2 border-start border-3';
        
        // Color coding based on message type
        let borderColor = 'border-secondary';
        if (data.direction === 'incoming') {
            borderColor = 'border-success';
        } else if (data.direction === 'outgoing') {
            borderColor = 'border-primary';
        }
        
        messageDiv.className += ` ${borderColor}`;
        
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        const direction = data.direction === 'incoming' ? '←' : '→';
        const transport = data.transport || 'UDP';
        
        messageDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-1">
                <small class="text-muted">
                    <strong>${timestamp}</strong> 
                    <span class="badge bg-secondary">${transport}</span>
                    <span class="badge ${data.direction === 'incoming' ? 'bg-success' : 'bg-primary'}">${direction} ${data.direction.toUpperCase()}</span>
                    <span class="text-muted">${data.remote_addr || ''}</span>
                </small>
            </div>
            <pre class="mb-0" style="font-size: 11px; white-space: pre-wrap;">${data.message}</pre>
        `;
        
        sipContainer.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        const container = document.getElementById('sipMessagesContainer');
        container.scrollTop = container.scrollHeight;
        
        // Keep only last 100 messages
        const messages = sipContainer.children;
        if (messages.length > 100) {
            sipContainer.removeChild(messages[0]);
        }
    }
    
    updateChartsFromActiveCalls(calls) {
        if (!calls || calls.length === 0) {
            // Clear charts when no active calls
            this.clearCharts();
            return;
        }
        
        // Check if this is a new call (different call_id from last update)
        const currentCallIds = calls.map(call => call.call_id).join(',');
        if (this.lastCallIds && this.lastCallIds !== currentCallIds) {
            console.log('New call detected, clearing charts');
            this.clearCharts();
        }
        this.lastCallIds = currentCallIds;
        
        // Calculate average metrics from active calls
        let totalMos = 0;
        let totalPacketLoss = 0;
        let totalJitter = 0;
        let validCalls = 0;
        
        calls.forEach(call => {
            if (call.current_mos && call.current_mos > 0) {
                totalMos += call.current_mos;
                totalPacketLoss += call.packet_loss_rate || 0;
                totalJitter += call.jitter || 0;
                validCalls++;
            }
        });
        
        if (validCalls > 0) {
            const avgMos = totalMos / validCalls;
            const avgPacketLoss = totalPacketLoss / validCalls;
            const avgJitter = totalJitter / validCalls;
            const currentTime = new Date().toLocaleTimeString();
            
            this.updateCharts(currentTime, avgMos, avgPacketLoss, avgJitter);
        }
    }
    
    updateCharts(time, mosScore, packetLoss, jitter) {
        // Update MOS Chart
        if (this.mosChart) {
            const mosData = this.mosChart.data;
            mosData.labels.push(time);
            mosData.datasets[0].data.push(mosScore);
            
            // Keep only last 20 data points
            if (mosData.labels.length > 20) {
                mosData.labels.shift();
                mosData.datasets[0].data.shift();
            }
            
            this.mosChart.update('none');
        }
        
        // Update Network Quality Chart
        if (this.networkChart) {
            const networkData = this.networkChart.data;
            networkData.labels.push(time);
            networkData.datasets[0].data.push(packetLoss); // Packet Loss
            networkData.datasets[1].data.push(jitter);     // Jitter
            
            // Keep only last 20 data points
            if (networkData.labels.length > 20) {
                networkData.labels.shift();
                networkData.datasets[0].data.shift();
                networkData.datasets[1].data.shift();
            }
            
            this.networkChart.update('none');
        }
    }
    
    clearCharts() {
        // Clear MOS Chart
        if (this.mosChart) {
            this.mosChart.data.labels = [];
            this.mosChart.data.datasets[0].data = [];
            this.mosChart.update('none');
        }
        
        // Clear Network Quality Chart
        if (this.networkChart) {
            this.networkChart.data.labels = [];
            this.networkChart.data.datasets[0].data = [];
            this.networkChart.data.datasets[1].data = [];
            this.networkChart.update('none');
        }
    }
    
    refreshCallHistory() {
        this.loadCallHistory();
    }
    
    refreshSummaryStats() {
        this.loadSummaryStats();
    }
}

// Initialize dashboard when DOM is loaded (single instance)
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new Dashboard();
});

// Clear SIP log function
function clearSipLog() {
    const sipContainer = document.getElementById('sipMessages');
    sipContainer.innerHTML = '<div class="text-muted text-center">Log pulito - in attesa di nuovi messaggi SIP...</div>';
}

// Refresh function for manual refresh button
function refreshHistory() {
    if (window.dashboard) {
        window.dashboard.refreshCallHistory();
    }
}