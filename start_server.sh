#!/bin/bash
# Script per avviare il VoIP Quality Monitor su Ubuntu

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

APP_DIR="$HOME/voip-quality-monitor"

echo -e "${BLUE}=================================="
echo -e "VoIP Quality Monitor - Avvio Server"
echo -e "==================================${NC}"

# Controlla se la directory esiste
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}Errore: Directory $APP_DIR non trovata${NC}"
    echo "Esegui prima lo script di installazione: ./install_ubuntu.sh"
    exit 1
fi

cd "$APP_DIR"

# Attiva ambiente virtuale
if [ ! -d "venv" ]; then
    echo -e "${RED}Errore: Virtual environment non trovato${NC}"
    echo "Esegui prima lo script di installazione: ./install_ubuntu.sh"
    exit 1
fi

echo -e "${BLUE}Attivazione ambiente virtuale...${NC}"
source venv/bin/activate

# Controlla se i file Python esistono
if [ ! -f "app_simple.py" ]; then
    echo -e "${RED}Errore: File app_simple.py non trovato${NC}"
    echo "Copia tutti i file Python nella directory $APP_DIR"
    exit 1
fi

# Ottieni IP locale
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Avvio del server VoIP Quality Monitor...${NC}"
echo ""
echo -e "${BLUE}Server IP:${NC} $LOCAL_IP"
echo -e "${BLUE}Dashboard:${NC} http://$LOCAL_IP:5000"
echo -e "${BLUE}SIP Server:${NC} $LOCAL_IP:5060 (UDP/TCP)"
echo ""
echo -e "${GREEN}Configurazione Gateway Asterisk:${NC}"
echo "set voip sip profile voip-monitor registrar $LOCAL_IP"
echo ""
echo -e "${BLUE}Premi Ctrl+C per fermare il server${NC}"
echo ""

# Avvia l'applicazione
python app_simple.py