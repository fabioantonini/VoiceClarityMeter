#!/usr/bin/env python3
"""
Script per generare la configurazione gateway Welcome Italia
per VoIP Quality Monitor come registrar/proxy
"""

import socket
import sys

def get_local_ip():
    """Ottiene l'IP locale della webapp"""
    try:
        # Connessione temporanea per ottenere IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "192.168.1.100"  # IP di fallback

def generate_gateway_config(webapp_ip, use_tls=False, original_registrar=None):
    """Genera configurazione CLI per gateway Welcome Italia"""
    
    # Porta SIP
    sip_port = 5061 if use_tls else 5060
    transport = "tls" if use_tls else "udp"
    
    config = f"""
# Configurazione Gateway Welcome Italia per VoIP Quality Monitor
# Data: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# ==================================================================
# CONFIGURAZIONE PER MONITORAGGIO QUALITÀ
# Il gateway si registrerà alla webapp per analisi chiamate
# ==================================================================

# Backup configurazione originale (per ripristino)
# set voip sip profile welcome registrar proxy01-sip.welcomeitalia.it

# Nuova configurazione: webapp come registrar/proxy
set voip sip profile welcome registrar {webapp_ip}:{sip_port}
set voip sip profile welcome outbound-proxy {webapp_ip}:{sip_port}
set voip sip profile welcome sip-domain voip-monitor.local"""

    if use_tls:
        config += f"""
set voip sip profile welcome transport-protocol tls"""
    
    config += f"""

# Mantieni configurazione codec (già ottimali per Welcome Italia)
set voip sip profile welcome codec-type g729 alaw
set voip sip profile welcome dtmf rfc4733
set voip sip profile welcome registration-expiry 3600
set voip sip profile welcome registration-retry-timer 57

# Abilita funzioni per monitoraggio qualità
set voip sip profile welcome caller-rewrite yes
set voip sip profile welcome rfc3325-header preferred
set voip sip profile welcome enable-prack supported

# Configurazione trunk esistente (mantieni invariata)
set voip trunk sip welcome1 username 08631780017
set voip trunk sip welcome1 authentication-password WLC40808S117L1
set voip trunk sip welcome1 codec-type g729 alaw
set voip trunk sip welcome1 authentication-username s08631780017
set voip trunk sip welcome1 display-name 08631780017
set voip trunk sip welcome1 dtmf rfc4733
set voip trunk sip welcome1 sip-profile welcome
set voip trunk sip welcome1 enable yes

# ==================================================================
# CONFIGURAZIONE OPZIONALE PER QoS
# ==================================================================

# Abilita QoS per migliore analisi qualità
set voip qos dscp-marking ef
set voip qos packet-loss-concealment yes

# Configurazione RTP per monitoraggio
set voip rtp local-port-range 10000 20000
set voip rtp jitter-buffer adaptive

# ==================================================================
# COMANDI DI VERIFICA
# ==================================================================

# Verifica registrazione
show voip sip registration
show voip trunk status

# Test chiamate qualità webapp
# Chiama: 999 (Test Qualità), 998 (Test Rumore)
# Chiama: 997 (Test Echo), 996 (Test Packet Loss)

# ==================================================================
# RIPRISTINO CONFIGURAZIONE ORIGINALE
# ==================================================================

# Per tornare alla configurazione originale Welcome Italia:
# set voip sip profile welcome registrar proxy01-sip.welcomeitalia.it
# set voip sip profile welcome sip-domain welcomeitalia.it
# set voip sip profile welcome transport-protocol udp"""

    if original_registrar:
        config += f"""

# Ripristino con registrar originale specifico:
# set voip sip profile welcome registrar {original_registrar}"""

    return config

def generate_webapp_verification():
    """Genera comandi per verificare webapp"""
    return """
# ==================================================================
# VERIFICA WEBAPP VOIP QUALITY MONITOR
# ==================================================================

# 1. Verifica che webapp sia in esecuzione
curl -s http://{webapp_ip}:5000 | grep -q "VoIP Quality Monitor" && echo "✓ Webapp attiva" || echo "✗ Webapp non raggiungibile"

# 2. Verifica porte SIP
nmap -p 5060,5061 {webapp_ip} 2>/dev/null | grep -E "(5060|5061).*open" && echo "✓ Porte SIP aperte" || echo "✗ Porte SIP chiuse"

# 3. Test connessione SIP (da gateway)
sip-test {webapp_ip} 5060

# 4. Dashboard monitoraggio
# Apri browser: http://{webapp_ip}:5000/dashboard
"""

def main():
    print("=" * 60)
    print("GENERATORE CONFIGURAZIONE GATEWAY WELCOME ITALIA")
    print("per VoIP Quality Monitor")
    print("=" * 60)
    
    # Ottieni IP webapp
    default_ip = get_local_ip()
    webapp_ip = input(f"IP della webapp VoIP Monitor [{default_ip}]: ").strip() or default_ip
    
    # Scelta trasporto
    use_tls = input("Usare TLS/SIPS per sicurezza? [s/N]: ").strip().lower().startswith('s')
    
    # Registrar originale (opzionale)
    original_registrar = input("Registrar originale Welcome Italia [proxy01-sip.welcomeitalia.it]: ").strip() or "proxy01-sip.welcomeitalia.it"
    
    print("\n" + "=" * 60)
    print("CONFIGURAZIONE GENERATA")
    print("=" * 60)
    
    # Genera configurazione
    config = generate_gateway_config(webapp_ip, use_tls, original_registrar)
    print(config)
    
    # Genera verifica
    verification = generate_webapp_verification().format(webapp_ip=webapp_ip)
    print(verification)
    
    # Salva su file
    filename = f"welcome_gateway_config_{webapp_ip.replace('.', '_')}.txt"
    with open(filename, 'w') as f:
        f.write(config)
        f.write(verification)
    
    print(f"\n✓ Configurazione salvata in: {filename}")
    print(f"\n📋 PASSI SUCCESSIVI:")
    print(f"1. Avvia webapp: python app_simple.py")
    print(f"2. Verifica dashboard: http://{webapp_ip}:5000")
    print(f"3. Applica configurazione gateway (CLI)")
    print(f"4. Verifica registrazione in dashboard")
    print(f"5. Test chiamate qualità: 999, 998, 997, 996")

if __name__ == "__main__":
    main()