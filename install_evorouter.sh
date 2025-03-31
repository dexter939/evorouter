#!/bin/bash
#
# Script di installazione automatica per EvoRouter R4 OS
# Questo script automatizza l'intero processo di installazione del sistema operativo
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
chmod 777 $INSTALL_DIR/instance

# In caso di SQLite, verifica che l'utente corrente possa scrivere nella directory
if [[ "$DATABASE_URL" == sqlite* ]]; then
    # Imposta i permessi corretti per la directory dell'applicazione
    chmod -R 755 $INSTALL_DIR
    chmod -R 777 $INSTALL_DIR/instance
    print_message "info" "Permessi impostati per database SQLite in $INSTALL_DIR/instance"
fi

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