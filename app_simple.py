"""
VoIP Quality Monitor - Simplified Version
A real-time VoIP call quality monitoring system
"""
import os
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime, timedelta
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from functools import wraps

# Import our VoIP components
from call_manager import CallManager
from config_helper import ConfigHelper
from sip_registrar import SIPRegistrar
from mos_calculator import MOSCalculator

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "voip-quality-app-secret-key"

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Simple authentication setup
login_manager = LoginManager()
login_manager.init_app(app)

class SimpleUser(UserMixin):
    def __init__(self, user_id, email=None, first_name=None):
        self.id = user_id
        self.email = email
        self.first_name = first_name

@login_manager.user_loader  
def load_user(user_id):
    return SimpleUser(user_id, 'admin@voip-monitor.com', 'Admin')

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required', 'redirect': '/auth/demo-login'}), 401
            return redirect(url_for('demo_login'))
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/auth/demo-login')
def demo_login():
    demo_user = SimpleUser('demo_admin', 'admin@voip-monitor.com', 'Admin')
    login_user(demo_user)
    return redirect(url_for('dashboard'))

@app.route('/auth/logout')
def auth_logout():
    logout_user()
    return redirect(url_for('index'))

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Initialize core components
call_manager = CallManager()
config_helper = ConfigHelper()
sip_server = None

# Routes
@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html', user=current_user)

@app.route('/dashboard')
@require_login
def dashboard():
    """Real-time monitoring dashboard"""
    return render_template('dashboard.html', user=current_user)

@app.route('/config')
@require_login
def config():
    """SIP client configuration helper"""
    return render_template('config.html', user=current_user)

# API Routes
@app.route('/api/calls/active')
@require_login
def get_active_calls():
    """Get currently active calls"""
    active_calls = call_manager.get_active_calls()
    return jsonify(active_calls)

@app.route('/api/calls/history')
@require_login
def get_call_history():
    """Get historical call data"""
    limit = request.args.get('limit', 100, type=int)
    history = call_manager.get_call_history(limit)
    return jsonify(history)

@app.route('/api/stats/summary')
@require_login
def get_summary_stats():
    """Get summary statistics"""
    stats = call_manager.get_summary_stats()
    return jsonify(stats)

@app.route('/api/config/generate', methods=['POST'])
@require_login
def generate_config():
    """Generate SIP client configuration"""
    data = request.json or {}
    client_type = data.get('client_type', 'generic')
    server_ip = data.get('server_ip', '127.0.0.1')
    server_port = data.get('server_port', 5060)
    
    config = config_helper.generate_config(client_type, server_ip, server_port)
    return jsonify(config)

@app.route('/api/test/connectivity', methods=['POST'])
@require_login
def test_connectivity():
    """Test network connectivity"""
    data = request.json or {}
    target_ip = data.get('ip', '127.0.0.1')
    target_port = data.get('port', 5060)
    
    result = config_helper.test_connectivity(target_ip, target_port)
    return jsonify(result)

@app.route('/api/devices/registered')
@require_login
def get_registered_devices():
    """Get list of registered FXS devices from Asterisk gateway"""
    if sip_server:
        devices = sip_server.get_registered_devices()
        return jsonify(devices)
    return jsonify([])

@app.route('/api/gateway/status')
@require_login
def get_gateway_status():
    """Get gateway connection status"""
    if sip_server:
        devices = sip_server.get_registered_devices()
        gateway_connected = len(devices) > 0
        
        status = {
            'gateway_connected': gateway_connected,
            'registered_extensions': len(devices),
            'extensions': [device['extension'] for device in devices],
            'last_activity': devices[0]['last_seen'] if devices else None
        }
        return jsonify(status)
    
    return jsonify({
        'gateway_connected': False,
        'registered_extensions': 0,
        'extensions': [],
        'last_activity': None
    })

# WebSocket handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print("Client connected to WebSocket")
    emit('status', {'message': 'Connected to VoIP Quality Monitor'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print("Client disconnected from WebSocket")

# Background services
def start_sip_server():
    """Start the SIP Registrar for Asterisk gateway"""
    global sip_server
    try:
        sip_server = SIPRegistrar(call_manager, socketio)
        sip_server.start()
        print("SIP Registrar started successfully - ready for Asterisk gateway connections")
    except Exception as e:
        print(f"Failed to start SIP Registrar: {e}")

def broadcast_call_updates():
    """Broadcast call updates to all connected clients"""
    def update_loop():
        while True:
            try:
                if call_manager.has_updates():
                    # Get current data
                    active_calls = call_manager.get_active_calls()
                    summary_stats = call_manager.get_summary_stats()
                    
                    # Broadcast to all connected clients
                    socketio.emit('call_update', {
                        'active_calls': active_calls,
                        'summary_stats': summary_stats,
                        'timestamp': datetime.now().isoformat()
                    })
                
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"Error in broadcast loop: {e}")
                time.sleep(5)
    
    # Start the update thread
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()
    print("Started call update broadcast service")

if __name__ == '__main__':
    print("=" * 50)
    print("VoIP Quality Monitor - Starting Up")
    print("=" * 50)
    
    # Start background services
    sip_thread = threading.Thread(target=start_sip_server, daemon=True)
    sip_thread.start()
    
    # Start broadcast service
    broadcast_call_updates()
    
    print("Dashboard available at: http://0.0.0.0:5000/")
    print("Configuration helper at: http://0.0.0.0:5000/config")
    print("SIP server listening on UDP port 5060")
    
    # Run Flask-SocketIO app
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, log_output=True)