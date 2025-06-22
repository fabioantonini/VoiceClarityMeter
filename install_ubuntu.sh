#!/bin/bash
# VoIP Quality Monitor - Installazione per Ubuntu 22.04
# Script di installazione automatica

set -e

echo "=================================="
echo "VoIP Quality Monitor - Installazione"
echo "=================================="

# Controlla se è Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    echo "Attenzione: Questo script è ottimizzato per Ubuntu 22.04"
fi

# Aggiorna il sistema
echo "Aggiornamento sistema..."
sudo apt update
sudo apt upgrade -y

# Installa Python 3.11 e pip
echo "Installazione Python 3.11..."
sudo apt install -y python3.11 python3.11-dev python3.11-venv python3-pip

# Crea directory dell'applicazione
APP_DIR="$HOME/voip-quality-monitor"
echo "Creazione directory: $APP_DIR"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Crea virtual environment
echo "Creazione ambiente virtuale Python..."
python3.11 -m venv venv
source venv/bin/activate

# Installa dipendenze Python
echo "Installazione dipendenze Python..."
pip install --upgrade pip
pip install flask flask-socketio numpy werkzeug

# Crea file requirements.txt
cat > requirements.txt << EOF
flask==2.3.3
flask-socketio==5.3.6
numpy==1.24.3
werkzeug==2.3.7
python-socketio==5.8.0
eventlet==0.33.3
EOF

echo "Dipendenze installate:"
pip list

# Imposta variabili d'ambiente
echo "Configurazione variabili d'ambiente..."
cat > .env << EOF
# VoIP Quality Monitor Configuration
FLASK_APP=app_simple.py
FLASK_ENV=production
FLASK_DEBUG=False
HOST=0.0.0.0
PORT=5000
EOF

# Ottieni IP locale
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=================================="
echo "INSTALLAZIONE COMPLETATA!"
echo "=================================="
echo ""
echo "IP del server: $LOCAL_IP"
echo "Directory applicazione: $APP_DIR"
echo ""
echo "CONFIGURAZIONE GATEWAY ASTERISK:"
echo "set voip sip profile create voip-monitor"
echo "set voip sip profile voip-monitor registrar $LOCAL_IP"
echo "set voip sip profile voip-monitor sip-domain voip-monitor.local"
echo "set voip sip profile voip-monitor codec-type g711 alaw ulaw"
echo "set voip sip profile voip-monitor port 5060"
echo "set voip fxs port 1 profile voip-monitor extension 201"
echo "set voip fxs port 2 profile voip-monitor extension 202"
echo ""
echo "COMANDI PER AVVIARE:"
echo "cd $APP_DIR"
echo "source venv/bin/activate"
echo "python app_simple.py"
echo ""
echo "URL Dashboard: http://$LOCAL_IP:5000"
echo ""
echo "PORTA FIREWALL: Assicurati che le porte 5000 e 5060 siano aperte"
echo "sudo ufw allow 5000"
echo "sudo ufw allow 5060"
echo ""