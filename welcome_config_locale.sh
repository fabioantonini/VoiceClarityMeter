#!/bin/bash

# Script per generare configurazione Gateway Welcome Italia per ambiente locale
# Rileva automaticamente IP locale e genera comandi CLI

echo "============================================================"
echo "CONFIGURAZIONE GATEWAY WELCOME ITALIA - AMBIENTE LOCALE"
echo "============================================================"

# Rileva IP locale
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP=$(ip route get 8.8.8.8 | awk '{print $7; exit}')
fi

echo "📍 IP PC rilevato: $LOCAL_IP"

# Verifica webapp attiva
if curl -s --max-time 2 http://$LOCAL_IP:5000 >/dev/null 2>&1; then
    echo "🌐 Webapp: ✓ Attiva su porta 5000"
else
    echo "🌐 Webapp: ✗ Non attiva - avvia con 'python app_simple.py'"
fi

# Verifica porte SIP
if nc -z $LOCAL_IP 5060 2>/dev/null; then
    echo "🔌 SIP UDP/TCP: ✓ Porta 5060 aperta"
else
    echo "🔌 SIP UDP/TCP: ✗ Porta 5060 chiusa"
fi

if nc -z $LOCAL_IP 5061 2>/dev/null; then
    echo "🔒 SIP TLS: ✓ Porta 5061 aperta"
    TLS_AVAILABLE=true
else
    echo "🔒 SIP TLS: ✗ Porta 5061 chiusa"
    TLS_AVAILABLE=false
fi

echo ""
echo "============================================================"
echo "CONFIGURAZIONE CLI GATEWAY WELCOME ITALIA"
echo "============================================================"

# Genera configurazione
cat > welcome_gateway_locale.txt << EOF
# Configurazione Gateway Welcome Italia per VoIP Quality Monitor
# IP PC Locale: $LOCAL_IP
# Data: $(date '+%Y-%m-%d %H:%M:%S')

# ==================================================================
# BACKUP CONFIGURAZIONE ORIGINALE
# ==================================================================
# set voip sip profile welcome registrar proxy01-sip.welcomeitalia.it
# set voip sip profile welcome sip-domain welcomeitalia.it

# ==================================================================
# CONFIGURAZIONE LOCALE - VoIP Quality Monitor
# ==================================================================

# Configurazione SIP Profile per webapp locale
set voip sip profile welcome registrar $LOCAL_IP:5060
set voip sip profile welcome outbound-proxy $LOCAL_IP:5060
set voip sip profile welcome sip-domain voip-monitor.local

# Mantieni configurazione codec Welcome Italia (ottimale)
set voip sip profile welcome codec-type g729 alaw
set voip sip profile welcome dtmf rfc4733
set voip sip profile welcome registration-expiry 3600
set voip sip profile welcome registration-retry-timer 57

# Configurazioni per monitoraggio qualità
set voip sip profile welcome caller-rewrite yes
set voip sip profile welcome rfc3325-header preferred
set voip sip profile welcome enable-prack supported

# ==================================================================
# CONFIGURAZIONE TRUNK (MANTIENI ESISTENTE)
# ==================================================================

set voip trunk sip welcome1 username 08631780017
set voip trunk sip welcome1 authentication-password WLC40808S117L1
set voip trunk sip welcome1 codec-type g729 alaw
set voip trunk sip welcome1 authentication-username s08631780017
set voip trunk sip welcome1 display-name 08631780017
set voip trunk sip welcome1 dtmf rfc4733
set voip trunk sip welcome1 sip-profile welcome
set voip trunk sip welcome1 enable yes

# ==================================================================
# VERIFICA E TEST
# ==================================================================

# Verifica registrazione gateway
show voip sip registration
show voip trunk status

# Test chiamate qualità (dopo configurazione)
# Numero 999: Test Qualità Generale
# Numero 998: Test con Rumore
# Numero 997: Test Echo/Delay  
# Numero 996: Test Packet Loss

# ==================================================================
# RIPRISTINO RAPIDO
# ==================================================================

# Per tornare alla configurazione originale Welcome Italia:
# set voip sip profile welcome registrar proxy01-sip.welcomeitalia.it
# set voip sip profile welcome sip-domain welcomeitalia.it

EOF

# Opzione TLS se disponibile
if [ "$TLS_AVAILABLE" = true ]; then
cat >> welcome_gateway_locale.txt << EOF

# ==================================================================
# CONFIGURAZIONE TLS OPZIONALE (per sicurezza maggiore)
# ==================================================================

# Per abilitare TLS/SIPS su porta 5061:
# set voip sip profile welcome transport-protocol tls
# set voip sip profile welcome registrar $LOCAL_IP:5061

EOF
fi

echo "✓ Configurazione generata: welcome_gateway_locale.txt"
echo ""
echo "============================================================"
echo "PASSI SUCCESSIVI"
echo "============================================================"
echo "1. Assicurati che webapp sia attiva:"
echo "   python app_simple.py"
echo ""
echo "2. Verifica dashboard: http://$LOCAL_IP:5000"
echo ""
echo "3. Applica configurazione sul gateway Welcome Italia:"
echo "   (copia e incolla i comandi da welcome_gateway_locale.txt)"
echo ""
echo "4. Verifica registrazione nella dashboard"
echo ""
echo "5. Test chiamate qualità: 999, 998, 997, 996"
echo ""
echo "============================================================"
echo "CONFIGURAZIONE FIREWALL CONSIGLIATA"
echo "============================================================"
echo "sudo ufw allow 5000/tcp   # Dashboard web"
echo "sudo ufw allow 5060/tcp   # SIP TCP"
echo "sudo ufw allow 5060/udp   # SIP UDP"
echo "sudo ufw allow 5061/tcp   # SIP TLS"
echo "sudo ufw allow 10000:20000/udp  # RTP media"
echo ""
echo "✓ Setup completato!"