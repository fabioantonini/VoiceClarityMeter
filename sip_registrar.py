"""
SIP Registrar and Proxy for VoIP Gateway with FXS interfaces
Handles registration and call routing for Asterisk-based gateways
"""
import socket
import ssl
import threading
import re
import select
import time
import os
from datetime import datetime, timedelta
from rtp_processor import RTPProcessor

class SIPRegistrar:
    def __init__(self, call_manager, socketio):
        self.call_manager = call_manager
        self.socketio = socketio
        self.host = '0.0.0.0'
        self.udp_port = 5060
        self.tcp_port = 5060
        self.tls_port = 5061
        self.udp_socket = None
        self.tcp_socket = None
        self.tls_socket = None
        self.running = False
        self.ssl_context = None
        
        # Registry for connected devices
        self.registered_devices = {}  # {extension: {contact, expires, last_seen, transport}}
        self.active_calls = {}
        self.tcp_connections = {}
        self.tls_connections = {}  # Track TLS connections
        
        # Configuration for FXS gateway and Welcome Italia compatibility
        self.domain = "voip-monitor.local"
        self.registration_expires = 3600  # 1 hour (compatible with Welcome Italia)
        self.supported_codecs = ['G.711', 'G.729', 'G.722', 'OPUS']
        self.dtmf_support = 'rfc4733'  # Welcome Italia standard
        
        # Default SIP authentication credentials for gateway registration
        self.sip_users = {
            'gateway-monitor': 'VoipQuality2025!',
            'gateway-test': 'TestMonitor123',
            'welcome-gw': 'WelcomeGW456'
        }
        
        # Test extensions for quality monitoring (now with REAL RTP analysis)
        self.test_extensions = {
            '999': {'name': 'Test Audio Qualità', 'description': 'Analisi RTP reale per test qualità'},
            '998': {'name': 'Test con Rumore', 'description': 'Analisi RTP reale con monitoraggio rumore'},
            '997': {'name': 'Test Echo/Delay', 'description': 'Analisi RTP reale per delay e echo'},
            '996': {'name': 'Test Packet Loss', 'description': 'Analisi RTP reale per packet loss'}
        }
        
    def start(self):
        """Start SIP Registrar and Proxy services"""
        try:
            self.start_udp_server()
            self.start_tcp_server()
            self.start_tls_server()
            
            print(f"SIP Registrar listening on UDP {self.host}:{self.udp_port}")
            print(f"SIP Registrar listening on TCP {self.host}:{self.tcp_port}")
            if self.tls_socket:
                print(f"SIP Registrar listening on TLS {self.host}:{self.tls_port}")
            else:
                print(f"TLS not available - certificates not found")
            
            self.running = True
            
            # Start registration cleanup thread
            cleanup_thread = threading.Thread(target=self.cleanup_expired_registrations, daemon=True)
            cleanup_thread.start()
            
            # Main server loop
            self.server_loop()
            
        except Exception as e:
            print(f"Error starting SIP Registrar: {e}")
            
    def start_udp_server(self):
        """Initialize UDP socket"""
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind((self.host, self.udp_port))
        self.udp_socket.setblocking(False)
        
    def start_tcp_server(self):
        """Initialize TCP socket"""
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(5)
        self.tcp_socket.setblocking(False)

    def start_tls_server(self):
        """Initialize TLS socket with SSL context"""
        try:
            # Check if certificates exist
            cert_dir = "certificates"
            cert_file = os.path.join(cert_dir, "sip-server.local-cert.pem")
            key_file = os.path.join(cert_dir, "sip-server.local-private-key.pem")
            
            if not os.path.exists(cert_file) or not os.path.exists(key_file):
                print("TLS certificates not found - TLS server not started")
                print("Generate certificates at /certificates to enable TLS")
                return
                
            # Create SSL context
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(cert_file, key_file)
            
            # Create TLS socket
            self.tls_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tls_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tls_socket.bind((self.host, self.tls_port))
            self.tls_socket.listen(5)
            self.tls_socket.setblocking(False)
            
        except Exception as e:
            print(f"Error starting TLS server: {e}")
            self.tls_socket = None
            self.ssl_context = None
        
    def server_loop(self):
        """Main server loop handling UDP, TCP and TLS"""
        while self.running:
            try:
                read_sockets = [self.udp_socket, self.tcp_socket]
                if self.tls_socket:
                    read_sockets.append(self.tls_socket)
                read_sockets.extend(self.tcp_connections.keys())
                read_sockets.extend(self.tls_connections.keys())
                
                ready_sockets, _, error_sockets = select.select(read_sockets, [], read_sockets, 1.0)
                
                for sock in ready_sockets:
                    if sock == self.udp_socket:
                        self.handle_udp_data()
                    elif sock == self.tcp_socket:
                        self.handle_new_tcp_connection()
                    elif sock == self.tls_socket:
                        self.handle_new_tls_connection()
                    elif sock in self.tcp_connections:
                        self.handle_tcp_data(sock)
                    elif sock in self.tls_connections:
                        self.handle_tls_data(sock)
                        
                for sock in error_sockets:
                    if sock in self.tcp_connections:
                        self.close_tcp_connection(sock)
                    elif sock in self.tls_connections:
                        self.close_tls_connection(sock)
                        
            except Exception as e:
                print(f"Error in registrar loop: {e}")
                
    def handle_udp_data(self):
        """Handle incoming UDP data"""
        try:
            data, addr = self.udp_socket.recvfrom(4096)
            threading.Thread(
                target=self.handle_sip_message,
                args=(data, addr, 'UDP'),
                daemon=True
            ).start()
        except socket.error:
            pass
            
    def handle_new_tcp_connection(self):
        """Handle new TCP connection"""
        try:
            client_socket, addr = self.tcp_socket.accept()
            client_socket.setblocking(False)
            self.tcp_connections[client_socket] = {
                'addr': addr,
                'buffer': b'',
                'transport': 'TCP'
            }
            print(f"New TCP connection from gateway at {addr}")
        except socket.error:
            pass

    def handle_new_tls_connection(self):
        """Handle new TLS connection"""
        try:
            client_socket, addr = self.tls_socket.accept()
            # Wrap socket with SSL
            ssl_socket = self.ssl_context.wrap_socket(client_socket, server_side=True)
            ssl_socket.setblocking(False)
            self.tls_connections[ssl_socket] = {
                'addr': addr,
                'buffer': b'',
                'transport': 'TLS'
            }
            print(f"New TLS connection from {addr}")
        except Exception as e:
            print(f"Error accepting TLS connection: {e}")
            
    def handle_tcp_data(self, client_socket):
        """Handle data from TCP connection"""
        try:
            data = client_socket.recv(4096)
            if not data:
                self.close_tcp_connection(client_socket)
                return
                
            conn_info = self.tcp_connections[client_socket]
            conn_info['buffer'] += data
            
            self.process_tcp_buffer(client_socket)
            
        except socket.error:
            self.close_tcp_connection(client_socket)
            
    def process_tcp_buffer(self, client_socket):
        """Process buffered TCP data for complete SIP messages"""
        conn_info = self.tcp_connections[client_socket]
        buffer = conn_info['buffer']
        
        while b'\r\n\r\n' in buffer:
            header_end = buffer.find(b'\r\n\r\n') + 4
            headers_data = buffer[:header_end]
            content_length = self.extract_content_length(headers_data)
            total_length = header_end + content_length
            
            if len(buffer) >= total_length:
                message = buffer[:total_length]
                buffer = buffer[total_length:]
                
                threading.Thread(
                    target=self.handle_sip_message,
                    args=(message, conn_info['addr'], 'TCP', client_socket),
                    daemon=True
                ).start()
            else:
                break
                
        conn_info['buffer'] = buffer
        
    def extract_content_length(self, headers_data):
        """Extract Content-Length from SIP headers"""
        try:
            headers_str = headers_data.decode('utf-8', errors='ignore')
            match = re.search(r'Content-Length:\s*(\d+)', headers_str, re.IGNORECASE)
            return int(match.group(1)) if match else 0
        except:
            return 0
            
    def close_tcp_connection(self, client_socket):
        """Close TCP connection"""
        try:
            addr = self.tcp_connections[client_socket]['addr']
            print(f"Closing TCP connection from {addr}")
            client_socket.close()
            del self.tcp_connections[client_socket]
        except:
            pass

    def handle_tls_data(self, client_socket):
        """Handle data from TLS connection"""
        try:
            data = client_socket.recv(4096)
            if not data:
                self.close_tls_connection(client_socket)
                return
                
            conn_info = self.tls_connections[client_socket]
            conn_info['buffer'] += data
            
            # Process complete SIP messages
            self.process_tls_buffer(client_socket)
            
        except ssl.SSLWantReadError:
            # SSL handshake in progress, continue
            pass
        except Exception as e:
            print(f"Error handling TLS data: {e}")
            self.close_tls_connection(client_socket)

    def process_tls_buffer(self, client_socket):
        """Process buffered TLS data for complete SIP messages"""
        conn_info = self.tls_connections[client_socket]
        buffer = conn_info['buffer']
        
        while b'\r\n\r\n' in buffer:
            # Find end of headers
            headers_end = buffer.find(b'\r\n\r\n') + 4
            headers_data = buffer[:headers_end]
            
            # Check for Content-Length
            content_length = self.extract_content_length(headers_data)
            total_length = headers_end + content_length
            
            if len(buffer) >= total_length:
                # Complete SIP message
                message = buffer[:total_length]
                buffer = buffer[total_length:]
                
                threading.Thread(
                    target=self.handle_sip_message,
                    args=(message, conn_info['addr'], 'TLS', client_socket),
                    daemon=True
                ).start()
            else:
                break
                
        conn_info['buffer'] = buffer

    def close_tls_connection(self, client_socket):
        """Close TLS connection"""
        try:
            addr = self.tls_connections[client_socket]['addr']
            print(f"Closing TLS connection from {addr}")
            client_socket.close()
            del self.tls_connections[client_socket]
        except:
            pass
            
    def handle_sip_message(self, data, addr, transport='UDP', client_socket=None):
        """Handle incoming SIP message from gateway or phones"""
        try:
            message = data.decode('utf-8', errors='ignore')
            lines = message.split('\r\n')
            
            if not lines:
                return
                
            request_line = lines[0]
            headers = self.parse_headers(lines[1:])
            
            print(f"Received SIP {transport} from {addr}: {request_line}")
            
            # Broadcast SIP message to dashboard
            self.broadcast_sip_message(message, addr, transport, 'incoming')
            
            # Route based on SIP method
            if request_line.startswith('REGISTER'):
                self.handle_register(request_line, headers, addr, transport, client_socket)
            elif request_line.startswith('INVITE'):
                self.handle_invite(request_line, headers, addr, transport, client_socket)
            elif request_line.startswith('ACK'):
                self.handle_ack(request_line, headers, addr, transport, client_socket)
            elif request_line.startswith('BYE'):
                self.handle_bye(request_line, headers, addr, transport, client_socket)
            elif request_line.startswith('OPTIONS'):
                self.handle_options(request_line, headers, addr, transport, client_socket)
            elif request_line.startswith('CANCEL'):
                self.handle_cancel(request_line, headers, addr, transport, client_socket)
            else:
                print(f"Unhandled SIP method: {request_line}")
                
        except Exception as e:
            print(f"Error handling SIP {transport} message: {e}")
            
    def parse_headers(self, header_lines):
        """Parse SIP headers"""
        headers = {}
        for line in header_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        return headers
        
    def handle_register(self, request_line, headers, addr, transport, client_socket=None):
        """Handle REGISTER requests from gateway/phones with authentication"""
        try:
            # Extract registration info
            contact = headers.get('contact', '')
            expires = int(headers.get('expires', self.registration_expires))
            from_header = headers.get('from', '')
            to_header = headers.get('to', '')
            authorization = headers.get('authorization', '')
            
            # Extract extension/user
            extension = self.extract_extension(from_header)
            contact_uri = self.extract_contact_uri(contact)
            
            print(f"DEBUG REGISTER: extension={extension}, from_header={from_header}")
            
            # Check for authentication
            if authorization:
                print(f"DEBUG: Authorization header present: {authorization[:50]}...")
                # Parse authorization header
                auth_valid = self.verify_sip_auth(authorization, extension)
                print(f"DEBUG: Auth result for {extension}: {auth_valid}")
                if not auth_valid:
                    print(f"DEBUG: Sending 403 Forbidden for {extension}")
                    self.send_response(addr, '403', 'Forbidden', headers, transport, client_socket)
                    return
            else:
                # Send authentication challenge
                self.send_auth_challenge(addr, headers, transport, client_socket)
                return
            
            if extension:
                if expires > 0:
                    # Register the device
                    self.registered_devices[extension] = {
                        'contact': contact_uri,
                        'expires': datetime.now() + timedelta(seconds=expires),
                        'last_seen': datetime.now(),
                        'transport': transport,
                        'addr': addr,
                        'gateway_info': {
                            'from_header': from_header,
                            'to_header': to_header
                        }
                    }
                    print(f"Registered extension {extension} from {addr} via {transport}")
                    print(f"Contact: {contact_uri}")
                    
                    # Notify dashboard of new registration
                    self.socketio.emit('device_registered', {
                        'extension': extension,
                        'contact': contact_uri,
                        'transport': transport,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    # Unregister the device
                    if extension in self.registered_devices:
                        del self.registered_devices[extension]
                        print(f"Unregistered extension {extension}")
                        
                        self.socketio.emit('device_unregistered', {
                            'extension': extension,
                            'timestamp': datetime.now().isoformat()
                        })
                
                # Send 200 OK response
                self.send_response(addr, '200', 'OK', headers, transport, client_socket)
            else:
                # Send 400 Bad Request
                self.send_response(addr, '400', 'Bad Request', headers, transport, client_socket)
                
        except Exception as e:
            print(f"Error handling REGISTER: {e}")
            self.send_response(addr, '500', 'Internal Server Error', headers, transport, client_socket)
            
    def handle_invite(self, request_line, headers, addr, transport, client_socket=None):
        """Handle INVITE requests for call setup"""
        try:
            call_id = headers.get('call-id', f"call_{datetime.now().timestamp()}")
            from_header = headers.get('from', '')
            to_header = headers.get('to', '')
            
            from_ext = self.extract_extension(from_header)
            to_ext = self.extract_extension(to_header)
            
            print(f"Call setup: {from_ext} -> {to_ext} (Call-ID: {call_id})")
            
            # Track call for quality monitoring
            session_info = {
                'from_address': from_ext or self.extract_address(from_header),
                'to_address': to_ext or self.extract_address(to_header),
                'transport': transport,
                'remote_addr': addr,
                'call_type': 'FXS_Gateway'
            }
            
            self.call_manager.start_call(call_id, session_info)
            
            # Check if destination is a test extension
            if to_ext and to_ext in self.test_extensions:
                # Handle test extension call
                self.handle_test_extension_call(to_ext, call_id, headers, addr, transport, client_socket)
            elif to_ext and to_ext in self.registered_devices:
                # Forward INVITE to registered device
                self.forward_invite(request_line, headers, to_ext, transport, client_socket)
            else:
                # Redirect call to monitoring endpoint (proxy behavior)
                self.send_redirect_response(addr, headers, to_ext, transport, client_socket)
                
                # Still track the call attempt for monitoring
                print(f"Call redirected for monitoring: {from_ext} -> {to_ext}")
                
                # Start lightweight RTP monitoring on the redirect target
                # This allows monitoring without complex SIP endpoint behavior
                    
        except Exception as e:
            print(f"Error handling INVITE: {e}")
            self.send_response(addr, '500', 'Internal Server Error', headers, transport, client_socket)
            
    def handle_ack(self, request_line, headers, addr, transport, client_socket=None):
        """Handle ACK requests"""
        call_id = headers.get('call-id')
        print(f"DEBUG: Received ACK for call {call_id} from {addr} via {transport}")
        if call_id and self.call_manager.is_call_active(call_id):
            print(f"Call {call_id} confirmed and established via {transport}")
        else:
            print(f"WARNING: ACK received for inactive call {call_id}")
            
    def handle_bye(self, request_line, headers, addr, transport, client_socket=None):
        """Handle BYE requests"""
        call_id = headers.get('call-id')
        if call_id:
            self.call_manager.end_call(call_id)
            self.send_response(addr, '200', 'OK', headers, transport, client_socket)
            print(f"Call {call_id} terminated via {transport}")
            
    def handle_options(self, request_line, headers, addr, transport, client_socket=None):
        """Handle OPTIONS requests"""
        self.send_response(addr, '200', 'OK', headers, transport, client_socket)
        
    def handle_cancel(self, request_line, headers, addr, transport, client_socket=None):
        """Handle CANCEL requests"""
        self.send_response(addr, '200', 'OK', headers, transport, client_socket)
        
    def handle_test_extension_call(self, extension, call_id, headers, addr, transport, client_socket):
        """Handle calls to test extensions with REAL RTP analysis"""
        test_info = self.test_extensions[extension]
        
        print(f"Test call to {extension} ({test_info['name']}) - Call-ID: {call_id}")
        
        # Send 200 OK with SDP for test extension
        self.send_ok_with_sdp(addr, headers, transport, client_socket, call_id)
        
        # Start REAL RTP processing - same as normal calls
        rtp_port = self.parse_sdp_port(headers)
        if rtp_port:
            print(f"Starting REAL RTP analysis for test extension {extension} on port {rtp_port}")
            self.start_rtp_processing(call_id, rtp_port, addr[0])
        else:
            print(f"Warning: Could not parse RTP port for test extension {extension}")
        
        # Notify dashboard of test call
        self.socketio.emit('test_call_started', {
            'call_id': call_id,
            'extension': extension,
            'test_name': test_info['name'],
            'analysis_type': 'real_rtp',  # Changed from 'simulation'
            'timestamp': datetime.now().isoformat()
        })
        

        
    def forward_invite(self, request_line, headers, to_extension, transport, client_socket=None):
        """Forward INVITE to registered device"""
        # Implementation for call forwarding
        pass
        
    def send_response(self, addr, code, reason, request_headers, transport='UDP', client_socket=None):
        """Send SIP response"""
        try:
            via = request_headers.get('via', '')
            call_id_header = request_headers.get('call-id', 'unknown')
            from_header = request_headers.get('from', '')
            to_header = request_headers.get('to', '')
            cseq = request_headers.get('cseq', '1 REGISTER')
            
            response = f"SIP/2.0 {code} {reason}\r\n"
            response += f"Via: {via}\r\n"
            response += f"Call-ID: {call_id_header}\r\n"
            response += f"From: {from_header}\r\n"
            response += f"To: {to_header}\r\n"
            response += f"CSeq: {cseq}\r\n"
            response += f"Server: VoIP-Quality-Monitor-Registrar/1.0\r\n"
            
            if code == '200' and 'REGISTER' in cseq:
                response += f"Contact: {request_headers.get('contact', '')}\r\n"
                response += f"Expires: {self.registration_expires}\r\n"
                
            response += "Content-Length: 0\r\n\r\n"
            
            # Send via appropriate transport
            if transport == 'TCP' and client_socket:
                client_socket.send(response.encode('utf-8'))
            elif transport == 'TLS' and client_socket:
                client_socket.send(response.encode('utf-8'))
            else:
                self.udp_socket.sendto(response.encode('utf-8'), addr)
                
            print(f"Sent {code} {reason} to {addr} via {transport}")
            
            # Broadcast outgoing SIP message to dashboard
            self.broadcast_sip_message(response, addr, transport, 'outgoing')
            
        except Exception as e:
            print(f"Error sending SIP response: {e}")
            
    def send_ok_with_sdp(self, addr, request_headers, transport, client_socket, call_id):
        """Send 200 OK with SDP for INVITE"""
        try:
            sdp = self.generate_sdp()
            
            response = self.build_ok_response(request_headers, len(sdp))
            response += sdp
            
            if transport == 'TCP' and client_socket:
                client_socket.send(response.encode('utf-8'))
            elif transport == 'TLS' and client_socket:
                client_socket.send(response.encode('utf-8'))
            else:
                self.udp_socket.sendto(response.encode('utf-8'), addr)
                
            print(f"Sent 200 OK with SDP to {addr} via {transport}")
            
            # Broadcast outgoing SIP message to dashboard
            self.broadcast_sip_message(response, addr, transport, 'outgoing')
            
        except Exception as e:
            print(f"Error sending OK with SDP: {e}")
            
    def build_ok_response(self, request_headers, content_length):
        """Build 200 OK response headers"""
        via = request_headers.get('via', '')
        call_id = request_headers.get('call-id', '')
        from_header = request_headers.get('from', '')
        to_header = request_headers.get('to', '')
        cseq = request_headers.get('cseq', '')
        
        # Add tag to To header if not present (required for 200 OK responses)
        if 'tag=' not in to_header:
            import random
            tag = f"tag={random.randint(1000000, 9999999)}"
            to_header += f";{tag}"
        
        response = "SIP/2.0 200 OK\r\n"
        response += f"Via: {via}\r\n"
        response += f"Call-ID: {call_id}\r\n"
        response += f"From: {from_header}\r\n"
        response += f"To: {to_header}\r\n"
        response += f"CSeq: {cseq}\r\n"
        response += f"Contact: <sip:{self.get_local_ip()}:{self.udp_port}>\r\n"
        response += "Content-Type: application/sdp\r\n"
        response += f"Content-Length: {content_length}\r\n\r\n"
        
        return response
        
    def extract_extension(self, header):
        """Extract username from SIP header"""
        # Match patterns like: sip:gateway-monitor@domain, sip:201@gateway.local
        match = re.search(r'sip:([^@]+)@', header)
        return match.group(1) if match else None
        
    def extract_contact_uri(self, contact_header):
        """Extract contact URI from Contact header"""
        match = re.search(r'<([^>]+)>', contact_header)
        return match.group(1) if match else contact_header.strip()
        
    def extract_address(self, header):
        """Extract address from SIP header"""
        match = re.search(r'<sip:([^@>]+)@?([^>]*)>', header)
        if match:
            return f"{match.group(1)}@{match.group(2)}" if match.group(2) else match.group(1)
        return header.split()[0] if header else 'unknown'
        
    def parse_sdp_port(self, headers):
        """Parse RTP port from SDP"""
        return 8000  # Default RTP port for monitoring
        
    def generate_sdp(self):
        """Generate SDP for call monitoring"""
        local_ip = self.get_local_ip()
        # Use dynamic RTP port
        import random
        rtp_port = random.randint(10000, 20000)
        
        return f"""v=0
o=voip-monitor 123456 654321 IN IP4 {local_ip}
s=VoIP Quality Monitor
c=IN IP4 {local_ip}
t=0 0
m=audio {rtp_port} RTP/AVP 0 8 18 101
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
a=rtpmap:18 G729/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:18 annexb=yes
a=sendrecv
"""
        
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
            
    def start_rtp_processing(self, call_id, rtp_port, remote_ip):
        """Start RTP stream processing for quality monitoring"""
        def process_rtp():
            try:
                rtp_processor = RTPProcessor(call_id, rtp_port, self.call_manager)
                rtp_processor.start_processing()
            except Exception as e:
                print(f"RTP processing error for call {call_id}: {e}")
        
        rtp_thread = threading.Thread(target=process_rtp, daemon=True)
        rtp_thread.start()
        
    def cleanup_expired_registrations(self):
        """Clean up expired registrations"""
        while self.running:
            try:
                now = datetime.now()
                expired = []
                
                for extension, info in self.registered_devices.items():
                    if info['expires'] < now:
                        expired.append(extension)
                        
                for extension in expired:
                    del self.registered_devices[extension]
                    print(f"Registration expired for extension {extension}")
                    
                    self.socketio.emit('device_expired', {
                        'extension': extension,
                        'timestamp': now.isoformat()
                    })
                    
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in registration cleanup: {e}")
                time.sleep(60)
                
    def get_registered_devices(self):
        """Get list of currently registered devices"""
        devices = []
        for extension, info in self.registered_devices.items():
            devices.append({
                'extension': extension,
                'contact': info['contact'],
                'expires': info['expires'].isoformat(),
                'last_seen': info['last_seen'].isoformat(),
                'transport': info['transport'],
                'addr': f"{info['addr'][0]}:{info['addr'][1]}"
            })
        return devices
    
    def broadcast_sip_message(self, message, addr, transport, direction):
        """Broadcast SIP message to dashboard via WebSocket"""
        try:
            self.socketio.emit('sip_message', {
                'message': message,
                'remote_addr': f"{addr[0]}:{addr[1]}",
                'transport': transport,
                'direction': direction,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error broadcasting SIP message: {e}")
        
    def stop(self):
        """Stop the SIP Registrar"""
        self.running = False
        
        if self.udp_socket:
            self.udp_socket.close()
            
        if self.tcp_socket:
            self.tcp_socket.close()
            
        for client_socket in list(self.tcp_connections.keys()):
            self.close_tcp_connection(client_socket)
    
    def verify_sip_auth(self, authorization, username):
        """Verify SIP authentication credentials using digest authentication"""
        try:
            if username not in self.sip_users:
                print(f"DEBUG: Username {username} not found in sip_users")
                return False
                
            password = self.sip_users[username]
            print(f"DEBUG: Found password for {username}: {password}")
            
            # Parse authorization header
            auth_params = {}
            auth_data = authorization.replace('Digest ', '')
            print(f"DEBUG: Auth data: {auth_data}")
            
            # Split by comma and parse key=value pairs
            for param in auth_data.split(','):
                param = param.strip()
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    auth_params[key] = value
            
            print(f"DEBUG: Parsed auth params: {auth_params}")
            
            # Extract required parameters
            auth_username = auth_params.get('username', '')
            realm = auth_params.get('realm', '')
            nonce = auth_params.get('nonce', '')
            uri = auth_params.get('uri', '')
            response = auth_params.get('response', '')
            
            # Verify username matches
            if auth_username != username:
                print(f"DEBUG: Username mismatch: {auth_username} vs {username}")
                return False
            
            # Calculate expected response using MD5 digest
            import hashlib
            
            # A1 = username:realm:password
            a1 = f"{username}:{realm}:{password}"
            ha1 = hashlib.md5(a1.encode()).hexdigest()
            print(f"DEBUG: A1={a1}, HA1={ha1}")
            
            # A2 = method:uri (method is REGISTER for registration)
            a2 = f"REGISTER:{uri}"
            ha2 = hashlib.md5(a2.encode()).hexdigest()
            print(f"DEBUG: A2={a2}, HA2={ha2}")
            
            # Response = MD5(HA1:nonce:HA2)
            expected_response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()
            print(f"DEBUG: Expected response: {expected_response}")
            print(f"DEBUG: Received response: {response}")
            
            # Compare responses
            result = response.lower() == expected_response.lower()
            print(f"DEBUG: Auth result: {result}")
            return result
            
        except Exception as e:
            print(f"Auth verification error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_auth_challenge(self, addr, request_headers, transport, client_socket=None):
        """Send 401 Unauthorized with authentication challenge"""
        try:
            via = request_headers.get('via', '')
            call_id = request_headers.get('call-id', 'unknown')
            from_header = request_headers.get('from', '')
            to_header = request_headers.get('to', '')
            cseq = request_headers.get('cseq', '1 REGISTER')
            
            # Generate nonce for digest auth
            import hashlib
            import time
            nonce = hashlib.md5(f"{time.time()}{addr}".encode()).hexdigest()
            
            response = f"SIP/2.0 401 Unauthorized\r\n"
            response += f"Via: {via}\r\n"
            response += f"Call-ID: {call_id}\r\n"
            response += f"From: {from_header}\r\n"
            response += f"To: {to_header}\r\n"
            response += f"CSeq: {cseq}\r\n"
            response += f'WWW-Authenticate: Digest realm="{self.domain}", nonce="{nonce}"\r\n'
            response += f"Server: VoIP-Quality-Monitor-Registrar/1.0\r\n"
            response += "Content-Length: 0\r\n\r\n"
            
            # Send via appropriate transport
            if transport == 'TCP' and client_socket:
                client_socket.send(response.encode('utf-8'))
            elif transport == 'TLS' and client_socket:
                client_socket.send(response.encode('utf-8'))
            else:
                self.udp_socket.sendto(response.encode('utf-8'), addr)
            
            # Broadcast outgoing challenge to dashboard
            self.broadcast_sip_message(response, addr, transport, 'outgoing')
            print(f"Sent 401 Unauthorized to {addr} via {transport}")
            
        except Exception as e:
            print(f"Error sending auth challenge: {e}")
            
    def send_redirect_response(self, addr, request_headers, to_ext, transport, client_socket=None):
        """Send 302 Moved Temporarily redirect response"""
        try:
            via = request_headers.get('via', '')
            call_id = request_headers.get('call-id', '')
            from_header = request_headers.get('from', '')
            to_header = request_headers.get('to', '')
            cseq = request_headers.get('cseq', '')
            
            # Add tag to To header for redirect response
            if 'tag=' not in to_header:
                import random
                tag = f"tag={random.randint(1000000, 9999999)}"
                to_header += f";{tag}"
            
            # Create redirect to echo test service (simulates call completion)
            local_ip = self.get_local_ip()
            redirect_uri = f"sip:echo@{local_ip}:5060"
            
            response = "SIP/2.0 302 Moved Temporarily\r\n"
            response += f"Via: {via}\r\n"
            response += f"Call-ID: {call_id}\r\n"
            response += f"From: {from_header}\r\n"
            response += f"To: {to_header}\r\n"
            response += f"CSeq: {cseq}\r\n"
            response += f"Contact: <{redirect_uri}>\r\n"
            response += f"Server: VoIP-Quality-Monitor-Proxy/1.0\r\n"
            response += "Content-Length: 0\r\n\r\n"
            
            # Send via appropriate transport
            if transport == 'TCP' and client_socket:
                client_socket.send(response.encode('utf-8'))
            elif transport == 'TLS' and client_socket:
                client_socket.send(response.encode('utf-8'))
            else:
                self.udp_socket.sendto(response.encode('utf-8'), addr)
                
            print(f"Sent 302 Redirect to {addr} via {transport} -> {redirect_uri}")
            
            # Broadcast redirect response to dashboard
            self.broadcast_sip_message(response, addr, transport, 'outgoing')
            
        except Exception as e:
            print(f"Error sending redirect response: {e}")