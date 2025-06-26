import socket
import struct
import threading
import time
from datetime import datetime
import numpy as np
from mos_calculator import MOSCalculator

class RTPProcessor:
    def __init__(self, call_id, port, call_manager):
        self.call_id = call_id
        self.port = port
        self.call_manager = call_manager
        self.socket = None
        self.running = False
        self.mos_calculator = MOSCalculator()
        
        # Quality metrics
        self.packets_received = 0
        self.packets_lost = 0
        self.jitter_buffer = []
        self.last_packet_time = None
        self.sequence_numbers = []
        self.timestamps = []
        self.detected_codec = 'G.711'  # Default codec, updated from RTP packets
        
    def start_processing(self):
        """Start processing RTP packets"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.settimeout(1.0)
            self.running = True
            
            print(f"RTP Processor listening on port {self.port} for call {self.call_id}")
            
            packet_count = 0
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    packet_count += 1
                    if packet_count <= 5:  # Log first 5 packets
                        print(f"RTP packet #{packet_count} received from {addr} ({len(data)} bytes) for call {self.call_id}")
                    elif packet_count == 6:
                        print(f"RTP processing active for call {self.call_id} - logging reduced")
                    
                    self.process_packet(data, addr)
                    
                except socket.timeout:
                    # Check if call is still active
                    if not self.call_manager.is_call_active(self.call_id):
                        print(f"Call {self.call_id} no longer active, stopping RTP processing")
                        break
                    
                    # Update with zero metrics if no packets received
                    if time.time() - self.last_update_time > 5:
                        print(f"DEBUG RTP: No packets for 5s on port {self.port}, updating with zero metrics")
                        self.update_call_metrics_with_zeros()
                        self.last_update_time = time.time()
                    continue
                    
                except Exception as e:
                    print(f"Error processing RTP packet for call {self.call_id}: {e}")
                    
        except Exception as e:
            print(f"Error starting RTP processor: {e}")
        finally:
            self.stop_processing()
            
    def stop_processing(self):
        """Stop processing RTP packets"""
        self.running = False
        if self.socket:
            self.socket.close()
            
    def process_packet(self, data, addr):
        """Process individual RTP packet"""
        try:
            if len(data) < 12:  # RTP header is at least 12 bytes
                print(f"DEBUG RTP: Packet too short ({len(data)} bytes) from {addr}")
                return
                
            # Parse RTP header
            rtp_header = self.parse_rtp_header(data)
            
            if rtp_header:
                self.packets_received += 1
                current_time = time.time()
                
                print(f"DEBUG RTP: Packet #{self.packets_received} from {addr}, seq={rtp_header['sequence']}, PT={rtp_header.get('payload_type', 'unknown')}")
                
                # Update detected codec from RTP header
                if 'codec' in rtp_header:
                    self.detected_codec = rtp_header['codec']
                    print(f"DEBUG RTP: Codec detected: {self.detected_codec}")
                
                # Calculate packet loss
                self.calculate_packet_loss(rtp_header['sequence'])
                
                # Calculate jitter
                if self.last_packet_time:
                    inter_arrival = current_time - self.last_packet_time
                    self.calculate_jitter(inter_arrival)
                    
                self.last_packet_time = current_time
                
                # Update call metrics every 10 packets
                if self.packets_received % 10 == 0:
                    print(f"DEBUG RTP: Updating metrics after {self.packets_received} packets")
                    self.update_call_metrics()
            else:
                print(f"DEBUG RTP: Failed to parse RTP header from {addr}")
                    
        except Exception as e:
            print(f"Error processing packet: {e}")
            import traceback
            traceback.print_exc()
            
    def parse_rtp_header(self, data):
        """Parse RTP header"""
        try:
            # RTP header format (first 12 bytes)
            header = struct.unpack('!BBHII', data[:12])
            
            version = (header[0] >> 6) & 0x3
            padding = (header[0] >> 5) & 0x1
            extension = (header[0] >> 4) & 0x1
            cc = header[0] & 0xF
            
            marker = (header[1] >> 7) & 0x1
            payload_type = header[1] & 0x7F
            
            sequence = header[2]
            timestamp = header[3]
            ssrc = header[4]
            
            # Determine codec from payload type
            codec = self.get_codec_from_payload_type(payload_type)
            
            return {
                'version': version,
                'sequence': sequence,
                'timestamp': timestamp,
                'ssrc': ssrc,
                'payload_type': payload_type,
                'marker': marker,
                'codec': codec
            }
            
        except Exception as e:
            print(f"Error parsing RTP header: {e}")
            return None
    
    def get_codec_from_payload_type(self, payload_type):
        """Map RTP payload type to codec name"""
        # Standard payload types (RFC 3551) + Welcome Italia compatibility
        standard_payload_types = {
            0: 'G.711',    # PCMU
            8: 'G.711',    # PCMA (alaw - Welcome Italia)
            18: 'G.729',   # G.729 (Welcome Italia primary)
            19: 'G.729',   # G.729A (Welcome Italia variant)
            4: 'G.723.1',  # G.723
            3: 'GSM',      # GSM
            97: 'iLBC',    # iLBC (dynamic)
            98: 'G.729',   # G.729 (alternative dynamic type)
            99: 'G.729A',  # G.729A (alternative dynamic type)
            111: 'Opus',   # Opus (commonly used dynamic type)
            120: 'Opus',   # Opus (alternative dynamic type)
        }
        
        # Check for dynamic payload types that could be Opus
        if payload_type >= 96 and payload_type <= 127:
            # Dynamic payload type - assume Opus for common ranges
            if payload_type in [96, 97, 111, 120, 121, 122]:
                return 'Opus'
            return 'Unknown'
        
        return standard_payload_types.get(payload_type, 'G.711')
            
    def calculate_packet_loss(self, sequence):
        """Calculate packet loss percentage"""
        self.sequence_numbers.append(sequence)
        
        if len(self.sequence_numbers) > 100:
            # Keep only last 100 sequences
            self.sequence_numbers = self.sequence_numbers[-100:]
            
        if len(self.sequence_numbers) > 1:
            expected_packets = max(self.sequence_numbers) - min(self.sequence_numbers) + 1
            received_packets = len(set(self.sequence_numbers))
            self.packets_lost = expected_packets - received_packets
            
    def calculate_jitter(self, inter_arrival):
        """Calculate jitter using RFC 3550 algorithm"""
        self.jitter_buffer.append(inter_arrival)
        
        if len(self.jitter_buffer) > 50:
            # Keep only last 50 measurements
            self.jitter_buffer = self.jitter_buffer[-50:]
            
    def get_jitter(self):
        """Get current jitter value in milliseconds"""
        if len(self.jitter_buffer) < 2:
            return 0
            
        # Calculate jitter as standard deviation of inter-arrival times
        jitter = np.std(self.jitter_buffer) * 1000  # Convert to milliseconds
        return jitter
        
    def get_packet_loss_rate(self):
        """Get packet loss rate as percentage"""
        if self.packets_received == 0:
            return 0
            
        total_expected = self.packets_received + self.packets_lost
        if total_expected == 0:
            return 0
            
        return (self.packets_lost / total_expected) * 100
        
    def update_call_metrics(self):
        """Update call quality metrics"""
        try:
            jitter = self.get_jitter()
            packet_loss = self.get_packet_loss_rate()
            
            # Estimate delay (simplified - in production would use RTCP)
            delay = 50  # Default assumption of 50ms delay
            
            # Calculate MOS score using detected codec
            mos_score = self.mos_calculator.calculate_mos(
                packet_loss_rate=int(packet_loss),
                jitter=int(jitter),
                delay=delay,
                codec=self.detected_codec
            )
            
            # Update call manager with metrics
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'packets_received': self.packets_received,
                'packets_lost': self.packets_lost,
                'packet_loss_rate': packet_loss,
                'jitter': jitter,
                'delay': delay,
                'mos_score': mos_score,
                'codec': self.detected_codec
            }
            
            self.call_manager.update_call_metrics(self.call_id, metrics)
            print(f"Call {self.call_id}: MOS={mos_score:.2f}, Loss={packet_loss:.1f}%, Jitter={jitter:.1f}ms, Codec={self.detected_codec}")
            
        except Exception as e:
            print(f"Error updating call metrics: {e}")
            import traceback
            traceback.print_exc()
    
    def update_call_metrics_with_zeros(self):
        """Update call metrics with zero values when no RTP packets are received"""
        try:
            # Create zero metrics to show the call is active but no RTP data
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'packets_received': self.packets_received,  # Might still be 0
                'packets_lost': self.packets_lost,
                'packet_loss_rate': 0.0,
                'jitter': 0.0,
                'delay': 50,  # Default delay assumption
                'mos_score': 0.0,  # Zero indicates no RTP data
                'codec': 'No RTP'
            }
            
            self.call_manager.update_call_metrics(self.call_id, metrics)
            print(f"Call {self.call_id}: No RTP packets - MOS=0.0 (waiting for media)")
            
        except Exception as e:
            print(f"Error updating zero metrics: {e}")
