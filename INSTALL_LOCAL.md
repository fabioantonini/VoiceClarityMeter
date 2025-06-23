# Installazione Locale - VoIP Quality Monitor

## Requisiti di Sistema

- Ubuntu 22.04 o superiore
- Python 3.11
- Ambiente virtuale Python

## Installazione Rapida

1. **Clona il repository e entra nella directory**
```bash
cd VoiceClarityMeter  # o la directory del progetto
```

2. **Crea e attiva ambiente virtuale**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

3. **Esegui lo script di installazione**
```bash
./install_local.sh
```

4. **Avvia l'applicazione**
```bash
python app_simple.py
```

## Installazione Manuale

Se preferisci installare manualmente:

```bash
# Attiva ambiente virtuale
source venv/bin/activate

# Installa dipendenze
pip install -r requirements-local.txt

# Crea directory necessarie
mkdir -p certificates data

# Avvia applicazione
python app_simple.py
```

## Verifica Installazione

Dopo l'avvio, l'applicazione sarà disponibile su:

- **Dashboard Web**: http://localhost:5000
- **SIP Server UDP/TCP**: porta 5060
- **SIP Server TLS**: porta 5061

## Risoluzione Problemi

### Errore "ModuleNotFoundError: No module named 'flask'"
- Assicurati che l'ambiente virtuale sia attivo: `source venv/bin/activate`
- Reinstalla le dipendenze: `pip install -r requirements-local.txt`

### Errori di Permessi
- Rendi eseguibile lo script: `chmod +x install_local.sh`
- Esegui con utente normale (non root)

### Porte in Uso
- Controlla se le porte 5000, 5060, 5061 sono libere
- Modifica le porte nell'applicazione se necessario

## Configurazione TLS

Per abilitare il supporto TLS (SIPS):

1. Vai su http://localhost:5000/certificates
2. Genera certificati server
3. Il server TLS sarà automaticamente attivo sulla porta 5061

## Test del Sistema

1. Accedi alla dashboard: http://localhost:5000
2. Vai alla sezione certificati per configurare TLS
3. Configura un client SIP per testare la connettività
4. Effettua chiamate di test alle estensioni 999-996 per analisi qualità