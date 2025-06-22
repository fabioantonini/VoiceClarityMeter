// Simplified Dashboard JavaScript for VoIP Quality Monitor

class Dashboard {
    constructor() {
        this.socket = null;
        this.initializeWebSocket();
        this.loadInitialData();
        this.setupRefreshTimer();
    }
    
    initializeWebSocket() {
        // Check if Socket.IO is available
        if (typeof io === 'undefined') {
            console.warn('Socket.IO not loaded, using polling mode');
            this.setupPolling();
            return;
        }
        
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to real-time updates');
                this.showStatus('Connected to real-time updates', 'success');
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from real-time updates');
                this.showStatus('Disconnected - using polling mode', 'warning');
                this.setupPolling();
            });
            
            this.socket.on('call_update', (data) => {
                this.updateDashboard(data);
            });
            
            this.socket.on('status', (data) => {
                this.showStatus(data.message, 'info');
            });
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.setupPolling();
        }
    }
    
    setupPolling() {
        // Fallback to HTTP polling
        setInterval(() => {
            this.loadInitialData();
        }, 5000); // Poll every 5 seconds
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
        
        if (calls.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No active calls</td></tr>';
            return;
        }
        
        calls.forEach(call => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${this.truncateString(call.call_id, 20)}</td>
                <td>${call.from_address || 'N/A'}</td>
                <td>${call.to_address || 'N/A'}</td>
                <td>${this.formatDuration(call.start_time)}</td>
                <td><span class="badge ${this.getMosClass(call.current_mos || 0)}">${(call.current_mos || 0).toFixed(2)}</span></td>
                <td>${(call.packet_loss_rate || 0).toFixed(2)}%</td>
                <td>${(call.jitter || 0).toFixed(2)}ms</td>
                <td><span class="badge ${this.getQualityClass(this.getQualityCategory(call.current_mos || 0))}">${this.getQualityCategory(call.current_mos || 0)}</span></td>
            `;
            tbody.appendChild(row);
        });
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
        // Update summary cards
        const elements = {
            'totalCalls': data.total_calls || 0,
            'activeCalls': data.active_calls || 0,
            'avgMos': (data.avg_mos || 0).toFixed(2),
            'avgPacketLoss': (data.avg_packet_loss || 0).toFixed(2)
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
        
        // Update MOS badge color
        const mosElement = document.getElementById('avgMos');
        if (mosElement) {
            const mosValue = parseFloat(mosElement.textContent);
            mosElement.className = `h4 mb-0 badge ${this.getMosClass(mosValue)}`;
        }
    }
    
    updateGatewayStatus(data) {
        const statusElement = document.getElementById('gateway-status');
        const cardElement = document.getElementById('gateway-status-card');
        
        if (statusElement && cardElement) {
            if (data.gateway_connected) {
                statusElement.textContent = `Connesso (${data.registered_extensions} int.)`;
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
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new Dashboard();
});

// Refresh function for manual refresh button
function refreshHistory() {
    if (window.dashboard) {
        window.dashboard.refreshCallHistory();
    }
}

// Store dashboard instance globally for debugging
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new Dashboard();
});