# Configurazione Gateway Welcome Italia per VoIP Quality Monitor

## Configurazione Gateway Originale (CLI)

```bash
# Profilo SIP Welcome Italia
set voip sip profile create welcome
set voip sip profile welcome registrar proxy01-sip.welcomeitalia.it
set voip sip profile welcome codec-type g729 alaw
set voip sip profile welcome sip-domain welcomeitalia.it
set voip sip profile welcome caller-rewrite yes
set voip sip profile welcome dtmf rfc4733
set voip sip profile welcome registration-retry-timer 57
set voip sip profile welcome registration-expiry 3600
set voip sip profile welcome rfc3325-header preferred
set voip sip profile welcome enable-prack supported

# Trunk SIP Welcome Italia
set voip trunk sip create welcome1
set voip trunk sip welcome1 username 08631780017
set voip trunk sip welcome1 authentication-password WLC40808S117L1
set voip trunk sip welcome1 codec-type g729 alaw 
set voip trunk sip welcome1 authentication-username s08631780017
set voip trunk sip welcome1 display-name 08631780017
set voip trunk sip welcome1 dtmf rfc4733
set voip trunk sip welcome1 sip-profile welcome
set voip trunk sip welcome1 enable yes
```

## Configurazione Equivalente per VoIP Quality Monitor

### 1. Configurazione come Registrar Locale

Per configurare la webapp come registrar per il gateway:

```bash
# Nel gateway, modifica il registrar per puntare alla webapp
set voip sip profile welcome registrar <IP_WEBAPP>:5060
set voip sip profile welcome sip-domain voip-monitor.local

# Mantieni la configurazione trunk esistente
# Il gateway si registrerà alla webapp invece che direttamente a Welcome
```

### 2. Configurazione Webapp (Automatica)

La webapp è già configurata per:
- **Porta SIP**: 5060 (UDP/TCP) e 5061 (TLS)
- **Domini supportati**: voip-monitor.local
- **Codec supportati**: G.711 (alaw/ulaw), G.729, G.722, Opus
- **DTMF**: RFC4733 supportato nell'analisi RTP
- **Registrazione**: Timeout 3600 secondi (compatibile)

### 3. Schema di Configurazione

```
[Gateway] ----SIP----> [VoIP Monitor] ----SIP----> [Welcome Italia]
                            ^
                            |
                       [Dashboard Web]
                       [Analisi Qualità]
```

### 4. Configurazione Dettagliata Gateway

```bash
# Modifica profilo SIP per usare webapp come proxy
set voip sip profile welcome registrar <IP_WEBAPP>:5060
set voip sip profile welcome outbound-proxy <IP_WEBAPP>:5060
set voip sip profile welcome sip-domain voip-monitor.local

# Mantieni configurazione codec
set voip sip profile welcome codec-type g729 alaw

# Mantieni impostazioni DTMF e timer
set voip sip profile welcome dtmf rfc4733
set voip sip profile welcome registration-expiry 3600

# Opzionale: Abilita TLS per sicurezza
set voip sip profile welcome transport-protocol tls
set voip sip profile welcome registrar <IP_WEBAPP>:5061
```

### 5. Parametri di Rete

- **IP Webapp**: Inserisci l'IP del server dove gira la webapp
- **Porte**: 
  - 5060 per SIP standard (UDP/TCP)
  - 5061 per SIP sicuro (TLS)
- **Dominio**: voip-monitor.local (configurabile nella webapp)

### 6. Configurazione Avanzata per Monitoraggio

Per abilitare il monitoraggio qualità completo:

```bash
# Abilita RTP proxy mode per analisi packet
set voip sip profile welcome rtp-proxy-mode yes

# Configura QoS per analisi qualità
set voip qos dscp-marking ef
set voip qos packet-loss-concealment yes
```

## Comandi Webapp Equivalenti

I parametri del gateway vengono mappati automaticamente nella webapp:

| Parametro Gateway | Gestione Webapp |
|------------------|-----------------|
| `registrar` | Configurazione SIP server porta 5060/5061 |
| `codec-type` | Rilevamento automatico da RTP payload |
| `dtmf rfc4733` | Analisi DTMF nei packet RTP |
| `registration-expiry` | Timer registrazione (3600s default) |
| `authentication` | Gestione credenziali SIP |
| `caller-rewrite` | Parsing header SIP From/To |

## Test della Configurazione

1. **Avvia webapp**: `python app_simple.py`
2. **Modifica gateway**: Cambia registrar verso IP webapp
3. **Verifica registrazione**: Dashboard -> Dispositivi Registrati
4. **Test chiamate**: Estensioni 999-996 per analisi qualità
5. **Monitoraggio**: Dashboard real-time per metriche qualità

## Troubleshooting

- **Gateway non si registra**: Verifica IP e porta webapp
- **Codec non riconosciuto**: Webapp rileva automaticamente da RTP
- **Chiamate non passano**: Controlla routing SIP nella webapp
- **Qualità non misurata**: Verifica che RTP passi attraverso webapp