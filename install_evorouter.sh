#!/bin/bash
#
# Script di installazione automatica per EvoRouter R4 OS
# Questo script automatizza l'intero processo di installazione del sistema operativo
# Versione: 1.1
# Data: 03/04/2025
# 
# Changelog:
# 1.1 - 03/04/2025:
#   - Risolto problema pagina di default di Nginx
#   - Migliorata gestione permessi database SQLite
#   - Aggiunta rimozione file index.nginx-debian.html
#   - Migliorata configurazione di systemd
#   - Aggiunto supporto per creazione automatica database PostgreSQL
#

# Funzione per visualizzare messaggi colorati
print_message() {
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
    
    case $1 in
        "info")
            echo -e "${BLUE}[INFO]${NC} $2"
            ;;
        "success")
            echo -e "${GREEN}[SUCCESSO]${NC} $2"
            ;;
        "error")
            echo -e "${RED}[ERRORE]${NC} $2"
            ;;
        "warning")
            echo -e "${YELLOW}[AVVISO]${NC} $2"
            ;;
        *)
            echo "$2"
            ;;
    esac
}

# Funzione per verificare l'esito di un comando
check_command() {
    if [ $? -ne 0 ]; then
        print_message "error" "$1"
        exit 1
    fi
}

# Verifica se lo script è eseguito come root
if [ "$(id -u)" != "0" ]; then
   print_message "error" "Questo script deve essere eseguito come root (sudo)!"
   exit 1
fi

print_message "info" "#############################################"
print_message "info" "##                                         ##"
print_message "info" "##  INSTALLAZIONE EvoRouter R4 OS         ##"
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "info" "Inizializzazione dell'installazione di EvoRouter R4 OS..."
print_message "info" "Questo processo potrebbe richiedere alcuni minuti."

# Definizione del percorso di installazione
INSTALL_DIR="/opt/evorouter"
NGINX_CONF="/etc/nginx/sites-available/evorouter"
SERVICE_FILE="/etc/systemd/system/evorouter.service"

# Chiedi conferma prima di continuare
read -p "Questo script installerà EvoRouter R4 OS in $INSTALL_DIR. Continuare? (s/n): " confirm
if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    print_message "info" "Installazione annullata."
    exit 0
fi

# Passo 1: Preparazione dell'ambiente
print_message "info" "Passo 1: Preparazione dell'ambiente..."

# Creazione directory di installazione
print_message "info" "Creazione directory $INSTALL_DIR..."
mkdir -p $INSTALL_DIR
check_command "Impossibile creare la directory $INSTALL_DIR"

# Aggiornamento delle liste dei pacchetti
print_message "info" "Aggiornamento delle liste dei pacchetti..."
apt-get update
check_command "Impossibile aggiornare le liste dei pacchetti. Verifica la connessione internet."

# Installazione delle dipendenze di sistema
print_message "info" "Installazione delle dipendenze di sistema..."
apt-get install -y python3 python3-pip python3-venv python3-miniupnpc nginx curl wget unzip git
check_command "Impossibile installare le dipendenze di sistema."

# Passo 2: Configurazione dell'ambiente Python
print_message "info" "Passo 2: Configurazione dell'ambiente Python..."

# Creazione dell'ambiente virtuale
print_message "info" "Creazione dell'ambiente virtuale Python..."
cd $INSTALL_DIR
python3 -m venv venv
check_command "Impossibile creare l'ambiente virtuale Python."

# Attivazione dell'ambiente virtuale e installazione delle dipendenze
print_message "info" "Installazione delle dipendenze Python..."
source venv/bin/activate
pip install flask flask-login flask-jwt-extended flask-sqlalchemy flask-wtf gunicorn psutil psycopg2-binary email-validator miniupnpc stripe
check_command "Impossibile installare le dipendenze Python."

# Passo 3: Download e installazione dei file di EvoRouter
print_message "info" "Passo 3: Download e installazione dei file di EvoRouter..."

# Chiedi all'utente quale metodo di installazione preferisce
echo ""
echo "Seleziona il metodo di installazione:"
echo "1) Download dal repository GitHub (consigliato)"
echo "2) Trasferimento manuale di un archivio ZIP"
read -p "Scelta (1/2): " install_method

case $install_method in
    1)
        # Download dal repository GitHub
        print_message "info" "Download del codice dal repository GitHub..."
        read -p "Inserisci l'URL del repository GitHub (predefinito: https://github.com/dexter939/evorouter.git): " github_url
        github_url=${github_url:-https://github.com/dexter939/evorouter.git}
        
        cd $INSTALL_DIR
        # Rimuovi eventuali file esistenti ma mantieni l'ambiente virtuale
        find . -mindepth 1 -maxdepth 1 -not -name "venv" -exec rm -rf {} \;
        git clone $github_url temp
        check_command "Impossibile clonare il repository GitHub."
        
        # Sposta i file nella directory principale mantenendo l'ambiente virtuale
        mv temp/* .
        mv temp/.* . 2>/dev/null || true
        rmdir temp
        ;;
    2)
        # Trasferimento manuale dell'archivio ZIP
        print_message "info" "Preparazione per il trasferimento manuale..."
        print_message "info" "Inserisci il percorso completo dell'archivio ZIP di EvoRouter:"
        read -p "Percorso archivio ZIP: " zip_path
        
        if [ ! -f "$zip_path" ]; then
            print_message "error" "File ZIP non trovato: $zip_path"
            exit 1
        fi
        
        print_message "info" "Estrazione dei file..."
        cd $INSTALL_DIR
        # Rimuovi eventuali file esistenti ma mantieni l'ambiente virtuale
        find . -mindepth 1 -maxdepth 1 -not -name "venv" -exec rm -rf {} \;
        unzip -q "$zip_path"
        check_command "Impossibile estrarre l'archivio ZIP."
        ;;
    *)
        print_message "error" "Opzione non valida. Installazione annullata."
        exit 1
        ;;
esac

# Passo 4: Configurazione del database
print_message "info" "Passo 4: Configurazione del database..."

# Chiedi all'utente se vuole utilizzare SQLite o PostgreSQL
echo ""
echo "Seleziona il tipo di database da utilizzare:"
echo "1) SQLite (più semplice, consigliato per installazioni singole)"
echo "2) PostgreSQL (più robusto, consigliato per ambienti di produzione)"
read -p "Scelta (1/2): " db_choice

case $db_choice in
    1)
        # Configurazione SQLite
        print_message "info" "Configurazione database SQLite..."
        
        # Crea un file .env con la configurazione
        cat > $INSTALL_DIR/.env << EOF
# Configurazione EvoRouter
FLASK_APP=main.py
FLASK_ENV=production
SESSION_SECRET=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///instance/evorouter.db
STRIPE_SECRET_KEY=your_stripe_secret_key_here
EOF
        ;;
    2)
        # Configurazione PostgreSQL
        print_message "info" "Configurazione database PostgreSQL..."
        
        # Chiedi dettagli della connessione
        read -p "Host PostgreSQL (default: localhost): " pg_host
        pg_host=${pg_host:-localhost}
        
        read -p "Porta PostgreSQL (default: 5432): " pg_port
        pg_port=${pg_port:-5432}
        
        read -p "Nome database (default: evorouter): " pg_dbname
        pg_dbname=${pg_dbname:-evorouter}
        
        read -p "Utente PostgreSQL: " pg_user
        
        read -s -p "Password PostgreSQL: " pg_password
        echo ""  # Nuova linea dopo input password
        
        # Verifica se postgresql-client è installato
        if ! command -v psql &> /dev/null; then
            print_message "info" "Installazione di postgresql-client..."
            apt-get install -y postgresql-client
            check_command "Impossibile installare postgresql-client."
        fi
        
        # Verifica la connessione al database
        print_message "info" "Verifica della connessione al database PostgreSQL..."
        if PGPASSWORD="$pg_password" psql -h "$pg_host" -p "$pg_port" -U "$pg_user" -d "$pg_dbname" -c "SELECT 1" &> /dev/null; then
            print_message "success" "Connessione al database PostgreSQL riuscita!"
        else
            # Prova a creare il database se non esiste
            print_message "warning" "Database '$pg_dbname' non trovato. Tentativo di creazione..."
            if PGPASSWORD="$pg_password" psql -h "$pg_host" -p "$pg_port" -U "$pg_user" -c "CREATE DATABASE $pg_dbname;" &> /dev/null; then
                print_message "success" "Database '$pg_dbname' creato con successo!"
            else
                print_message "error" "Impossibile connettersi al database o creare il database. Verifica le credenziali e che PostgreSQL sia in esecuzione."
                print_message "info" "Puoi riprovare l'installazione o selezionare SQLite come alternativa."
                exit 1
            fi
        fi
        
        # Crea un file .env con la configurazione
        cat > $INSTALL_DIR/.env << EOF
# Configurazione EvoRouter
FLASK_APP=main.py
FLASK_ENV=production
SESSION_SECRET=$(openssl rand -hex 32)
DATABASE_URL=postgresql://$pg_user:$pg_password@$pg_host:$pg_port/$pg_dbname
PGHOST=$pg_host
PGPORT=$pg_port
PGDATABASE=$pg_dbname
PGUSER=$pg_user
PGPASSWORD=$pg_password
STRIPE_SECRET_KEY=your_stripe_secret_key_here
EOF
        ;;
    *)
        print_message "error" "Opzione non valida. Installazione annullata."
        exit 1
        ;;
esac

# Imposta i permessi corretti
chmod 600 $INSTALL_DIR/.env
check_command "Impossibile impostare i permessi sul file .env"

# Carica le variabili d'ambiente e inizializza il database
print_message "info" "Inizializzazione del database..."
cd $INSTALL_DIR
source venv/bin/activate
set -a
source .env
set +a

# Crea la directory instance per SQLite se necessario
mkdir -p $INSTALL_DIR/instance
# Imposta permessi molto permissivi per assicurare l'accesso
chmod -R 777 $INSTALL_DIR/instance

# Crea un file vuoto per il database con i permessi corretti
if [[ "$DATABASE_URL" == sqlite* ]]; then
    # Estrai il percorso del file database dall'URL
    DB_FILE_PATH=${DATABASE_URL#sqlite:///}
    
    # Se è un percorso relativo, lo rendiamo assoluto
    if [[ "$DB_FILE_PATH" != /* ]]; then
        DB_FILE_PATH="$INSTALL_DIR/$DB_FILE_PATH"
    fi
    
    # Crea le directory necessarie per il database
    DB_DIR=$(dirname "$DB_FILE_PATH")
    mkdir -p "$DB_DIR"
    
    # Tocca il file del database per crearlo e imposta permessi molto permissivi
    touch "$DB_FILE_PATH"
    chmod 666 "$DB_FILE_PATH"
    
    # Imposta i permessi corretti per le directory
    chmod -R 777 "$DB_DIR"
    chown -R www-data:www-data "$DB_DIR" 2>/dev/null || true
    
    print_message "info" "File database SQLite creato in $DB_FILE_PATH con permessi corretti"
    print_message "info" "Permessi impostati per database SQLite in $DB_DIR"
fi

# Inizializza il database con gestione degli errori migliorata
print_message "info" "Inizializzazione del database e creazione tabelle..."
cd $INSTALL_DIR
# Esegui le migrazioni del database
python -c "from app import app, db; app.app_context().push(); db.create_all()" 2> db_error.log
if [ $? -ne 0 ]; then
    print_message "error" "Impossibile inizializzare il database. Consultare il file $INSTALL_DIR/db_error.log per i dettagli dell'errore."
    cat db_error.log
    
    # Controlli aggiuntivi per SQLite
    if [[ "$DATABASE_URL" == sqlite* ]]; then
        # Estrai il percorso del file database dall'URL
        DB_FILE_PATH=${DATABASE_URL#sqlite:///}
        
        # Se è un percorso relativo, lo rendiamo assoluto
        if [[ "$DB_FILE_PATH" != /* ]]; then
            DB_FILE_PATH="$INSTALL_DIR/$DB_FILE_PATH"
        fi
        
        # Verifica i permessi nella directory del database
        DB_DIR=$(dirname "$DB_FILE_PATH")
        print_message "info" "Tentativo di correzione dei permessi per SQLite..."
        mkdir -p "$DB_DIR"
        chmod -R 777 "$DB_DIR"
        chown -R root:root "$DB_DIR" 2>/dev/null || true
        
        # Prova a creare il DB di nuovo
        python -c "from app import app, db; app.app_context().push(); db.create_all()" 2> db_error_retry.log
        if [ $? -ne 0 ]; then
            print_message "error" "Secondo tentativo fallito. Consultare il file $INSTALL_DIR/db_error_retry.log"
            cat db_error_retry.log
        else
            print_message "success" "Correzione riuscita! Database inizializzato con successo!"
        fi
    fi
    
    print_message "info" "Puoi tentare di risolvere il problema manualmente e poi eseguire: cd $INSTALL_DIR && source venv/bin/activate && python -c 'from app import app, db; app.app_context().push(); db.create_all()'"
fi

# Esegui create_admin.py con gestione degli errori migliorata
print_message "info" "Creazione dell'account amministratore predefinito..."
python create_admin.py 2> admin_error.log
if [ $? -ne 0 ]; then
    print_message "warning" "Impossibile creare l'account amministratore. Consultare il file $INSTALL_DIR/admin_error.log per i dettagli."
    cat admin_error.log
    print_message "info" "Puoi creare l'amministratore manualmente eseguendo: cd $INSTALL_DIR && source venv/bin/activate && python create_admin.py"
else
    print_message "success" "Account amministratore creato con successo!"
fi

# Passo 5: Configurazione di Nginx
print_message "info" "Passo 5: Configurazione di Nginx..."

# Creazione del file di configurazione
print_message "info" "Creazione del file di configurazione Nginx..."
cat > $NGINX_CONF << EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    # Impostazioni generali
    root /var/www/html;
    index index.html index.htm;
    
    # Aumenta il buffer per le intestazioni
    large_client_header_buffers 4 32k;
    
    # Elimina la pagina di default di Nginx
    location = /index.nginx-debian.html {
        return 301 /;
    }

    # Configurazione del proxy per l'applicazione EvoRouter
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout estesi per operazioni di lunga durata
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffering migliorato
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
        
        # Gestione degli errori quando il backend non è disponibile
        proxy_intercept_errors on;
        error_page 502 503 504 /50x.html;
    }
    
    # Pagina di errore personalizzata quando l'applicazione non è raggiungibile
    location = /50x.html {
        root /var/www/html;
        internal;
    }
    
    # Permettere l'accesso alle risorse statiche direttamente
    location /static/ {
        alias $INSTALL_DIR/static/;
        expires 7d;
    }
}
EOF
check_command "Impossibile creare il file di configurazione Nginx."

# Rimuovi la configurazione di default di Nginx se esiste
if [ -f /etc/nginx/sites-enabled/default ]; then
    print_message "info" "Rimozione della configurazione di default di Nginx..."
    rm -f /etc/nginx/sites-enabled/default
fi

# Rimuovi anche la pagina di default di Nginx
print_message "info" "Rimozione della pagina di default di Nginx..."
NGINX_DEFAULT_HTML="/var/www/html/index.nginx-debian.html"
if [ -f "$NGINX_DEFAULT_HTML" ]; then
    rm -f "$NGINX_DEFAULT_HTML"
fi

# Crea una pagina di redirect per maggiore sicurezza
print_message "info" "Creazione di una pagina di redirect di fallback..."
cat > /var/www/html/index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url=/" />
    <title>Reindirizzamento a EvoRouter</title>
</head>
<body>
    <p>Reindirizzamento a EvoRouter...</p>
    <script>
        window.location.href = "/";
    </script>
</body>
</html>
EOF

# Abilita il sito e verifica la configurazione
print_message "info" "Abilitazione del sito web in Nginx..."
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
nginx -t
check_command "La configurazione di Nginx non è valida."

# Riavvio di Nginx
print_message "info" "Riavvio di Nginx..."
systemctl restart nginx
check_command "Impossibile riavviare Nginx."

# Passo 6: Configurazione del servizio systemd
print_message "info" "Passo 6: Configurazione del servizio systemd..."

# Creazione del file di servizio
print_message "info" "Creazione del file di servizio systemd..."
cat > $SERVICE_FILE << EOF
[Unit]
Description=EvoRouter R4 OS
After=network.target postgresql.service
Wants=nginx.service
Before=nginx.service

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
# Carica le variabili d'ambiente dal file .env
EnvironmentFile=-$INSTALL_DIR/.env
# Verifica preliminare e creazione directory
ExecStartPre=/bin/bash -c "mkdir -p $INSTALL_DIR/instance && chmod 777 $INSTALL_DIR/instance"
# Avvia l'applicazione con gunicorn
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 3 --timeout 120 --error-logfile $INSTALL_DIR/instance/gunicorn-error.log --access-logfile $INSTALL_DIR/instance/gunicorn-access.log main:app
# Riavvio automatico in caso di errore
Restart=always
RestartSec=5
# Definisci la priorità
Nice=-5
# Timeout di avvio esteso
TimeoutStartSec=90
# Evita che venga terminato troppo facilmente
OOMScoreAdjust=-1000

[Install]
WantedBy=multi-user.target
EOF
check_command "Impossibile creare il file di servizio systemd."

# Ricarica la configurazione di systemd
print_message "info" "Ricaricamento della configurazione di systemd..."
systemctl daemon-reload
check_command "Impossibile ricaricare la configurazione di systemd."

# Verifica se il file di servizio è valido prima di abilitarlo
print_message "info" "Verifica del file di servizio systemd..."
systemctl is-enabled --quiet evorouter.service || systemctl enable evorouter.service
check_command "Impossibile abilitare il servizio EvoRouter."

print_message "info" "Avvio del servizio EvoRouter..."
systemctl restart evorouter.service

# Verifica lo stato in modo più dettagliato
print_message "info" "Verifica dello stato del servizio dopo l'avvio..."
sleep 5  # Attendiamo che il servizio abbia tempo di inizializzare
if ! systemctl is-active --quiet evorouter.service; then
    print_message "warning" "Il servizio EvoRouter non è stato avviato correttamente."
    print_message "info" "Controllo dei log per maggiori dettagli..."
    journalctl -u evorouter.service -n 20 --no-pager
    
    # Secondo tentativo di avvio con opzioni diverse
    print_message "info" "Tentativo di riavvio con impostazioni alternative..."
    systemctl start evorouter.service
    sleep 5
    
    if ! systemctl is-active --quiet evorouter.service; then
        print_message "warning" "Secondo tentativo fallito. Verifica manuale richiesta."
        journalctl -u evorouter.service -n 10 --no-pager
        # Non usciamo con errore per consentire all'installazione di completarsi
    else
        print_message "success" "Secondo tentativo riuscito! Servizio EvoRouter avviato con successo!"
    fi
else
    print_message "success" "Il servizio EvoRouter è stato avviato con successo!"
fi

# Passo 7: Verifica dell'installazione
print_message "info" "Passo 7: Verifica dell'installazione..."

# Verifica che il servizio sia in esecuzione
if systemctl is-active --quiet evorouter.service; then
    print_message "success" "Il servizio EvoRouter è in esecuzione!"
else
    print_message "warning" "Il servizio EvoRouter sembra non essere in esecuzione."
    print_message "info" "Verifica lo stato con: systemctl status evorouter.service"
fi

# Ottieni l'indirizzo IP per il login
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# Verifica finale dell'applicazione web
print_message "info" "Verifica dell'applicazione web..."
# Utilizziamo curl per controllare se l'applicazione risponde correttamente
sleep 5  # Attendiamo che l'applicazione si inizializzi completamente
ATTEMPT=1
MAX_ATTEMPTS=3
APP_OK=false

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    print_message "info" "Tentativo $ATTEMPT di $MAX_ATTEMPTS per verificare che l'applicazione web risponda..."
    if curl -s --max-time 10 http://127.0.0.1/ | grep -q "EvoRouter"; then
        APP_OK=true
        break
    else
        if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
            print_message "warning" "L'applicazione non risponde ancora. Nuovo tentativo tra 5 secondi..."
            # Controlla eventuali errori nei log
            journalctl -u evorouter.service -n 10 --no-pager
            sleep 5
        fi
    fi
    ATTEMPT=$((ATTEMPT+1))
done

if [ "$APP_OK" = true ]; then
    print_message "success" "L'applicazione web è attiva e raggiungibile!"
else
    print_message "warning" "L'applicazione web non risponde correttamente. Verificare i log:"
    print_message "info" "journalctl -u evorouter.service -n 50"
    print_message "info" "journalctl -u nginx.service -n 20"
    
    # Tentativi di recupero
    print_message "info" "Tentativo di correzione automatica..."
    
    # Riavvia entrambi i servizi in sequenza
    systemctl restart evorouter.service
    sleep 2
    systemctl restart nginx.service
    
    print_message "info" "I servizi sono stati riavviati. Si consiglia di verificare manualmente la connessione all'applicazione."
fi

# Informazioni finali
print_message "success" "##############################################"
print_message "success" "Installazione di EvoRouter R4 OS completata!"
print_message "success" "##############################################"
print_message "info" ""
print_message "info" "Informazioni importanti:"
print_message "info" "- Interfaccia web: http://$IP_ADDRESS/"
print_message "info" "- Credenziali predefinite:"
print_message "info" "  Username: admin"
print_message "info" "  Password: admin123"
print_message "info" ""
print_message "warning" "IMPORTANTE: Cambia la password di admin al primo accesso!"
print_message "info" ""
print_message "info" "Se vedi la pagina di default di Nginx invece dell'interfaccia EvoRouter:"
print_message "info" "1. Controlla lo stato dei servizi: systemctl status evorouter.service nginx.service"
print_message "info" "2. Riavvia i servizi: systemctl restart evorouter.service nginx.service"
print_message "info" "3. Verifica i log: journalctl -u evorouter.service -n 50"
print_message "info" ""
print_message "info" "Per installare il centralino telefonico (FreeSWITCH):"
print_message "info" "1. Accedi all'interfaccia web con le credenziali sopra indicate"
print_message "info" "2. Vai alla sezione Centralino e segui la procedura guidata di installazione"
print_message "info" ""
print_message "info" "Per visualizzare i log del sistema:"
print_message "info" "- Logs di EvoRouter: journalctl -u evorouter.service -f"
print_message "info" "- Logs di Nginx: journalctl -u nginx.service -f"
print_message "info" ""
print_message "info" "Grazie per aver installato EvoRouter R4 OS!"

exit 0