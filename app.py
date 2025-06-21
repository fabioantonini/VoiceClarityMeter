import os

from flask import Flask, render_template, jsonify, request, session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import threading
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "voip-quality-app-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize database
db = SQLAlchemy(app, model_class=Base)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Create tables
with app.app_context():
    import models  # noqa: F401
    db.create_all()
    logging.info("Database tables created")

# Import auth after app and db are initialized
from replit_auth import init_login_manager, make_replit_blueprint, require_login
from flask_login import current_user

# Initialize authentication
storage_class = init_login_manager(app, db)

# Register auth blueprint
app.register_blueprint(make_replit_blueprint(storage_class), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Import after db initialization
from sip_server import SIPServer
from call_manager import CallManager
from config_helper import ConfigHelper

# Global instances
call_manager = CallManager()
config_helper = ConfigHelper()
sip_server = None

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Real-time monitoring dashboard"""
    return render_template('dashboard.html')

@app.route('/config')
def config():
    """SIP client configuration helper"""
    return render_template('config.html')

@app.route('/api/calls/active')
def get_active_calls():
    """Get currently active calls"""
    return jsonify(call_manager.get_active_calls())

@app.route('/api/calls/history')
def get_call_history():
    """Get historical call data"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(call_manager.get_call_history(limit))

@app.route('/api/stats/summary')
def get_summary_stats():
    """Get summary statistics"""
    return jsonify(call_manager.get_summary_stats())

@app.route('/api/config/generate', methods=['POST'])
def generate_config():
    """Generate SIP client configuration"""
    data = request.json
    client_type = data.get('client_type', 'generic')
    server_ip = data.get('server_ip', '127.0.0.1')
    server_port = data.get('server_port', 5060)
    
    config = config_helper.generate_config(client_type, server_ip, server_port)
    return jsonify(config)

@app.route('/api/test/connectivity', methods=['POST'])
def test_connectivity():
    """Test network connectivity"""
    data = request.json
    target_ip = data.get('ip', '127.0.0.1')
    target_port = data.get('port', 5060)
    
    result = config_helper.test_connectivity(target_ip, target_port)
    return jsonify(result)

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to VoIP Quality Monitor'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f"Client disconnected: {request.sid}")

def start_sip_server():
    """Start the SIP server in a separate thread"""
    global sip_server
    sip_server = SIPServer(call_manager, socketio)
    sip_server.start()

def broadcast_call_updates():
    """Broadcast call updates to all connected clients"""
    def update_loop():
        import time
        while True:
            if call_manager.has_updates():
                active_calls = call_manager.get_active_calls()
                socketio.emit('call_update', active_calls)
                
                # Send quality metrics for active calls
                for call in active_calls:
                    if call.get('quality_metrics'):
                        socketio.emit('quality_update', {
                            'call_id': call['call_id'],
                            'metrics': call['quality_metrics']
                        })
            time.sleep(1)
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Initialize empty calls file if it doesn't exist
    calls_file = 'data/calls.json'
    if not os.path.exists(calls_file):
        with open(calls_file, 'w') as f:
            json.dump([], f)
    
    # Start SIP server
    sip_thread = threading.Thread(target=start_sip_server, daemon=True)
    sip_thread.start()
    
    # Start call updates broadcaster
    broadcast_call_updates()
    
    print("VoIP Quality Monitor starting...")
    print("Dashboard available at: http://0.0.0.0:5000/dashboard")
    print("Configuration helper at: http://0.0.0.0:5000/config")
    
    # Run Flask-SocketIO app
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
