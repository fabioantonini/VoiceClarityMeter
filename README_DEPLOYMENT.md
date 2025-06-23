# VoIP Quality Monitor - Deployment Ubuntu 22.04

## Installazione Locale (Sviluppo/Test)

### Risoluzione Errore Flask
Se ricevi l'errore `ModuleNotFoundError: No module named 'flask'`:

1. **Attiva ambiente virtuale**
```bash
source venv/bin/activate
```

2. **Usa il nuovo script di installazione locale**
```bash
chmod +x install_local.sh
./install_local.sh
```

3. **Avvia applicazione**
```bash
python app_simple.py
```

## Installazione Produzione

### 1. Download dei file
Scarica tutti i file del progetto dal repository Replit sul tuo PC Ubuntu.

### 2. Installazione automatica
```bash
chmod +x install_ubuntu.sh
./install_ubuntu.sh
```

### 3. Copia file applicazione
Copia tutti i file Python nella directory creata:
```bash
cd ~/voip-quality-monitor
# Copia tutti i file .py, templates/, static/, data/
```

### 4. Configurazione firewall
```bash
sudo ufw allow 5000  # Dashboard web
sudo ufw allow 5060  # SIP server
```

### 5. Avvio applicazione
```bash
cd ~/voip-quality-monitor
source venv/bin/activate
python app_simple.py
```

## Configurazione Gateway Asterisk

Usa l'IP del tuo PC Ubuntu (mostrato durante l'installazione):

```bash
set voip sip profile create voip-monitor
set voip sip profile voip-monitor registrar [IP_UBUNTU]
set voip sip profile voip-monitor sip-domain voip-monitor.local
set voip sip profile voip-monitor codec-type g711 alaw ulaw
set voip sip profile voip-monitor port 5060
set voip fxs port 1 profile voip-monitor extension 201
set voip fxs port 2 profile voip-monitor extension 202
```

## Accesso Dashboard

- URL: `http://[IP_UBUNTU]:5000`
- Login: automatico (demo mode)

## Test Disponibili

### Estensioni FXS del Gateway
- 201, 202 (i tuoi telefoni)

### Estensioni di Test
- 999: Test Audio Qualità (MOS alto)
- 998: Test con Rumore 
- 997: Test Echo/Delay
- 996: Test Packet Loss

## Servizio Automatico (Opzionale)

Crea servizio systemd per avvio automatico:

```bash
sudo nano /etc/systemd/system/voip-monitor.service
```

Contenuto:
```ini
[Unit]
Description=VoIP Quality Monitor
After=network.target

[Service]
Type=simple
User=tuonome
WorkingDirectory=/home/tuonome/voip-quality-monitor
ExecStart=/home/tuonome/voip-quality-monitor/venv/bin/python app_simple.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Attiva servizio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable voip-monitor
sudo systemctl start voip-monitor
```

## Risoluzione Problemi

### Gateway non si registra
1. Verifica IP corretto nel gateway
2. Controlla firewall: `sudo ufw status`
3. Verifica porte aperte: `sudo netstat -tulpn | grep 5060`

### Dashboard non accessibile
1. Controlla se l'app è in esecuzione
2. Verifica porta 5000: `sudo netstat -tulpn | grep 5000`
3. Prova da browser: `http://localhost:5000`

### Log debugging
I log dell'applicazione mostrano le registrazioni SIP in tempo reale.

## Struttura File

```
~/voip-quality-monitor/
├── app_simple.py          # Applicazione principale
├── sip_registrar.py       # Server SIP Registrar/Proxy
├── call_manager.py        # Gestione chiamate
├── mos_calculator.py      # Calcolo qualità audio
├── rtp_processor.py       # Processamento RTP
├── config_helper.py       # Helper configurazione
├── templates/             # Template HTML
├── static/               # CSS, JS, file statici
├── data/                 # Dati persistenti
├── venv/                 # Virtual environment Python
└── requirements.txt      # Dipendenze Python
```