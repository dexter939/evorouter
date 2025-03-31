# EvoRouter R4 OS - Repository GitHub

Benvenuto nel repository GitHub ufficiale di EvoRouter R4 OS! Questo repository contiene il codice sorgente completo del sistema operativo personalizzato per router EvoRouter R4 con interfaccia web avanzata, centralino telefonico integrato e funzionalità complete di rete.

## Come utilizzare questo repository

### Installazione di EvoRouter R4 OS

Per installare il sistema su un dispositivo EvoRouter R4, puoi utilizzare uno dei nostri script di installazione semplificati:

```bash
# Installazione solo sistema
curl -sSL https://raw.githubusercontent.com/dexter939/evorouter/main/install_evorouter.sh | sudo bash

# Installazione completa (sistema + centralino)
curl -sSL https://raw.githubusercontent.com/dexter939/evorouter/main/install_evorouter_complete.sh | sudo bash
```

Per istruzioni dettagliate, consulta il file [INSTALL.md](INSTALL.md).

### Per sviluppatori

Se desideri contribuire allo sviluppo o fare modifiche al sistema:

1. **Clona il repository**:
   ```bash
   git clone https://github.com/dexter939/evorouter.git
   cd evorouter
   ```

2. **Imposta l'ambiente di sviluppo**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Avvia il server di sviluppo**:
   ```bash
   python main.py
   ```

4. **Accedi all'interfaccia web** tramite http://localhost:5000 con credenziali predefinite:
   - Username: admin
   - Password: admin123

## Documentazione

- [README.md](README.md) - Panoramica generale del progetto
- [INSTALL.md](INSTALL.md) - Guida dettagliata all'installazione
- [API_INTEGRATION.md](API_INTEGRATION.md) - Documentazione API
- [HARDWARE.md](HARDWARE.md) - Specifiche hardware e funzionalità
- [CONTRIBUTING.md](CONTRIBUTING.md) - Linee guida per i contributi

## Struttura del progetto

```
evorouter/
├── app.py              # Configurazione app Flask
├── main.py             # Entry point
├── models.py           # Modelli database
├── config.py           # Configurazioni
├── routes/             # Route e controller
├── forms/              # Definizioni form
├── templates/          # Template UI
├── static/             # Asset statici
├── utils/              # Funzioni di utilità
└── tests/              # Test unitari
```

## Flusso di lavoro per lo sviluppo

Per contribuire al progetto, segui queste linee guida:

1. **Crea un fork** di questo repository
2. **Crea un branch** per la tua funzionalità (`git checkout -b feature/amazing-feature`)
3. **Commit** delle tue modifiche (`git commit -m 'Aggiunta nuova funzionalità'`)
4. **Push** al branch (`git push origin feature/amazing-feature`)
5. **Crea una Pull Request** verso questo repository

## Politica di rilascio

Utilizziamo il versionamento semantico (SemVer) per tutte le release:
- **Versioni major (X.0.0)** contengono cambiamenti incompatibili con versioni precedenti
- **Versioni minor (0.X.0)** contengono nuove funzionalità retrocompatibili
- **Versioni patch (0.0.X)** contengono correzioni di bug retrocompatibili

## Licenza

Questo progetto è rilasciato sotto licenza [MIT](LICENSE).

## Riconoscimenti

Un ringraziamento speciale a tutti i contributori che hanno reso possibile questo progetto!

---

### Note per chi utilizza GitHub per la prima volta

Se sei nuovo con GitHub e Git, ecco alcune risorse utili:
- [GitHub Guides](https://guides.github.com/) 
- [Git Documentation](https://git-scm.com/doc)
- [Pro Git Book](https://git-scm.com/book/en/v2) (disponibile anche in italiano)