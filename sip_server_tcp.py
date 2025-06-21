import socket
import threading
import re
import select
from datetime import datetime
from rtp_processor import RTPProcessor

class SIPServerTCP:
    def __init__(self, call_manager, socketio):
        self.call_manager = call_manager
        self.socketio = socketio
        self.host = '0.0.0.0'
        self.udp_port = 5060
        self.tcp_port = 5060
        self.udp_socket = None
        self.tcp_socket = None
        self.running = False
        self.active_sessions = {}
        self.tcp_connections = {}
        
    def start(self):
        """Start both UDP and TCP SIP servers"""
        try:
            # Start UDP server
            self.start_udp_server()
            
            # Start TCP server
            self.start_tcp_server()
            
            print(f"SIP Server listening on UDP {self.host}:{self.udp_port}")
            print(f"SIP Server listening on TCP {self.host}:{self.tcp_port}")
            
            self.running = True
            
            # Main server loop handling both UDP and TCP
            self.server_loop()
            
        except Exception as e:
            print(f"Error starting SIP server: {e}")
            
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
        
    def server_loop(self):
        """Main server loop using select for both UDP and TCP"""
        while self.running:
            try:
                # Prepare socket lists for select
                read_sockets = [self.udp_socket, self.tcp_socket]
                read_sockets.extend(self.tcp_connections.keys())
                
                # Use select to handle multiple sockets
                ready_sockets, _, error_sockets = select.select(read_sockets, [], read_sockets, 1.0)
                
                for sock in ready_sockets:
                    if sock == self.udp_socket:
                        # Handle UDP data
                        self.handle_udp_data()
                    elif sock == self.tcp_socket:
                        # Handle new TCP connection
                        self.handle_new_tcp_connection()
                    elif sock in self.tcp_connections:
                        # Handle existing TCP connection data
                        self.handle_tcp_data(sock)
                        
                # Handle socket errors
                for sock in error_sockets:
                    if sock in self.tcp_connections:
                        self.close_tcp_connection(sock)
                        
            except Exception as e:
                print(f"Error in server loop: {e}")
                
    def handle_udp_data(self):
        """Handle incoming UDP data"""
        try:
            data, addr = self.udp_socket.recvfrom(4096)
            threading.Thread(
                target=self.handle_request,
                args=(data, addr, 'UDP'),
                daemon=True
            ).start()
        except socket.error:
            pass  # No data available
            
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
            print(f"New TCP connection from {addr}")
        except socket.error:
            pass  # No connection available
            
    def handle_tcp_data(self, client_socket):
        """Handle data from existing TCP connection"""
        try:
            data = client_socket.recv(4096)
            if not data:
                # Connection closed by client
                self.close_tcp_connection(client_socket)
                return
                
            conn_info = self.tcp_connections[client_socket]
            conn_info['buffer'] += data
            
            # Process complete SIP messages
            self.process_tcp_buffer(client_socket)
            
        except socket.error:
            self.close_tcp_connection(client_socket)
            
    def process_tcp_buffer(self, client_socket):
        """Process buffered TCP data for complete SIP messages"""
        conn_info = self.tcp_connections[client_socket]
        buffer = conn_info['buffer']
        
        while b'\r\n\r\n' in buffer:
            # Find end of SIP headers
            header_end = buffer.find(b'\r\n\r\n') + 4
            
            # Extract headers to check for Content-Length
            headers_data = buffer[:header_end]
            content_length = self.extract_content_length(headers_data)
            
            # Calculate total message length
            total_length = header_end + content_length
            
            if len(buffer) >= total_length:
                # Complete message available
                message = buffer[:total_length]
                buffer = buffer[total_length:]
                
                # Process the complete SIP message
                threading.Thread(
                    target=self.handle_request,
                    args=(message, conn_info['addr'], 'TCP', client_socket),
                    daemon=True
                ).start()
            else:
                # Incomplete message, wait for more data
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
        """Close TCP connection and clean up"""
        try:
            addr = self.tcp_connections[client_socket]['addr']
            print(f"Closing TCP connection from {addr}")
            client_socket.close()
            del self.tcp_connections[client_socket]
        except:
            pass
            
    def stop(self):
        """Stop both UDP and TCP servers"""
        self.running = False
        
        if self.udp_socket:
            self.udp_socket.close()
            
        if self.tcp_socket:
            self.tcp_socket.close()
            
        # Close all TCP connections
        for client_socket in list(self.tcp_connections.keys()):
            self.close_tcp_connection(client_socket)
            
    def handle_request(self, data, addr, transport='UDP', client_socket=None):
        """Handle incoming SIP request (UDP or TCP)"""
        try:
            message = data.decode('utf-8', errors='ignore')
            lines = message.split('\r\n')
            
            if not lines:
                return
                
            request_line = lines[0]
            headers = self.parse_headers(lines[1:])
            
            print(f"Received SIP {transport} request from {addr}: {request_line}")
            
            # Route based on SIP method
            if request_line.startswith('INVITE'):
                self.handle_invite(request_line, headers, addr, transport, client_socket)
            elif request_line.startswith('ACK'):
                self.handle_ack(request_line, headers, addr, transport, client_socket)
            elif request_line.startswith('BYE'):
                self.handle_bye(request_line, headers, addr, transport, client_socket)
            elif request_line.startswith('REGISTER'):
                self.handle_register(request_line, headers, addr, transport, client_socket)
            elif request_line.startswith('OPTIONS'):
                self.handle_options(request_line, headers, addr, transport, client_socket)
            else:
                print(f"Unhandled SIP method: {request_line}")
                
        except Exception as e:
            print(f"Error handling SIP {transport} request: {e}")
            
    def parse_headers(self, header_lines):
        """Parse SIP headers"""
        headers = {}
        for line in header_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        return headers
        
    def handle_invite(self, request_line, headers, addr, transport, client_socket=None):
        """Handle SIP INVITE request"""
        call_id = headers.get('call-id', f"call_{datetime.now().timestamp()}")
        from_header = headers.get('from', '')
        to_header = headers.get('to', '')
        
        # Extract session info
        session_info = {
            'from_address': self.extract_address(from_header),
            'to_address': self.extract_address(to_header),
            'transport': transport,
            'remote_addr': addr
        }
        
        # Start call tracking
        self.call_manager.start_call(call_id, session_info)
        
        # Send response
        self.send_response(addr, '200', 'OK', headers, transport, client_socket, call_id)
        
        # Parse SDP and start RTP processing
        rtp_port = self.parse_sdp(headers)
        if rtp_port:
            self.start_rtp_processing(call_id, rtp_port, addr[0])
            
    def handle_ack(self, request_line, headers, addr, transport, client_socket=None):
        """Handle SIP ACK request"""
        call_id = headers.get('call-id')
        if call_id and self.call_manager.is_call_active(call_id):
            print(f"Call {call_id} confirmed via {transport}")
            
    def handle_bye(self, request_line, headers, addr, transport, client_socket=None):
        """Handle SIP BYE request"""
        call_id = headers.get('call-id')
        if call_id:
            self.call_manager.end_call(call_id)
            self.send_response(addr, '200', 'OK', headers, transport, client_socket)
            print(f"Call {call_id} ended via {transport}")
            
    def handle_register(self, request_line, headers, addr, transport, client_socket=None):
        """Handle SIP REGISTER request"""
        self.send_response(addr, '200', 'OK', headers, transport, client_socket)
        print(f"Registration accepted from {addr} via {transport}")
        
    def handle_options(self, request_line, headers, addr, transport, client_socket=None):
        """Handle SIP OPTIONS request"""
        self.send_response(addr, '200', 'OK', headers, transport, client_socket)
        
    def send_response(self, addr, code, reason, request_headers, transport='UDP', client_socket=None, call_id=None):
        """Send SIP response via UDP or TCP"""
        try:
            # Build SIP response
            via = request_headers.get('via', '')
            call_id_header = request_headers.get('call-id', call_id or 'unknown')
            from_header = request_headers.get('from', '')
            to_header = request_headers.get('to', '')
            cseq = request_headers.get('cseq', '1 INVITE')
            
            response = f"SIP/2.0 {code} {reason}\r\n"
            response += f"Via: {via}\r\n"
            response += f"Call-ID: {call_id_header}\r\n"
            response += f"From: {from_header}\r\n"
            response += f"To: {to_header}\r\n"
            response += f"CSeq: {cseq}\r\n"
            response += f"User-Agent: VoIP-Quality-Monitor/1.0\r\n"
            
            if code == '200' and 'INVITE' in cseq:
                # Add SDP for INVITE response
                sdp = self.generate_sdp()
                response += f"Content-Type: application/sdp\r\n"
                response += f"Content-Length: {len(sdp)}\r\n\r\n"
                response += sdp
            else:
                response += "Content-Length: 0\r\n\r\n"
            
            # Send via appropriate transport
            if transport == 'TCP' and client_socket:
                client_socket.send(response.encode('utf-8'))
            else:
                self.udp_socket.sendto(response.encode('utf-8'), addr)
                
            print(f"Sent {code} {reason} to {addr} via {transport}")
            
        except Exception as e:
            print(f"Error sending SIP response via {transport}: {e}")
            
    def extract_address(self, header):
        """Extract address from SIP header"""
        match = re.search(r'<sip:([^@>]+)@?([^>]*)>', header)
        if match:
            return f"{match.group(1)}@{match.group(2)}" if match.group(2) else match.group(1)
        return header.split()[0] if header else 'unknown'
        
    def parse_sdp(self, headers):
        """Parse SDP from headers (simplified)"""
        return 8000  # Default RTP port
        
    def generate_sdp(self):
        """Generate SDP response"""
        local_ip = self.get_local_ip()
        return f"""v=0
o=voip-monitor 123456 654321 IN IP4 {local_ip}
s=VoIP Quality Monitor
c=IN IP4 {local_ip}
t=0 0
m=audio 8000 RTP/AVP 0
a=rtpmap:0 PCMU/8000
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
        """Start RTP stream processing"""
        def process_rtp():
            try:
                rtp_processor = RTPProcessor(call_id, rtp_port, self.call_manager)
                rtp_processor.start_processing()
            except Exception as e:
                print(f"RTP processing error for call {call_id}: {e}")
        
        rtp_thread = threading.Thread(target=process_rtp, daemon=True)
        rtp_thread.start()