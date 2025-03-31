# Guida all'Installazione del Router OS per EvoRouter R4

Questa guida spiega come installare il Router OS sviluppato per EvoRouter R4, un sistema operativo completo per la gestione del router e del centralino telefonico integrato.

## Prerequisiti
- EvoRouter R4
- Scheda microSD (minimo 16GB consigliati)
- Alimentatore compatibile (12V, 2A minimo)
- Cavo Ethernet
- Computer con lettore di schede SD
- Connessione Internet per il download dei pacchetti

## Installazione Semplificata (Raccomandata)

Per semplificare l'installazione, abbiamo preparato degli script automatizzati che gestiscono l'intero processo:

### Opzione 1: Installazione Solo Sistema
```bash
# Scarica lo script di installazione
wget https://raw.githubusercontent.com/dexter939/evorouter/main/install_evorouter.sh

# Rendi lo script eseguibile
chmod +x install_evorouter.sh

# Esegui lo script
sudo ./install_evorouter.sh
```

### Opzione 2: Installazione Completa (Sistema + Centralino)
```bash
# Scarica lo script di installazione completa
wget https://raw.githubusercontent.com/dexter939/evorouter/main/install_evorouter_complete.sh

# Rendi lo script eseguibile
chmod +x install_evorouter_complete.sh

# Esegui lo script
sudo ./install_evorouter_complete.sh
```

Lo script di installazione completa automatizza tutti i passaggi descritti sotto, inclusa l'installazione del centralino FreeSWITCH.

## Installazione Manuale
Se preferisci installare manualmente il sistema o desideri maggiore controllo sul processo di installazione, segui i passaggi dettagliati qui sotto.

### 1. Preparazione dell'ambiente sul dispositivo

1. Crea una directory sul dispositivo dove verrà installato il software:
   ```
   mkdir -p /opt/evorouter
   ```

2. Installa le dipendenze di sistema necessarie:
   ```
   apt update
   apt install -y python3 python3-pip python3-venv nginx curl wget unzip
   ```

> **Nota**: A differenza delle versioni precedenti, FreeSWITCH non viene più installato automaticamente con apt. Il software include ora un sistema di installazione guidata accessibile dall'interfaccia web.

### 2. Configurazione dell'ambiente Python

1. Crea un ambiente virtuale:
   ```
   cd /opt/evorouter
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Installa le dipendenze Python:
   ```
   pip install flask flask-login flask-jwt-extended flask-sqlalchemy flask-wtf gunicorn psutil psycopg2-binary email-validator
   ```

### 3. Copia dei file del progetto

Esistono due modi per trasferire i file del progetto al dispositivo:

#### Metodo 1: Download diretto dal repository GitHub (se disponibile)
```
cd /opt/evorouter
git clone https://github.com/tuo-username/evorouter .
```

#### Metodo 2: Trasferimento manuale
1. Scarica l'archivio ZIP del progetto da Replit
2. Trasferisci il file sul dispositivo usando SCP:
   ```
   scp evorouter.zip user@evorouter-device:/tmp/
   ```
3. Sul dispositivo, estrai i file:
   ```
   cd /opt/evorouter
   unzip /tmp/evorouter.zip
   ```

### 4. Configurazione del database

1. Inizializza il database:
   ```
   cd /opt/evorouter
   source venv/bin/activate
   python create_admin.py
   ```

### 5. Configurazione di Nginx

1. Crea un file di configurazione per Nginx:
   ```
   nano /etc/nginx/sites-available/evorouter
   ```

2. Aggiungi questa configurazione:
   ```
   server {
       listen 80;
       server_name _;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

3. Abilita il sito:
   ```
   ln -s /etc/nginx/sites-available/evorouter /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx
   ```

### 6. Configurazione del servizio systemd

1. Crea un file di servizio:
   ```
   nano /etc/systemd/system/evorouter.service
   ```

2. Aggiungi questa configurazione:
   ```
   [Unit]
   Description=EvoRouter R4 OS
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/opt/evorouter
   ExecStart=/opt/evorouter/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 3 main:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. Abilita e avvia il servizio:
   ```
   systemctl enable evorouter.service
   systemctl start evorouter.service
   ```

### 7. Verifica dell'installazione

1. Verifica che il servizio sia in esecuzione:
   ```
   systemctl status evorouter.service
   ```

2. Accedi all'interfaccia web:
   - Apri un browser e visita `http://indirizzo-ip-del-dispositivo/`
   - Accedi con le credenziali predefinite:
     - Username: admin
     - Password: admin123

### 8. Installazione guidata del Centralino (FreeSWITCH)

Dopo aver effettuato l'accesso all'interfaccia web, puoi installare il centralino telefonico seguendo questi passaggi:

1. Dalla dashboard, trova la sezione "Servizi di Sistema" e individua la riga "Centralino (FreeSWITCH)"
2. Fai clic sull'icona di download accanto al servizio
3. Nella pagina di installazione, scegli tra:
   - **Installazione Standard**: utilizza i pacchetti precompilati (consigliata)
   - **Installazione da Sorgente**: compila FreeSWITCH dai sorgenti (richiede più tempo)
4. Fai clic su "Avvia Installazione" e attendi il completamento del processo
5. Al termine, il sistema ti reindirizzerà alla dashboard dove potrai verificare lo stato del centralino

> **Importante**: L'installazione da sorgente può richiedere fino a 30-60 minuti, a seconda delle prestazioni del dispositivo.

## Risoluzione dei problemi

Se riscontri problemi durante l'installazione, puoi controllare i log:
```
journalctl -u evorouter.service -f
```

Per problemi relativi a Nginx:
```
journalctl -u nginx.service -f
```

Per problemi relativi all'installazione o al funzionamento del Centralino (FreeSWITCH):
```
# Controlla lo stato del servizio
systemctl status freeswitch

# Visualizza i log di FreeSWITCH
tail -f /var/log/freeswitch/freeswitch.log
```

## Note di sicurezza

- Si consiglia vivamente di cambiare la password dell'utente admin al primo accesso!
- L'API del sistema è protetta tramite autenticazione JWT. Puoi generare e gestire i token API dalla sezione impostazioni.
- Il sistema è pronto per l'uso in rete protetta. Per l'esposizione su Internet, si raccomanda di configurare HTTPS tramite Let's Encrypt.