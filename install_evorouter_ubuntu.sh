#!/bin/bash
#
# Script di installazione automatica per EvoRouter R4 OS su Ubuntu/Debian
# Questo script automatizza l'intero processo di installazione del sistema operativo
# Versione: 1.2
# Data: 03/04/2025
# 
# Changelog:
# 1.2 - 03/04/2025:
#   - Aggiunto supporto specifico per Ubuntu
#   - Rilevamento automatico del gestore pacchetti (apt/apt-get)
#   - Migliorato rilevamento della distribuzione
#   - Verifiche aggiuntive di compatibilità
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

# Funzione per installare pacchetti a seconda della distro
install_packages() {
    local packages="$1"
    
    if command -v apt &> /dev/null; then
        # Ubuntu moderno o derivati, usa apt
        apt update
        apt install -y $packages
    elif command -v apt-get &> /dev/null; then
        # Debian o Ubuntu più vecchio, usa apt-get
        apt-get update
        apt-get install -y $packages
    else
        print_message "error" "Impossibile trovare un gestore di pacchetti compatibile (apt o apt-get)."
        print_message "error" "Questo script è progettato per sistemi Ubuntu/Debian."
        exit 1
    fi
    
    check_command "Impossibile installare i pacchetti: $packages"
}

# Verifica se lo script è eseguito come root
if [ "$(id -u)" != "0" ]; then
   print_message "error" "Questo script deve essere eseguito come root (sudo)!"
   exit 1
fi

# Rileva la distribuzione
DISTRO="Sconosciuta"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$NAME $VERSION_ID"
fi

print_message "info" "#############################################"
print_message "info" "##                                         ##"
print_message "info" "##  INSTALLAZIONE EvoRouter R4 OS         ##"
print_message "info" "##  Distribuzione: $DISTRO                 "
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "info" "Inizializzazione dell'installazione di EvoRouter R4 OS..."
print_message "info" "Questo processo potrebbe richiedere alcuni minuti."

# Verifiche sulla compatibilità
print_message "info" "Verifica della compatibilità del sistema..."
compatible=true

# Verifica Python3
if ! command -v python3 &> /dev/null; then
    print_message "warning" "Python3 non è installato. Verrà installato automaticamente."
fi

# Verifica versione minima di Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
    PYTHON_MIN_VERSION="3.8"
    
    if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$PYTHON_MIN_VERSION" ]; then
        print_message "warning" "Versione di Python rilevata ($PYTHON_VERSION) inferiore alla minima raccomandata ($PYTHON_MIN_VERSION)."
        print_message "warning" "Potrebbero verificarsi problemi di compatibilità."
        compatible=false
    fi
fi

# Verifica requisiti hardware minimi
MEM_TOTAL=$(free -m | awk '/^Mem:/{print $2}')
DISK_FREE=$(df -m /opt | awk 'NR==2 {print $4}')

if [ "$MEM_TOTAL" -lt 2000 ]; then
    print_message "warning" "Memoria RAM disponibile (${MEM_TOTAL}MB) inferiore ai 2GB raccomandati."
    compatible=false
fi

if [ "$DISK_FREE" -lt 2000 ]; then
    print_message "warning" "Spazio su disco disponibile (${DISK_FREE}MB) inferiore ai 2GB raccomandati."
    compatible=false
fi

if [ "$compatible" = false ]; then
    print_message "warning" "Il sistema potrebbe non soddisfare tutti i requisiti minimi raccomandati."
    read -p "Vuoi continuare comunque con l'installazione? (s/n): " continue_anyway
    if [ "$continue_anyway" != "s" ] && [ "$continue_anyway" != "S" ]; then
        print_message "info" "Installazione annullata."
        exit 0
    fi
fi

# Definizione del percorso di installazione
INSTALL_DIR="/opt/evorouter"
NGINX_CONF="/etc/nginx/sites-available/evorouter"
SERVICE_FILE="/etc/systemd/system/evorouter.service"

# Rileva il web server predefinito (nginx o apache2)
USE_NGINX=true
if ! command -v nginx &> /dev/null && command -v apache2 &> /dev/null; then
    print_message "warning" "Nginx non è installato, ma è stato rilevato Apache2."
    read -p "Vuoi utilizzare Apache2 invece di installare Nginx? (s/n): " use_apache
    if [ "$use_apache" = "s" ] || [ "$use_apache" = "S" ]; then
        USE_NGINX=false
    fi
fi

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

# Installazione delle dipendenze di sistema
print_message "info" "Installazione delle dipendenze di sistema..."
if [ "$USE_NGINX" = true ]; then
    install_packages "python3 python3-pip python3-venv curl wget unzip git nginx"
else
    install_packages "python3 python3-pip python3-venv curl wget unzip git"
fi

# Installa miniupnpc se disponibile
if apt-cache search python3-miniupnpc | grep -q python3-miniupnpc; then
    install_packages "python3-miniupnpc"
fi

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
pip install --upgrade pip
pip install flask flask-login flask-jwt-extended flask-sqlalchemy flask-wtf gunicorn psutil psycopg2-binary email-validator stripe
check_command "Impossibile installare le dipendenze Python principali."

# Tenta di installare miniupnpc tramite pip se necessario
if ! apt-cache search python3-miniupnpc | grep -q python3-miniupnpc; then
    print_message "info" "Installazione di miniupnpc tramite pip..."
    pip install miniupnpc || print_message "warning" "Impossibile installare miniupnpc. Alcune funzionalità UPnP potrebbero non essere disponibili."
fi

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
        
        # Verifica se postgresql-client è installato
        if ! command -v psql &> /dev/null; then
            print_message "info" "Installazione di postgresql-client..."
            install_packages "postgresql-client"
        fi
        
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
    
    # Determina l'utente del server web
    if [ "$USE_NGINX" = true ] && command -v nginx &> /dev/null; then
        WEB_USER=$(grep -E "^user" /etc/nginx/nginx.conf | awk '{print $2}' | sed 's/;$//')
        # Impostazione predefinita se non trovato
        if [ -z "$WEB_USER" ]; then
            if [ -f /etc/debian_version ]; then
                WEB_USER="www-data"  # Utente predefinito per Debian/Ubuntu
            else
                WEB_USER="nginx"  # Utente predefinito per altre distro
            fi
        fi
    elif command -v apache2 &> /dev/null; then
        if [ -f /etc/debian_version ]; then
            WEB_USER="www-data"  # Utente predefinito per Apache su Debian/Ubuntu
        else
            WEB_USER="apache"  # Utente predefinito per altre distro
        fi
    else
        WEB_USER="www-data"  # Fallback su www-data
    fi
    
    chown -R $WEB_USER:$WEB_USER "$DB_DIR" 2>/dev/null || true
    
    print_message "info" "File database SQLite creato in $DB_FILE_PATH con permessi corretti"
    print_message "info" "Permessi impostati per database SQLite in $DB_DIR per l'utente $WEB_USER"
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
else
    print_message "success" "Database inizializzato con successo!"
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

# Passo 5: Configurazione del server web
if [ "$USE_NGINX" = true ]; then
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
    
    # Abilita il sito e verifica la configurazione
    print_message "info" "Abilitazione del sito e verifica della configurazione..."
    if [ -d "/etc/nginx/sites-enabled" ]; then
        # Debian/Ubuntu style
        ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
        
        # Rimuovi la configurazione di default se esiste
        if [ -f /etc/nginx/sites-enabled/default ]; then
            print_message "info" "Rimozione della configurazione di default di Nginx..."
            rm -f /etc/nginx/sites-enabled/default
        fi
    else
        # CentOS/RHEL style
        print_message "info" "Directory sites-enabled non trovata. Utilizzo la configurazione principale."
        echo "include $NGINX_CONF;" >> /etc/nginx/nginx.conf
    fi
    
    # Rimuovi anche la pagina di default di Nginx
    print_message "info" "Rimozione della pagina di default di Nginx..."
    NGINX_DEFAULT_HTML="/var/www/html/index.nginx-debian.html"
    if [ -f "$NGINX_DEFAULT_HTML" ]; then
        rm -f "$NGINX_DEFAULT_HTML"
    fi
    
    # Crea una pagina di redirect per maggiore sicurezza
    print_message "info" "Creazione di una pagina di redirect di fallback..."
    mkdir -p /var/www/html
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
    
    # Verifica la configurazione di Nginx
    nginx -t
    if [ $? -ne 0 ]; then
        print_message "error" "La configurazione di Nginx non è valida. Verifica il file $NGINX_CONF."
        exit 1
    fi
    
    # Riavvia Nginx
    print_message "info" "Riavvio di Nginx..."
    if command -v systemctl &> /dev/null; then
        systemctl restart nginx
    else
        service nginx restart
    fi
    check_command "Impossibile riavviare Nginx."
elif command -v apache2 &> /dev/null; then
    print_message "info" "Passo 5: Configurazione di Apache2..."
    
    # Installa il modulo proxy se necessario
    if ! apache2ctl -M 2>/dev/null | grep -q "proxy_module"; then
        print_message "info" "Installazione dei moduli proxy di Apache..."
        install_packages "libapache2-mod-proxy-html libxml2-dev"
        a2enmod proxy proxy_http proxy_balancer lbmethod_byrequests
    fi
    
    # Creazione del file di configurazione
    print_message "info" "Creazione del file di configurazione Apache..."
    APACHE_CONF="/etc/apache2/sites-available/evorouter.conf"
    cat > $APACHE_CONF << EOF
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html

    ErrorLog \${APACHE_LOG_DIR}/error.log
    CustomLog \${APACHE_LOG_DIR}/access.log combined

    # Configurazione del proxy per l'applicazione EvoRouter
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    # Permettere l'accesso alle risorse statiche direttamente
    Alias /static $INSTALL_DIR/static
    <Directory $INSTALL_DIR/static>
        Require all granted
    </Directory>
</VirtualHost>
EOF
    check_command "Impossibile creare il file di configurazione Apache."
    
    # Abilita il sito e disabilita il default
    print_message "info" "Abilitazione del sito..."
    a2dissite 000-default
    a2ensite evorouter
    
    # Verifica la configurazione di Apache
    apache2ctl configtest
    if [ $? -ne 0 ]; then
        print_message "error" "La configurazione di Apache non è valida. Verifica il file $APACHE_CONF."
        exit 1
    fi
    
    # Riavvia Apache
    print_message "info" "Riavvio di Apache..."
    if command -v systemctl &> /dev/null; then
        systemctl restart apache2
    else
        service apache2 restart
    fi
    check_command "Impossibile riavviare Apache."
else
    print_message "warning" "Nessun server web (Nginx o Apache) trovato. L'applicazione sarà accessibile solo sulla porta 5000."
    print_message "info" "Si consiglia di installare Nginx o Apache per una configurazione completa."
fi

# Passo 6: Configurazione del servizio systemd
print_message "info" "Passo 6: Configurazione del servizio systemd..."

# Verifica se systemd è disponibile
if ! command -v systemctl &> /dev/null; then
    print_message "warning" "Systemd non è disponibile su questo sistema. Non è possibile configurare il servizio automatico."
    print_message "info" "Per avviare l'applicazione manualmente, esegui: cd $INSTALL_DIR && source venv/bin/activate && gunicorn --bind 127.0.0.1:5000 --workers 3 main:app"
else
    # Creazione del file di servizio
    print_message "info" "Creazione del file di servizio systemd..."
    cat > $SERVICE_FILE << EOF
[Unit]
Description=EvoRouter R4 OS
After=network.target
Wants=nginx.service

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
# Carica le variabili d'ambiente dal file .env
EnvironmentFile=-$INSTALL_DIR/.env
ExecStartPre=/bin/bash -c "mkdir -p $INSTALL_DIR/instance && chmod 777 $INSTALL_DIR/instance"
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 3 --timeout 120 main:app
Restart=always
RestartSec=5
# Aggiungi un tempo di avvio più lungo per garantire che l'app abbia tempo di inizializzare
TimeoutStartSec=90

[Install]
WantedBy=multi-user.target
EOF
    check_command "Impossibile creare il file di servizio systemd."
    
    # Aggiorna systemd e avvia il servizio
    print_message "info" "Avvio del servizio EvoRouter..."
    systemctl daemon-reload
    systemctl enable evorouter.service
    systemctl restart evorouter.service
    check_command "Impossibile avviare il servizio EvoRouter."
    
    # Verifica che il servizio sia attivo
    sleep 5
    if systemctl is-active --quiet evorouter.service; then
        print_message "success" "Il servizio EvoRouter è attivo e funzionante!"
    else
        print_message "warning" "Il servizio EvoRouter potrebbe non essere avviato correttamente. Controllare i log con: journalctl -u evorouter.service"
    fi
fi

# Passo 7: Verifica dell'installazione
print_message "info" "Passo 7: Verifica finale dell'installazione..."

# Determina l'indirizzo IP per la connessione
IP_ADDRESS=$(hostname -I | awk '{print $1}')
if [ -z "$IP_ADDRESS" ]; then
    IP_ADDRESS="localhost"
fi

# Verifica se il servizio web è in ascolto
print_message "info" "Verifica della connettività all'applicazione web..."
sleep 5
if command -v curl &> /dev/null; then
    if curl -s --max-time 10 http://127.0.0.1:5000/ | grep -q "EvoRouter"; then
        print_message "success" "L'applicazione web è raggiungibile su http://$IP_ADDRESS/"
    else
        print_message "warning" "L'applicazione web non sembra rispondere correttamente. Consulta i log per maggiori dettagli."
        if command -v systemctl &> /dev/null; then
            print_message "info" "Puoi controllare i log con: journalctl -u evorouter.service -n 50"
        fi
    fi
else
    print_message "info" "Curl non è installato. Non è possibile verificare la connettività all'applicazione web."
    print_message "info" "Prova ad accedere a http://$IP_ADDRESS/ dal tuo browser."
fi

# Riepilogo e istruzioni finali
print_message "success" "##############################################"
print_message "success" "Installazione di EvoRouter R4 OS completata!"
print_message "success" "##############################################"
print_message "info" ""
print_message "info" "Informazioni di accesso:"
print_message "info" "- Interfaccia web: http://$IP_ADDRESS/"
print_message "info" "- Credenziali di default:"
print_message "info" "  Username: admin"
print_message "info" "  Password: admin123"
print_message "info" ""
print_message "warning" "IMPORTANTE: Cambia immediatamente la password predefinita!"
print_message "info" ""
print_message "info" "Per visualizzare i log del sistema:"
print_message "info" "- Logs di EvoRouter: journalctl -u evorouter.service -f"
if [ "$USE_NGINX" = true ]; then
    print_message "info" "- Logs di Nginx: journalctl -u nginx.service -f"
elif command -v apache2 &> /dev/null; then
    print_message "info" "- Logs di Apache: tail -f /var/log/apache2/error.log"
fi
print_message "info" ""
print_message "info" "Posizione dei file di EvoRouter: $INSTALL_DIR"
print_message "info" "File di configurazione database: $INSTALL_DIR/.env"
print_message "info" ""
print_message "info" "Grazie per aver installato EvoRouter R4 OS!"

exit 0