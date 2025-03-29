# Guida all'Installazione del Router OS per EvoRouter R4

Questa guida spiega come installare il Router OS sviluppato per EvoRouter R4.

## Prerequisiti
- EvoRouter R4
- Scheda microSD (minimo 8GB)
- Alimentatore compatibile
- Cavo Ethernet
- Computer con lettore di schede SD

## Passi per l'installazione

### 1. Preparazione dell'ambiente sul dispositivo

1. Crea una directory sul dispositivo dove verrà installato il software:
   ```
   mkdir -p /opt/evorouter
   ```

2. Installa le dipendenze di sistema necessarie:
   ```
   apt update
   apt install -y python3 python3-pip python3-venv nginx
   apt install -y freeswitch freeswitch-mod-console freeswitch-mod-sofia freeswitch-mod-event-socket
   ```

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

## Risoluzione dei problemi

Se riscontri problemi durante l'installazione, puoi controllare i log:
```
journalctl -u evorouter.service -f
```

Per problemi relativi a Nginx:
```
journalctl -u nginx.service -f
```

## Note di sicurezza

Si consiglia vivamente di cambiare la password dell'utente admin al primo accesso!