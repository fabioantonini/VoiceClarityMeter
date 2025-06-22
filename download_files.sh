#!/bin/bash
# Script per scaricare tutti i file necessari per il deployment

echo "VoIP Quality Monitor - Download Files"
echo "====================================="

# Crea directory temporanea
mkdir -p voip-monitor-deployment
cd voip-monitor-deployment

echo "Scaricamento file dell'applicazione..."

# Lista dei file da scaricare dal progetto Replit
FILES=(
    "app_simple.py"
    "sip_registrar.py" 
    "call_manager.py"
    "mos_calculator.py"
    "rtp_processor.py"
    "config_helper.py"
    "database.py"
    "install_ubuntu.sh"
    "start_server.sh"
    "README_DEPLOYMENT.md"
)

# Crea directory necessarie
mkdir -p templates static/css static/js data

echo "File pronti per il deployment:"
for file in "${FILES[@]}"; do
    echo "- $file"
done

echo ""
echo "Directory create:"
echo "- templates/ (per file HTML)"
echo "- static/css/ (per file CSS)"  
echo "- static/js/ (per file JavaScript)"
echo "- data/ (per dati persistenti)"
echo ""
echo "ISTRUZIONI:"
echo "1. Copia tutti i file Python nella directory voip-monitor-deployment/"
echo "2. Copia la cartella templates/ completa"
echo "3. Copia la cartella static/ completa"
echo "4. Trasferisci tutto sul tuo PC Ubuntu"
echo "5. Esegui: chmod +x install_ubuntu.sh && ./install_ubuntu.sh"