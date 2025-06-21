import socket
import json
from datetime import datetime

class ConfigHelper:
    def __init__(self):
        self.client_templates = {
            'xlite': {
                'name': 'X-Lite',
                'config_type': 'manual',
                'instructions': [
                    "1. Open X-Lite application",
                    "2. Go to SIP Account Settings",
                    "3. Enter the following details:",
                    "   - Display Name: VoIP Quality Test",
                    "   - User Name: test",
                    "   - Password: test",
                    "   - Domain: {server_ip}:{server_port}",
                    "   - Register: Yes",
                    "4. Save and test the connection"
                ]
            },
            'zoiper': {
                'name': 'Zoiper',
                'config_type': 'manual',
                'instructions': [
                    "1. Open Zoiper application",
                    "2. Go to Settings > Accounts",
                    "3. Add new SIP account with:",
                    "   - Account Name: VoIP Quality Monitor",
                    "   - Domain: {server_ip}:{server_port}",
                    "   - Username: test",
                    "   - Password: test",
                    "   - Outbound Proxy: {server_ip}:{server_port}",
                    "4. Enable account and test registration"
                ]
            },
            'linphone': {
                'name': 'Linphone',
                'config_type': 'manual',
                'instructions': [
                    "1. Open Linphone application",
                    "2. Go to Settings > Manage SIP accounts",
                    "3. Create new account:",
                    "   - Your SIP identity: sip:test@{server_ip}:{server_port}",
                    "   - SIP Proxy address: sip:{server_ip}:{server_port}",
                    "   - Username: test",
                    "   - Password: test",
                    "4. Save and register account"
                ]
            },
            'asterisk': {
                'name': 'Asterisk',
                'config_type': 'file',
                'filename': 'sip.conf',
                'content': '''[general]
context=default
allowoverlap=no
udpbindaddr=0.0.0.0:5060
tcpenable=no
tcpbindaddr=0.0.0.0:5060
transport=udp

[test]
type=friend
secret=test
host=dynamic
context=default
canreinvite=no
qualify=yes
nat=force_rport,comedia
dtmfmode=rfc2833
disallow=all
allow=ulaw
allow=alaw

; Dial plan in extensions.conf
; [default]
; exten => 100,1,Dial(SIP/{server_ip}:{server_port}/test)
'''
            },
            'opensips': {
                'name': 'OpenSIPS',
                'config_type': 'file',
                'filename': 'opensips.cfg',
                'content': '''# OpenSIPS configuration for VoIP Quality Monitor

listen=udp:0.0.0.0:5060

loadmodule "signaling.so"
loadmodule "sl.so"
loadmodule "tm.so"
loadmodule "rr.so"
loadmodule "maxfwd.so"
loadmodule "usrloc.so"
loadmodule "registrar.so"
loadmodule "textops.so"
loadmodule "uri.so"
loadmodule "dialog.so"

# Route to VoIP Quality Monitor
route[QUALITY_MONITOR] {{
    $ru = "sip:{server_ip}:{server_port}";
    route(RELAY);
}}

route[RELAY] {{
    t_on_failure("MANAGE_FAILURE");
    if (!t_relay()) {{
        send_reply("500", "Internal Error");
    }}
    exit;
}}
'''
            },
            'generic': {
                'name': 'Generic SIP Client',
                'config_type': 'manual',
                'instructions': [
                    "1. Configure your SIP client with these settings:",
                    "   - Server/Domain: {server_ip}",
                    "   - Port: {server_port}",
                    "   - Username: test",
                    "   - Password: test",
                    "   - Transport: UDP",
                    "   - Codec: G.711 (PCMU/PCMA)",
                    "2. Register the account",
                    "3. Make a test call to verify connection"
                ]
            }
        }
        
    def generate_config(self, client_type, server_ip, server_port):
        """Generate configuration for specific SIP client"""
        template = self.client_templates.get(client_type, self.client_templates['generic'])
        
        config = {
            'client_name': template['name'],
            'config_type': template['config_type'],
            'server_ip': server_ip,
            'server_port': server_port,
            'generated_at': datetime.now().isoformat()
        }
        
        if template['config_type'] == 'manual':
            config['instructions'] = [
                instruction.format(server_ip=server_ip, server_port=server_port)
                for instruction in template['instructions']
            ]
        elif template['config_type'] == 'file':
            config['filename'] = template['filename']
            config['content'] = template['content'].format(
                server_ip=server_ip,
                server_port=server_port
            )
            
        # Add common settings
        config['common_settings'] = {
            'domain': f"{server_ip}:{server_port}",
            'username': 'test',
            'password': 'test',
            'transport': 'UDP',
            'codecs': ['G.711 PCMU', 'G.711 PCMA'],
            'rtp_port_range': '10000-20000'
        }
        
        # Add testing information
        config['testing'] = {
            'test_number': 'sip:test@' + server_ip,
            'call_duration': 'Recommended: 30-60 seconds for quality measurement',
            'audio_test': 'Speak clearly for accurate quality assessment'
        }
        
        return config
        
    def test_connectivity(self, target_ip, target_port):
        """Test network connectivity to target"""
        result = {
            'target_ip': target_ip,
            'target_port': target_port,
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # Test UDP connectivity (SIP)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            # Send a simple UDP packet
            test_message = b"OPTIONS sip:test@" + target_ip.encode() + b" SIP/2.0\r\n\r\n"
            sock.sendto(test_message, (target_ip, target_port))
            
            result['tests']['udp_connectivity'] = {
                'status': 'success',
                'message': 'UDP connectivity test passed'
            }
            
        except socket.timeout:
            result['tests']['udp_connectivity'] = {
                'status': 'timeout',
                'message': 'UDP connectivity test timed out'
            }
        except Exception as e:
            result['tests']['udp_connectivity'] = {
                'status': 'failed',
                'message': f'UDP connectivity test failed: {str(e)}'
            }
        finally:
            try:
                sock.close()
            except:
                pass
                
        # Test TCP connectivity (for reference)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target_ip, target_port))
            sock.close()
            
            result['tests']['tcp_connectivity'] = {
                'status': 'success',
                'message': 'TCP connectivity test passed'
            }
            
        except socket.timeout:
            result['tests']['tcp_connectivity'] = {
                'status': 'timeout',
                'message': 'TCP connectivity test timed out'
            }
        except Exception as e:
            result['tests']['tcp_connectivity'] = {
                'status': 'failed',
                'message': f'TCP connectivity test failed: {str(e)}'
            }
            
        # Test DNS resolution
        try:
            socket.gethostbyname(target_ip)
            result['tests']['dns_resolution'] = {
                'status': 'success',
                'message': 'DNS resolution successful'
            }
        except Exception as e:
            result['tests']['dns_resolution'] = {
                'status': 'failed',
                'message': f'DNS resolution failed: {str(e)}'
            }
            
        # Overall status
        all_tests = result['tests'].values()
        if any(test['status'] == 'success' for test in all_tests):
            result['overall_status'] = 'partial_success'
        else:
            result['overall_status'] = 'failed'
            
        if all(test['status'] == 'success' for test in all_tests):
            result['overall_status'] = 'success'
            
        return result
        
    def get_troubleshooting_guide(self):
        """Get troubleshooting guide for common issues"""
        return {
            'common_issues': [
                {
                    'issue': 'Registration Failed',
                    'symptoms': ['Account shows as offline', 'Registration timeout'],
                    'solutions': [
                        'Check server IP address and port',
                        'Verify network connectivity',
                        'Check firewall settings',
                        'Ensure UDP port 5060 is accessible'
                    ]
                },
                {
                    'issue': 'Poor Call Quality',
                    'symptoms': ['Choppy audio', 'Echo', 'Delay'],
                    'solutions': [
                        'Check network bandwidth',
                        'Reduce network congestion',
                        'Use QoS settings',
                        'Try different codec (G.711 recommended)'
                    ]
                },
                {
                    'issue': 'No Audio/One-way Audio',
                    'symptoms': ['Silent calls', 'Can hear but cannot speak'],
                    'solutions': [
                        'Check RTP port range (10000-20000)',
                        'Configure NAT traversal',
                        'Check microphone/speaker settings',
                        'Verify codec compatibility'
                    ]
                },
                {
                    'issue': 'Call Connection Failed',
                    'symptoms': ['Busy tone', 'Call rejected', 'Timeout'],
                    'solutions': [
                        'Verify target number/URI',
                        'Check server availability',
                        'Review SIP logs',
                        'Test with different client'
                    ]
                }
            ],
            'network_requirements': {
                'bandwidth': 'Minimum 64 kbps per call (G.711)',
                'latency': 'Less than 150ms one-way',
                'jitter': 'Less than 30ms',
                'packet_loss': 'Less than 1%'
            },
            'recommended_settings': {
                'codec_priority': ['G.711 PCMU', 'G.711 PCMA', 'G.729'],
                'transport': 'UDP (recommended) or TCP',
                'dtmf': 'RFC 2833',
                'nat_traversal': 'STUN/ICE if behind NAT'
            }
        }
