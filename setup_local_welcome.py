#!/usr/bin/env python3
"""
Setup automatico per gateway Welcome Italia in ambiente locale
Rileva IP locale e genera configurazione CLI per gateway
"""

import socket
import subprocess
import sys
import os

def get_local_ip():
    """Rileva IP locale del PC"""
    try:
        # Metodo 1: Connessione UDP per ottenere IP routing
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            # Metodo 2: hostname -I
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                for ip in ips:
                    if ip.startswith(('192.168.', '10.', '172.')):
                        return ip
                return ips[0] if ips else None
        except:
            return None

def check_webapp_running(ip):
    """Verifica se webapp è in esecuzione"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((ip, 5000))
        s.close()
        return result == 0
    except:
        return False

def check_sip_ports(ip):
    """Verifica porte SIP disponibili"""
    ports = {'5060': False, '5061': False}
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            result = s.connect_ex((ip, int(port)))
            s.close()
            ports[port] = (result == 0)
        except:
            pass
    return ports

def generate_welcome_config(local_ip, use_tls=False):
    """Genera configurazione CLI per gateway Welcome Italia"""
    port = "5061" if use_tls else "5060"
    transport = "tls" if use_tls else "udp"
    
    config = f"""# Configurazione Gateway Welcome Italia - Setup Locale
# IP PC: {local_ip}
# Data: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# BACKUP CONFIGURAZIONE ORIGINALE
# set voip sip profile welcome registrar proxy01-sip.welcomeitalia.it
# set voip sip profile welcome sip-domain welcomeitalia.it

# CONFIGURAZIONE LOCALE - VoIP Quality Monitor
set voip sip profile welcome registrar {local_ip}:{port}
set voip sip profile welcome outbound-proxy {local_ip}:{port}
set voip sip profile welcome sip-domain voip-monitor.local"""

    if use_tls:
        config += f"\nset voip sip profile welcome transport-protocol tls"
    
    config += f"""

# Mantieni configurazione codec Welcome Italia
set voip sip profile welcome codec-type g729 alaw
set voip sip profile welcome dtmf rfc4733
set voip sip profile welcome registration-expiry 3600
set voip sip profile welcome registration-retry-timer 57

# Configurazioni per monitoraggio qualità
set voip sip profile welcome caller-rewrite yes
set voip sip profile welcome rfc3325-header preferred
set voip sip profile welcome enable-prack supported

# Trunk Welcome Italia (MANTIENI INVARIATA)
set voip trunk sip welcome1 username 08631780017
set voip trunk sip welcome1 authentication-password WLC40808S117L1
set voip trunk sip welcome1 codec-type g729 alaw
set voip trunk sip welcome1 authentication-username s08631780017
set voip trunk sip welcome1 display-name 08631780017
set voip trunk sip welcome1 dtmf rfc4733
set voip trunk sip welcome1 sip-profile welcome
set voip trunk sip welcome1 enable yes

# VERIFICA REGISTRAZIONE
show voip sip registration
show voip trunk status

# TEST CHIAMATE QUALITÀ
# 999 - Test Qualità Generale
# 998 - Test con Rumore  
# 997 - Test Echo/Delay
# 996 - Test Packet Loss

# RIPRISTINO RAPIDO
# set voip sip profile welcome registrar proxy01-sip.welcomeitalia.it
# set voip sip profile welcome sip-domain welcomeitalia.it"""

    return config

def setup_firewall(local_ip):
    """Configura firewall per webapp locale"""
    commands = [
        "sudo ufw allow 5000/tcp comment 'VoIP Monitor Dashboard'",
        "sudo ufw allow 5060/tcp comment 'SIP TCP'", 
        "sudo ufw allow 5060/udp comment 'SIP UDP'",
        "sudo ufw allow 5061/tcp comment 'SIP TLS'",
        "sudo ufw allow 10000:20000/udp comment 'RTP Media'"
    ]
    
    print("Configurazione firewall consigliata:")
    for cmd in commands:
        print(f"  {cmd}")
    
    return commands

def main():
    print("=" * 60)
    print("SETUP LOCALE - GATEWAY WELCOME ITALIA")
    print("VoIP Quality Monitor")
    print("=" * 60)
    
    # Rileva IP locale
    local_ip = get_local_ip()
    if not local_ip:
        print("✗ Impossibile rilevare IP locale")
        local_ip = input("Inserisci manualmente IP del PC: ").strip()
        if not local_ip:
            sys.exit(1)
    
    print(f"📍 IP PC rilevato: {local_ip}")
    
    # Verifica webapp
    webapp_running = check_webapp_running(local_ip)
    print(f"🌐 Webapp status: {'✓ Attiva' if webapp_running else '✗ Non attiva'}")
    
    # Verifica porte SIP
    sip_ports = check_sip_ports(local_ip)
    print(f"🔌 Porta 5060 (SIP): {'✓ Aperta' if sip_ports['5060'] else '✗ Chiusa'}")
    print(f"🔒 Porta 5061 (TLS): {'✓ Aperta' if sip_ports['5061'] else '✗ Chiusa'}")
    
    print("\n" + "=" * 60)
    
    # Scelta TLS
    use_tls = False
    if sip_ports['5061']:
        use_tls = input("Usare TLS (porta 5061) per sicurezza? [s/N]: ").strip().lower().startswith('s')
    
    # Genera configurazione
    config = generate_welcome_config(local_ip, use_tls)
    
    print("CONFIGURAZIONE GATEWAY GENERATA:")
    print("=" * 60)
    print(config)
    
    # Salva configurazione
    filename = f"welcome_config_{local_ip.replace('.', '_')}.txt"
    with open(filename, 'w') as f:
        f.write(config)
    
    print(f"\n✓ Configurazione salvata: {filename}")
    
    # Setup firewall
    print("\n" + "=" * 60)
    setup_firewall(local_ip)
    
    # Istruzioni finali
    print("\n" + "=" * 60)
    print("📋 PASSI SUCCESSIVI:")
    print("=" * 60)
    
    if not webapp_running:
        print("1. Avvia webapp:")
        print("   source venv/bin/activate")
        print("   python app_simple.py")
        print()
    
    print(f"2. Verifica dashboard: http://{local_ip}:5000")
    print()
    print("3. Applica configurazione su gateway Welcome Italia")
    print(f"   (usa i comandi in {filename})")
    print()
    print("4. Verifica registrazione gateway in dashboard")
    print()
    print("5. Test chiamate qualità: 999, 998, 997, 996")
    print()
    print("6. Per ripristinare configurazione originale:")
    print("   set voip sip profile welcome registrar proxy01-sip.welcomeitalia.it")
    
    print("\n" + "=" * 60)
    print("✓ Setup locale completato!")
    print("=" * 60)

if __name__ == "__main__":
    main()