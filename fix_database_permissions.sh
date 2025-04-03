#!/bin/bash
#
# Script per risolvere problemi comuni di permessi del database SQLite
# Questo script è utile quando appare l'errore "unable to open database file"
# Versione: 1.0
# Data: 03/04/2025
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

# Verifica se lo script è eseguito come root
if [ "$(id -u)" != "0" ]; then
   print_message "error" "Questo script deve essere eseguito come root (sudo)!"
   exit 1
fi

# Definizione del percorso di installazione
INSTALL_DIR="/opt/evorouter"

# Verifica che EvoRouter sia già installato
if [ ! -d "$INSTALL_DIR" ]; then
    print_message "error" "EvoRouter R4 OS non sembra essere installato in $INSTALL_DIR."
    print_message "info" "Esegui prima lo script di installazione install_evorouter.sh."
    exit 1
fi

print_message "info" "#############################################"
print_message "info" "##                                         ##"
print_message "info" "##  RIPARAZIONE DATABASE                  ##"
print_message "info" "##  EvoRouter R4 OS                       ##"
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "info" "Questo script risolverà i problemi comuni di permessi del database SQLite."

# Arresta il servizio prima di intervenire
print_message "info" "Arresto del servizio EvoRouter..."
systemctl stop evorouter.service

# Backup del database esistente (se presente)
print_message "info" "Creazione del backup del database (se presente)..."
mkdir -p $INSTALL_DIR/database_backup
if [ -d "$INSTALL_DIR/instance" ]; then
    cp -f $INSTALL_DIR/instance/*.db $INSTALL_DIR/database_backup/ 2>/dev/null
    if [ $? -eq 0 ]; then
        print_message "success" "Backup del database creato con successo."
    else
        print_message "warning" "Nessun file di database trovato per il backup."
    fi
fi

# Estrai il percorso del database dalla configurazione
print_message "info" "Individuazione del percorso del database..."
if [ -f "$INSTALL_DIR/.env" ]; then
    source $INSTALL_DIR/.env
    if [[ "$DATABASE_URL" == sqlite* ]]; then
        # Estrai il percorso del file database dall'URL
        DB_FILE_PATH=${DATABASE_URL#sqlite:///}
        
        # Se è un percorso relativo, lo rendiamo assoluto
        if [[ "$DB_FILE_PATH" != /* ]]; then
            DB_FILE_PATH="$INSTALL_DIR/$DB_FILE_PATH"
        fi
        
        print_message "info" "Percorso del database SQLite: $DB_FILE_PATH"
        
        # Crea la directory se non esiste
        DB_DIR=$(dirname "$DB_FILE_PATH")
        print_message "info" "Creazione della directory $DB_DIR (se non esiste)..."
        mkdir -p "$DB_DIR"
        chmod -R 777 "$DB_DIR"
        
        # Se il database esiste, correggi i permessi
        if [ -f "$DB_FILE_PATH" ]; then
            print_message "info" "Correzione dei permessi del file database..."
            chmod 666 "$DB_FILE_PATH"
            print_message "success" "Permessi corretti sul file $DB_FILE_PATH"
        else
            print_message "warning" "Il file database non esiste. Sarà creato al riavvio dell'applicazione."
        fi
    else
        print_message "info" "Non stai utilizzando SQLite, ma un altro tipo di database: $DATABASE_URL"
        print_message "info" "Questo script è principalmente per la risoluzione di problemi con SQLite."
    fi
else
    print_message "warning" "File di configurazione .env non trovato. Utilizzo il percorso predefinito."
    # Crea la directory instance se non esiste
    mkdir -p $INSTALL_DIR/instance
    chmod -R 777 $INSTALL_DIR/instance
    print_message "success" "Permessi corretti sulla directory instance."
fi

# Correggi i permessi della directory instance comunque
print_message "info" "Correzione dei permessi della directory instance..."
mkdir -p $INSTALL_DIR/instance
chmod -R 777 $INSTALL_DIR/instance
print_message "success" "Permessi corretti sulla directory instance."

# Correggi l'ownership dei file
print_message "info" "Impostazione dell'ownership corretta..."
NGINX_USER=$(grep -E "^user" /etc/nginx/nginx.conf | awk '{print $2}' | sed 's/;$//')
if [ -z "$NGINX_USER" ]; then
    NGINX_USER="www-data"  # Valore predefinito
fi

chown -R $NGINX_USER:$NGINX_USER $INSTALL_DIR/instance
print_message "success" "Ownership impostata a $NGINX_USER per la directory instance."

# Modifica il file di servizio systemd per creare la directory instance all'avvio
print_message "info" "Aggiornamento del file di servizio systemd..."
cat > /etc/systemd/system/evorouter.service << EOF
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

# Ricarica la configurazione di systemd
print_message "info" "Ricaricamento della configurazione di systemd..."
systemctl daemon-reload

# Tenta di inizializzare il database tramite Python
print_message "info" "Tentativo di inizializzazione del database..."
cd $INSTALL_DIR
source venv/bin/activate

python -c "from app import app, db; app.app_context().push(); db.create_all()"
if [ $? -ne 0 ]; then
    print_message "warning" "Errore durante l'inizializzazione del database. Per ulteriori dettagli, esegui il comando manualmente."
    print_message "info" "Puoi tentare manualmente con: cd $INSTALL_DIR && source venv/bin/activate && python -c 'from app import app, db; app.app_context().push(); db.create_all()'"
else
    print_message "success" "Database inizializzato con successo!"
fi

# Tenta di creare l'admin se necessario
if [ ! -f "$INSTALL_DIR/instance/evorouter.db" ] || [ ! -s "$INSTALL_DIR/instance/evorouter.db" ]; then
    print_message "info" "Tentativo di creazione dell'utente admin..."
    python create_admin.py
    if [ $? -ne 0 ]; then
        print_message "warning" "Errore durante la creazione dell'utente admin. Per ulteriori dettagli, esegui il comando manualmente."
        print_message "info" "Puoi tentare manualmente con: cd $INSTALL_DIR && source venv/bin/activate && python create_admin.py"
    else
        print_message "success" "Utente admin creato con successo!"
    fi
fi

# Riavvio del servizio
print_message "info" "Riavvio del servizio EvoRouter..."
systemctl restart evorouter.service

# Verifica lo stato in modo più dettagliato
sleep 5
if ! systemctl is-active --quiet evorouter.service; then
    print_message "warning" "Il servizio EvoRouter non è stato avviato correttamente."
    print_message "info" "Consulta i log per maggiori dettagli: journalctl -u evorouter.service -n 50"
else
    print_message "success" "Il servizio EvoRouter è stato riavviato con successo!"
fi

# Verifica finale dell'applicazione web
print_message "info" "Verifica dell'applicazione web..."
sleep 5
if curl -s --max-time 10 http://127.0.0.1/ | grep -q "EvoRouter"; then
    print_message "success" "L'applicazione web è attiva e raggiungibile!"
else
    print_message "warning" "L'applicazione web non risponde correttamente. Verificare i log:"
    print_message "info" "journalctl -u evorouter.service -n 50"
    print_message "info" "journalctl -u nginx.service -n 20"
fi

# Informazioni finali
print_message "success" "##############################################"
print_message "success" "Riparazione del database completata!"
print_message "success" "##############################################"
print_message "info" ""
print_message "info" "Se continui a riscontrare problemi con il database, prova a:"
print_message "info" "1. Verificare che il file .env contenga il percorso corretto del database"
print_message "info" "2. Assicurarsi che l'utente che esegue l'applicazione abbia accesso alla directory"
print_message "info" "3. Verificare la presenza di errori nei log di sistema"
print_message "info" ""
print_message "info" "Per visualizzare i log del sistema:"
print_message "info" "- Logs di EvoRouter: journalctl -u evorouter.service -f"
print_message "info" "- Logs di Nginx: journalctl -u nginx.service -f"

exit 0