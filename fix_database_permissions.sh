#!/bin/bash
#
# Script per risolvere i problemi di permessi del database SQLite in EvoRouter R4 OS
# Versione: 1.1
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
   print_message "info" "Esegui: sudo $0"
   exit 1
fi

print_message "info" "#############################################"
print_message "info" "##                                         ##"
print_message "info" "##  RIPARAZIONE DATABASE EVOROUTER R4 OS  ##"
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""

# Definizione delle variabili dei percorsi
INSTALL_DIR="/opt/evorouter"
DB_DIR="$INSTALL_DIR/instance"
DB_FILE="$DB_DIR/evorouter.db"
DB_ERROR_LOG="$INSTALL_DIR/db_error.log"
BACKUP_DIR="$INSTALL_DIR/db_backups"
WEB_USER="www-data"  # L'utente del web server (www-data per Nginx/Apache su Debian/Ubuntu)
APP_USER=$(stat -c '%U' "$INSTALL_DIR" 2>/dev/null || echo "root")

# Verifica la distribuzione
if [ -f /etc/os-release ]; then
    . /etc/os-release
    print_message "info" "Sistema operativo rilevato: $NAME $VERSION_ID"
    
    # Rileva l'utente del web server
    if [ "$ID" == "centos" ] || [ "$ID" == "fedora" ] || [ "$ID" == "rhel" ]; then
        WEB_USER="apache"
    fi
fi

print_message "info" "Verifica dei permessi e dell'installazione del database..."

# Verifica se il database esiste
if [ ! -f "$DB_FILE" ]; then
    print_message "warning" "Il file del database non esiste: $DB_FILE"
    
    # Verifica se la directory instance esiste
    if [ ! -d "$DB_DIR" ]; then
        print_message "info" "Creazione della directory instance..."
        mkdir -p "$DB_DIR"
        if [ $? -ne 0 ]; then
            print_message "error" "Impossibile creare la directory del database: $DB_DIR"
            exit 1
        fi
    fi
    
    # Crea un file vuoto per il database
    print_message "info" "Creazione del file di database vuoto..."
    touch "$DB_FILE"
    if [ $? -ne 0 ]; then
        print_message "error" "Impossibile creare il file di database: $DB_FILE"
        exit 1
    fi
else
    print_message "success" "File del database trovato: $DB_FILE"
    
    # Crea una directory di backup se non esiste
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
    fi
    
    # Crea un backup del database esistente
    BACKUP_FILE="$BACKUP_DIR/evorouter_$(date +%Y%m%d_%H%M%S).db"
    print_message "info" "Creazione di un backup del database in $BACKUP_FILE..."
    cp "$DB_FILE" "$BACKUP_FILE"
    if [ $? -eq 0 ]; then
        print_message "success" "Backup del database creato con successo."
    else
        print_message "warning" "Impossibile creare un backup del database."
    fi
fi

# Verifica chi è il proprietario del file di database
CURRENT_OWNER=$(stat -c '%U:%G' "$DB_FILE" 2>/dev/null)
print_message "info" "Proprietario attuale del database: $CURRENT_OWNER"

# Verifica i permessi attuali
CURRENT_PERMS=$(stat -c '%a' "$DB_FILE" 2>/dev/null)
print_message "info" "Permessi attuali del database: $CURRENT_PERMS"

# Cambia il proprietario del file di database
print_message "info" "Impostazione del proprietario del database a $WEB_USER..."
chown $WEB_USER:$WEB_USER "$DB_FILE"
if [ $? -eq 0 ]; then
    print_message "success" "Proprietario del database modificato con successo."
else
    print_message "error" "Impossibile modificare il proprietario del database."
fi

# Cambia i permessi del file di database
print_message "info" "Impostazione dei permessi di lettura/scrittura per il database..."
chmod 664 "$DB_FILE"
if [ $? -eq 0 ]; then
    print_message "success" "Permessi del database modificati con successo."
else
    print_message "error" "Impossibile modificare i permessi del database."
fi

# Cambia il proprietario dell'intera directory instance
print_message "info" "Impostazione del proprietario della directory del database a $WEB_USER..."
chown -R $WEB_USER:$WEB_USER "$DB_DIR"
if [ $? -eq 0 ]; then
    print_message "success" "Proprietario della directory del database modificato con successo."
else
    print_message "error" "Impossibile modificare il proprietario della directory del database."
fi

# Impostazione dei permessi sulla directory
print_message "info" "Impostazione dei permessi sulla directory del database..."
chmod 775 "$DB_DIR"
if [ $? -eq 0 ]; then
    print_message "success" "Permessi della directory del database modificati con successo."
else
    print_message "error" "Impossibile modificare i permessi della directory del database."
fi

# Verifica i nuovi permessi
NEW_OWNER=$(stat -c '%U:%G' "$DB_FILE" 2>/dev/null)
print_message "info" "Nuovo proprietario del database: $NEW_OWNER"

NEW_PERMS=$(stat -c '%a' "$DB_FILE" 2>/dev/null)
print_message "info" "Nuovi permessi del database: $NEW_PERMS"

# Verifica se esiste il file di log degli errori del database
if [ -f "$DB_ERROR_LOG" ]; then
    print_message "info" "Rimozione del file di log degli errori del database..."
    rm "$DB_ERROR_LOG"
fi

# Aggiunge l'utente dell'applicazione al gruppo del web server per consentire l'accesso ai file
if [ "$APP_USER" != "$WEB_USER" ] && [ "$APP_USER" != "root" ]; then
    print_message "info" "Aggiunta dell'utente dell'applicazione ($APP_USER) al gruppo del web server ($WEB_USER)..."
    usermod -a -G $WEB_USER $APP_USER 2>/dev/null
    if [ $? -eq 0 ]; then
        print_message "success" "Utente aggiunto al gruppo del web server con successo."
    else
        print_message "warning" "Impossibile aggiungere l'utente al gruppo del web server. Potrebbe essere necessario farlo manualmente."
    fi
fi

# Verifica la presenza e l'accessibilità dell'ambiente virtuale Python
if [ -d "$INSTALL_DIR/venv" ]; then
    print_message "info" "Ambiente virtuale Python trovato: $INSTALL_DIR/venv"
    
    # Verifica i permessi dell'ambiente virtuale
    VENV_OWNER=$(stat -c '%U:%G' "$INSTALL_DIR/venv" 2>/dev/null)
    print_message "info" "Proprietario dell'ambiente virtuale: $VENV_OWNER"
    
    # Aggiungi permessi di esecuzione ai file dell'ambiente virtuale
    print_message "info" "Aggiunta dei permessi di esecuzione ai file dell'ambiente virtuale..."
    chmod -R +x "$INSTALL_DIR/venv/bin"
    if [ $? -eq 0 ]; then
        print_message "success" "Permessi di esecuzione aggiunti con successo."
    else
        print_message "warning" "Impossibile aggiungere permessi di esecuzione."
    fi
else
    print_message "warning" "Ambiente virtuale Python non trovato: $INSTALL_DIR/venv"
    print_message "info" "Potrebbe essere necessario reinstallare l'applicazione o ricreare l'ambiente virtuale."
fi

# Istruzioni per testare il database
print_message "info" ""
print_message "info" "Database riparato. Per verificare la riparazione, esegui:"
print_message "info" "cd $INSTALL_DIR && source venv/bin/activate && python create_admin.py"
print_message "info" ""

# Istruzioni per riavviare il servizio
print_message "info" "Dopo la verifica, riavvia il servizio EvoRouter con:"
print_message "info" "sudo systemctl restart evorouter.service"
print_message "info" ""

print_message "success" "Riparazione del database completata."

exit 0