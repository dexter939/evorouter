# EvoRouter R4 OS v1.4.0

Sistema operativo personalizzato per router EvoRouter R4 con interfaccia web avanzata, centralino integrato e funzionalità VPN.

## Novità della versione 1.4.0

- **Script di Installazione Semplificati**: Nuovi script `install_evorouter.sh` e `install_evorouter_complete.sh` per installazione automatizzata
- **Installazione All-in-One**: Opzione per installare sistema e centralino in un unico passaggio
- **Rilevamento Automatico del Sistema**: Configurazione ottimizzata per diverse distribuzioni Debian
- **Aggiornamento Documentazione**: Aggiornamento delle guide di installazione con i nuovi metodi semplificati
- **Compatibilità Migliorata**: Verifica e correzione delle dipendenze durante l'installazione

## Novità della versione 1.3.0

- **Installazione Centralino Migliorata**: Nuovo sistema di installazione guidata del centralino telefonico accessibile dall'interfaccia web
- **API Stato Centralino**: Nuovo endpoint API per verificare lo stato di FreeSWITCH con informazioni dettagliate
- **Dashboard Potenziata**: Visualizzazione in tempo reale dello stato del centralino con monitoraggio automatico
- **Documentazione Aggiornata**: Guida all'installazione e documentazione API aggiornate per riflettere le nuove funzionalità
- **Stabilità Generale**: Numerosi miglioramenti di stabilità e prestazioni in tutto il sistema

## Novità della versione 1.2.0

- **Miglioramento Firewall**: Riorganizzazione della sezione firewall con spostamento UPnP nella sezione appropriata
- **Sicurezza Migliorata**: Implementazione completa della protezione CSRF nei form
- **QoS Ottimizzato**: Correzione dei problemi nella funzionalità Quality of Service 
- **Supporto IPv6**: Supporto completo per IPv6 in tutte le componenti di rete
- **UPnP Avanzato**: Miglioramento della funzionalità UPnP con status e gestione avanzata

## Caratteristiche

- **Interfaccia Web Responsive**: Gestione completa del dispositivo tramite interfaccia web intuitiva
- **Centralino Integrato**: Gestione chiamate, interni, voicemail, IVR e molto altro
- **Server VPN Integrato**: Supporto per OpenVPN con gestione client
- **Diagnostica Avanzata**: Strumenti completi per diagnostica di rete e sistema
- **API RESTful**: Per integrazione con sistemi esterni e automazione
- **Gestione Remota**: Possibilità di gestire tutti i dispositivi da un server centrale

## Stack Tecnologico

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap, JavaScript, Chart.js, Feather Icons
- **Componenti di Sistema**: PBX, OpenVPN, iptables
- **Hardware**: EvoRouter R4 (MT7988a)

## Installazione

### Installazione Rapida

```bash
# Installazione solo sistema
curl -sSL https://raw.githubusercontent.com/dexter939/evorouter/main/install_evorouter.sh | sudo bash

# Installazione completa (sistema + centralino)
curl -sSL https://raw.githubusercontent.com/dexter939/evorouter/main/install_evorouter_complete.sh | sudo bash
```

Per istruzioni dettagliate sull'installazione, consulta [INSTALL.md](INSTALL.md).

## Specifiche Hardware

Per dettagli sulle specifiche hardware e le funzionalità del dispositivo EvoRouter R4, consulta [HARDWARE.md](HARDWARE.md).

## Integrazione API

Per documentazione sulle API disponibili, consulta [API_INTEGRATION.md](API_INTEGRATION.md).

## Licenza

Questo progetto è rilasciato sotto licenza [MIT](LICENSE).

## Contributi

I contributi sono benvenuti! Per favore, leggi [CONTRIBUTING.md](CONTRIBUTING.md) per dettagli su come contribuire al progetto.