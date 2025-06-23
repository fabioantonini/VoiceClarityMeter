#!/bin/bash

# Script di installazione locale per VoIP Quality Monitor
# Per Ubuntu/Debian con Python 3.11

set -e

echo "=================================================="
echo "VoIP Quality Monitor - Installazione Locale"
echo "=================================================="

# Controlla se siamo in un virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "ERRORE: Devi attivare un ambiente virtuale prima di eseguire questo script"
    echo ""
    echo "Crea e attiva un ambiente virtuale:"
    echo "python3.11 -m venv venv"
    echo "source venv/bin/activate"
    echo ""
    echo "Poi esegui nuovamente questo script."
    exit 1
fi

echo "✓ Ambiente virtuale attivo: $VIRTUAL_ENV"

# Aggiorna pip
echo "Aggiornamento pip..."
python -m pip install --upgrade pip

# Installa le dipendenze Python
echo "Installazione dipendenze Python..."
if [ -f "requirements-local.txt" ]; then
    pip install -r requirements-local.txt
else
    pip install flask flask-socketio flask-login cryptography numpy
fi

# Verifica installazione
echo ""
echo "Verifica installazione..."
python -c "import flask; print(f'Flask {flask.__version__} installato')"
python -c "import flask_socketio; print(f'Flask-SocketIO installato')"
python -c "import cryptography; print(f'Cryptography installato')"
python -c "import numpy; print(f'NumPy installato')"

# Crea directory necessarie
echo ""
echo "Creazione directory necessarie..."
mkdir -p certificates
mkdir -p data

# Controlla se i file di dati esistono, altrimenti li crea
if [ ! -f "data/calls.json" ]; then
    echo "[]" > data/calls.json
    echo "✓ File calls.json creato"
fi

echo ""
echo "=================================================="
echo "✓ Installazione completata con successo!"
echo "=================================================="
echo ""
echo "Per avviare l'applicazione:"
echo "python app_simple.py"
echo ""
echo "Il server sarà disponibile su:"
echo "- Dashboard: http://localhost:5000"
echo "- SIP UDP/TCP: porta 5060"
echo "- SIP TLS: porta 5061"
echo ""