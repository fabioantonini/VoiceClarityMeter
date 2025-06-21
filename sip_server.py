import socket
import threading
import re
from datetime import datetime
from rtp_processor import RTPProcessor

class SIPServer:
    def __init__(self, call_manager, socketio):
        self.call_manager = call_manager
        self.socketio = socketio
        self.host = '0.0.0.0'
        self.port = 5060
        self.socket = None
        self.running = False
        self.active_sessions = {}
        
    def start(self):
        """Start the SIP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.running = True
            
            print(f"SIP Server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(4096)
                    threading.Thread(
                        target=self.handle_request,
                        args=(data, addr),
                        daemon=True
                    ).start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error receiving SIP data: {e}")
                    
        except Exception as e:
            print(f"Error starting SIP server: {e}")
            
    def stop(self):
        """Stop the SIP server"""
        self.running = False
        if self.socket:
            self.socket.close()
            
    def handle_request(self, data, addr):
        """Handle incoming SIP request"""
        try:
            message = data.decode('utf-8')
            print(f"Received SIP message from {addr}:\n{message}")
            
            # Parse SIP message
            lines = message.split('\r\n')
            if not lines:
                return
                
            request_line = lines[0]
            headers = self.parse_headers(lines[1:])
            
            # Handle different SIP methods
            if request_line.startswith('INVITE'):
                self.handle_invite(request_line, headers, addr)
            elif request_line.startswith('ACK'):
                self.handle_ack(request_line, headers, addr)
            elif request_line.startswith('BYE'):
                self.handle_bye(request_line, headers, addr)
            elif request_line.startswith('REGISTER'):
                self.handle_register(request_line, headers, addr)
                
        except Exception as e:
            print(f"Error handling SIP request: {e}")
            
    def parse_headers(self, header_lines):
        """Parse SIP headers"""
        headers = {}
        for line in header_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        return headers
        
    def handle_invite(self, request_line, headers, addr):
        """Handle SIP INVITE request"""
        call_id = headers.get('call-id', f"call_{datetime.now().timestamp()}")
        from_header = headers.get('from', '')
        to_header = headers.get('to', '')
        
        # Extract SDP information
        sdp_info = self.parse_sdp(headers)
        
        # Create call session
        session = {
            'call_id': call_id,
            'from': from_header,
            'to': to_header,
            'addr': addr,
            'status': 'ringing',
            'start_time': datetime.now().isoformat(),
            'sdp': sdp_info
        }
        
        self.active_sessions[call_id] = session
        
        # Send 180 Ringing
        self.send_response(addr, '180', 'Ringing', headers)
        
        # Send 200 OK with SDP
        self.send_ok_with_sdp(addr, headers, call_id)
        
        # Start RTP processing
        if sdp_info and 'audio_port' in sdp_info:
            self.start_rtp_processing(call_id, sdp_info['audio_port'], addr[0])
            
    def handle_ack(self, request_line, headers, addr):
        """Handle SIP ACK request"""
        call_id = headers.get('call-id')
        if call_id in self.active_sessions:
            self.active_sessions[call_id]['status'] = 'active'
            
            # Register call with call manager
            self.call_manager.start_call(call_id, self.active_sessions[call_id])
            
            # Notify frontend
            self.socketio.emit('call_started', {
                'call_id': call_id,
                'session': self.active_sessions[call_id]
            })
            
    def handle_bye(self, request_line, headers, addr):
        """Handle SIP BYE request"""
        call_id = headers.get('call-id')
        if call_id in self.active_sessions:
            # Send 200 OK
            self.send_response(addr, '200', 'OK', headers)
            
            # End call
            self.call_manager.end_call(call_id)
            
            # Clean up session
            del self.active_sessions[call_id]
            
            # Notify frontend
            self.socketio.emit('call_ended', {'call_id': call_id})
            
    def handle_register(self, request_line, headers, addr):
        """Handle SIP REGISTER request"""
        # Send 200 OK for registration
        self.send_response(addr, '200', 'OK', headers)
        
    def send_response(self, addr, code, reason, request_headers):
        """Send SIP response"""
        call_id = request_headers.get('call-id', 'unknown')
        from_header = request_headers.get('from', '')
        to_header = request_headers.get('to', '')
        via_header = request_headers.get('via', '')
        
        response = f"SIP/2.0 {code} {reason}\r\n"
        response += f"Via: {via_header}\r\n"
        response += f"From: {from_header}\r\n"
        response += f"To: {to_header}\r\n"
        response += f"Call-ID: {call_id}\r\n"
        response += f"Content-Length: 0\r\n\r\n"
        
        self.socket.sendto(response.encode('utf-8'), addr)
        
    def send_ok_with_sdp(self, addr, request_headers, call_id):
        """Send 200 OK with SDP"""
        call_id = request_headers.get('call-id', call_id)
        from_header = request_headers.get('from', '')
        to_header = request_headers.get('to', '')
        via_header = request_headers.get('via', '')
        
        # Generate SDP
        sdp = self.generate_sdp()
        
        response = f"SIP/2.0 200 OK\r\n"
        response += f"Via: {via_header}\r\n"
        response += f"From: {from_header}\r\n"
        response += f"To: {to_header}\r\n"
        response += f"Call-ID: {call_id}\r\n"
        response += f"Content-Type: application/sdp\r\n"
        response += f"Content-Length: {len(sdp)}\r\n\r\n"
        response += sdp
        
        self.socket.sendto(response.encode('utf-8'), addr)
        
    def parse_sdp(self, headers):
        """Parse SDP from headers"""
        # Simple SDP parsing - in production, this would be more robust
        sdp_info = {}
        
        # Look for audio port in common SDP patterns
        for key, value in headers.items():
            if 'audio' in value.lower() and 'port' in value.lower():
                # Extract port number
                port_match = re.search(r'(\d{4,5})', value)
                if port_match:
                    sdp_info['audio_port'] = int(port_match.group(1))
                    
        return sdp_info
        
    def generate_sdp(self):
        """Generate SDP response"""
        local_ip = self.get_local_ip()
        rtp_port = 10000  # Default RTP port for receiving
        
        sdp = f"v=0\r\n"
        sdp += f"o=- 0 0 IN IP4 {local_ip}\r\n"
        sdp += f"s=VoIP Quality Monitor\r\n"
        sdp += f"c=IN IP4 {local_ip}\r\n"
        sdp += f"t=0 0\r\n"
        sdp += f"m=audio {rtp_port} RTP/AVP 0 8\r\n"
        sdp += f"a=rtpmap:0 PCMU/8000\r\n"
        sdp += f"a=rtpmap:8 PCMA/8000\r\n"
        
        return sdp
        
    def get_local_ip(self):
        """Get local IP address"""
        try:
            # Create a dummy socket to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
            
    def start_rtp_processing(self, call_id, rtp_port, remote_ip):
        """Start RTP stream processing"""
        def process_rtp():
            rtp_processor = RTPProcessor(call_id, rtp_port, self.call_manager)
            rtp_processor.start_processing()
            
        threading.Thread(target=process_rtp, daemon=True).start()
