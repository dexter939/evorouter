#!/bin/bash
#
# Script di installazione completa per EvoRouter R4 OS con FreeSWITCH
# Questo script automatizza l'intero processo di installazione del sistema e del centralino
# Versione: 1.0
# Data: 31/03/2025
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
print_message "info" "##  INSTALLAZIONE COMPLETA EvoRouter R4 OS ##"
print_message "info" "##  SISTEMA + CENTRALINO                   ##"
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "info" "Questo script installerà:"
print_message "info" "1. EvoRouter R4 OS (sistema completo)"
print_message "info" "2. FreeSWITCH (centralino telefonico)"
print_message "info" ""
print_message "info" "Questo processo potrebbe richiedere 15-30 minuti."

# Definizione del percorso di installazione
INSTALL_DIR="/opt/evorouter"
NGINX_CONF="/etc/nginx/sites-available/evorouter"
SERVICE_FILE="/etc/systemd/system/evorouter.service"

# Chiedi conferma prima di continuare
read -p "Vuoi procedere con l'installazione completa? (s/n): " confirm
if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    print_message "info" "Installazione annullata."
    exit 0
fi

# PARTE 1: Installazione sistema EvoRouter R4 OS
print_message "info" ""
print_message "info" "PARTE 1: INSTALLAZIONE SISTEMA EVOROUTER R4 OS"
print_message "info" "============================================"

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
apt-get install -y python3 python3-pip python3-venv python3-miniupnpc nginx curl wget unzip git gnupg2 lsb-release ca-certificates apt-transport-https
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
pip install flask flask-login flask-jwt-extended flask-sqlalchemy flask-wtf gunicorn psutil psycopg2-binary email-validator miniupnpc
check_command "Impossibile installare le dipendenze Python."

# Passo 3: Download e installazione dei file di EvoRouter
print_message "info" "Passo 3: Download e installazione dei file di EvoRouter..."

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

# Esegui create_admin.py con messaggi di errore dettagliati
python create_admin.py 2> db_error.log
if [ $? -ne 0 ]; then
    print_message "error" "Impossibile inizializzare il database. Consultare il file $INSTALL_DIR/db_error.log per i dettagli dell'errore."
    cat db_error.log
    print_message "info" "Puoi tentare di risolvere il problema manualmente e poi eseguire: cd $INSTALL_DIR && source venv/bin/activate && python create_admin.py"
    exit 1
else
    print_message "success" "Database inizializzato con successo!"
fi

# Passo 5: Configurazione di Nginx
print_message "info" "Passo 5: Configurazione di Nginx..."

# Creazione del file di configurazione
print_message "info" "Creazione del file di configurazione Nginx..."
cat > $NGINX_CONF << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
check_command "Impossibile creare il file di configurazione Nginx."

# Abilita il sito e verifica la configurazione
print_message "info" "Abilitazione del sito web in Nginx..."
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
nginx -t
check_command "La configurazione di Nginx non è valida."

# Riavvio di Nginx
systemctl restart nginx
check_command "Impossibile riavviare Nginx."

# Passo 6: Configurazione del servizio systemd
print_message "info" "Passo 6: Configurazione del servizio systemd..."

# Creazione del file di servizio
print_message "info" "Creazione del file di servizio systemd..."
cat > $SERVICE_FILE << EOF
[Unit]
Description=EvoRouter R4 OS
After=network.target

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 3 main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
check_command "Impossibile creare il file di servizio systemd."

# Ricarica la configurazione di systemd
systemctl daemon-reload
check_command "Impossibile ricaricare la configurazione di systemd."

# Abilita e avvia il servizio
print_message "info" "Avvio del servizio EvoRouter..."
systemctl enable evorouter.service
systemctl start evorouter.service
check_command "Impossibile avviare il servizio EvoRouter."

# PARTE 2: Installazione di FreeSWITCH
print_message "info" ""
print_message "info" "PARTE 2: INSTALLAZIONE CENTRALINO (FREESWITCH)"
print_message "info" "============================================"

# Determinazione della versione di Debian
DEBIAN_VERSION=$(lsb_release -cs)
print_message "info" "Rilevata distribuzione: $DEBIAN_VERSION"

# Aggiunta del repository FreeSWITCH
print_message "info" "Aggiunta del repository ufficiale di FreeSWITCH..."

# Rimozione di eventuali repository precedenti per evitare duplicati
if [ -f /etc/apt/sources.list.d/freeswitch.list ]; then
    rm /etc/apt/sources.list.d/freeswitch.list
fi

# Selezione del repository appropriato in base alla versione di Debian
case $DEBIAN_VERSION in
    "bullseye")
        # Debian 11 Bullseye
        print_message "info" "Configurazione per Debian 11 Bullseye..."
        wget -O - https://files.freeswitch.org/repo/deb/debian-release/fsstretch-archive-keyring.asc | apt-key add -
        echo "deb http://files.freeswitch.org/repo/deb/debian-release/ bullseye main" > /etc/apt/sources.list.d/freeswitch.list
        ;;
    "bookworm")
        # Debian 12 Bookworm
        print_message "info" "Configurazione per Debian 12 Bookworm..."
        wget -O - https://files.freeswitch.org/repo/deb/debian-release/fsstretch-archive-keyring.asc | apt-key add -
        echo "deb http://files.freeswitch.org/repo/deb/debian-release/ bookworm main" > /etc/apt/sources.list.d/freeswitch.list
        ;;
    "buster")
        # Debian 10 Buster
        print_message "info" "Configurazione per Debian 10 Buster..."
        wget -O - https://files.freeswitch.org/repo/deb/debian-release/fsstretch-archive-keyring.asc | apt-key add -
        echo "deb http://files.freeswitch.org/repo/deb/debian-release/ buster main" > /etc/apt/sources.list.d/freeswitch.list
        ;;
    *)
        # Configurazione predefinita per altre distribuzioni
        print_message "warning" "Versione di Debian non riconosciuta: $DEBIAN_VERSION. Utilizzo della configurazione per Debian 11 Bullseye..."
        wget -O - https://files.freeswitch.org/repo/deb/debian-release/fsstretch-archive-keyring.asc | apt-key add -
        echo "deb http://files.freeswitch.org/repo/deb/debian-release/ bullseye main" > /etc/apt/sources.list.d/freeswitch.list
        ;;
esac

# Aggiornamento dopo l'aggiunta del repository
print_message "info" "Aggiornamento delle liste dei pacchetti dopo l'aggiunta del repository..."
apt-get update

# Installazione di FreeSWITCH e dei moduli necessari
print_message "info" "Installazione di FreeSWITCH e dei moduli necessari..."
apt-get install -y freeswitch freeswitch-meta-all || {
    print_message "warning" "Impossibile installare il pacchetto completo. Tentativo con moduli singoli..."
    
    # Tentativo di installazione dei moduli principali singolarmente
    apt-get install -y freeswitch freeswitch-mod-console freeswitch-mod-sofia freeswitch-mod-voicemail \
    freeswitch-mod-loopback freeswitch-mod-commands freeswitch-mod-conference freeswitch-mod-db \
    freeswitch-mod-dptools freeswitch-mod-hash freeswitch-mod-esf freeswitch-mod-dialplan-xml \
    freeswitch-mod-sndfile freeswitch-mod-native-file freeswitch-mod-local-stream freeswitch-mod-tone-stream \
    freeswitch-mod-lua freeswitch-mod-spandsp || {
        print_message "error" "Installazione di FreeSWITCH fallita."
        print_message "warning" "Il sistema EvoRouter R4 OS è stato installato correttamente, ma FreeSWITCH non è stato installato."
        print_message "info" "Puoi installare manualmente FreeSWITCH in seguito dall'interfaccia web."
    }
}

# Configurazione del servizio FreeSWITCH
if command -v freeswitch >/dev/null 2>&1; then
    print_message "info" "Configurazione del servizio FreeSWITCH..."
    systemctl enable freeswitch
    systemctl start freeswitch
    
    # Verifica dello stato finale di FreeSWITCH
    if systemctl is-active --quiet freeswitch; then
        print_message "success" "FreeSWITCH è stato installato e avviato con successo!"
    else
        print_message "warning" "FreeSWITCH è stato installato ma il servizio non risulta attivo."
        print_message "info" "Verifica lo stato del servizio con: systemctl status freeswitch"
    fi
else
    print_message "warning" "FreeSWITCH non risulta installato correttamente."
fi

# Passo 7: Verifica dell'installazione complessiva
print_message "info" ""
print_message "info" "Passo 7: Verifica dell'installazione complessiva..."

# Verifica che il servizio EvoRouter sia in esecuzione
if systemctl is-active --quiet evorouter.service; then
    print_message "success" "Il servizio EvoRouter è in esecuzione!"
else
    print_message "warning" "Il servizio EvoRouter sembra non essere in esecuzione."
    print_message "info" "Verifica lo stato con: systemctl status evorouter.service"
fi

# Ottieni l'indirizzo IP per il login
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# Informazioni finali
print_message "success" "##############################################"
print_message "success" "Installazione completa di EvoRouter R4 OS!"
if command -v freeswitch >/dev/null 2>&1; then
    print_message "success" "FreeSWITCH è stato installato con successo!"
fi
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
if command -v freeswitch >/dev/null 2>&1; then
    print_message "info" "Informazioni sul centralino FreeSWITCH:"
    print_message "info" "- Configurazione in: /etc/freeswitch/"
    print_message "info" "- Log in: /var/log/freeswitch/"
    print_message "info" "- Per accedere alla console: fs_cli"
    print_message "info" ""
fi
print_message "info" "Per visualizzare i log del sistema:"
print_message "info" "- Logs di EvoRouter: journalctl -u evorouter.service -f"
print_message "info" "- Logs di Nginx: journalctl -u nginx.service -f"
if command -v freeswitch >/dev/null 2>&1; then
    print_message "info" "- Logs di FreeSWITCH: tail -f /var/log/freeswitch/freeswitch.log"
fi
print_message "info" ""
print_message "info" "Grazie per aver installato EvoRouter R4 OS!"

exit 0