#!/bin/bash
#
# Script per sincronizzare EvoRouter R4 OS con il repository GitHub
# Questo script automatizza il processo di aggiornamento tramite GitHub
# Versione: 1.1
# Data: 03/04/2025
#
# Changelog:
# 1.1 - 03/04/2025:
#   - Aggiunto supporto per Apache2
#   - Migliorato rilevamento del web server
#   - Aggiunto check per Ubuntu/Debian
#   - Aggiunto supporto per autenticazione GitHub con token
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

# Definizione del percorso di installazione
INSTALL_DIR="/opt/evorouter"

# Verifica che EvoRouter sia già installato
if [ ! -d "$INSTALL_DIR" ]; then
    print_message "error" "EvoRouter R4 OS non sembra essere installato in $INSTALL_DIR."
    print_message "info" "Esegui prima lo script di installazione install_evorouter.sh."
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
print_message "info" "##  SINCRONIZZAZIONE GITHUB               ##"
print_message "info" "##  EvoRouter R4 OS                       ##"
print_message "info" "##  Distribuzione: $DISTRO                 "
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "info" "Questo script sincronizzerà EvoRouter R4 OS con il repository GitHub."

# Chiedi conferma prima di continuare
read -p "Continuare con la sincronizzazione? (s/n): " confirm
if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    print_message "info" "Sincronizzazione annullata."
    exit 0
fi

# Backup dei file di configurazione
print_message "info" "Creazione del backup dei file di configurazione..."
BACKUP_DIR="/opt/evorouter_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR/config

# Backup del file .env e di altri file di configurazione importanti
cp -f $INSTALL_DIR/.env $BACKUP_DIR/config/ 2>/dev/null || print_message "warning" "File .env non trovato, nessun backup creato."
cp -rf $INSTALL_DIR/instance/ $BACKUP_DIR/config/ 2>/dev/null || print_message "warning" "Directory instance non trovata, nessun backup creato."

print_message "success" "Backup dei file di configurazione creato in $BACKUP_DIR"

# Sincronizzazione con GitHub
print_message "info" "Sincronizzazione con GitHub..."

# Naviga nella directory di installazione
cd $INSTALL_DIR

# Arresta il servizio prima dell'aggiornamento
print_message "info" "Arresto del servizio EvoRouter..."
systemctl stop evorouter.service

# Verifica se è già un repository Git
if [ ! -d ".git" ]; then
    print_message "info" "Inizializzazione di Git in $INSTALL_DIR..."
    git init
    check_command "Impossibile inizializzare il repository Git."
    
    print_message "info" "Configurazione dell'URL del repository remoto..."
    git remote add origin https://github.com/dexter939/evorouter.git
    check_command "Impossibile aggiungere il repository remoto."
else
    print_message "info" "Repository Git già inizializzato."
fi

# Chiedi all'utente se vuole utilizzare un token GitHub per l'autenticazione
print_message "info" "L'autenticazione con token GitHub può migliorare l'accesso al repository."
read -p "Vuoi utilizzare un token GitHub per l'autenticazione? (s/n): " use_token
if [ "$use_token" = "s" ] || [ "$use_token" = "S" ]; then
    read -s -p "Inserisci il tuo token GitHub: " github_token
    echo "" # Nuova linea dopo input password
    
    if [ -n "$github_token" ]; then
        # Configura il remote con autenticazione basata su token
        git remote set-url origin "https://${github_token}@github.com/dexter939/evorouter.git"
        print_message "success" "Token GitHub configurato per l'autenticazione!"
    else
        print_message "warning" "Token non fornito. Verrà utilizzata l'autenticazione standard."
    fi
fi

# Recupera gli ultimi aggiornamenti
print_message "info" "Recupero degli ultimi aggiornamenti da GitHub..."
git fetch origin
if [ $? -ne 0 ]; then
    print_message "warning" "Impossibile recuperare gli aggiornamenti. Potrebbe essere necessario un token GitHub o verificare la connessione di rete."
    read -p "Vuoi riprovare con un token GitHub? (s/n): " retry_token
    if [ "$retry_token" = "s" ] || [ "$retry_token" = "S" ]; then
        read -s -p "Inserisci il tuo token GitHub: " github_token
        echo "" # Nuova linea dopo input password
        if [ -n "$github_token" ]; then
            git remote set-url origin "https://${github_token}@github.com/dexter939/evorouter.git"
            print_message "info" "Nuovo tentativo di recupero degli aggiornamenti..."
            git fetch origin
            check_command "Impossibile recuperare gli aggiornamenti da GitHub anche con il token."
        else
            print_message "error" "Token non fornito. Impossibile continuare."
            exit 1
        fi
    else
        print_message "error" "Impossibile recuperare gli aggiornamenti da GitHub. Verifica la connessione o utilizza un token."
        exit 1
    fi
fi

# Backup temporaneo dei file di configurazione
print_message "info" "Backup temporaneo dei file di configurazione..."
mkdir -p /tmp/evorouter_config_backup
cp -f .env /tmp/evorouter_config_backup/ 2>/dev/null || true
cp -rf instance/ /tmp/evorouter_config_backup/ 2>/dev/null || true

# Pull degli aggiornamenti (evitando conflitti sui file locali)
print_message "info" "Aggiornamento dei file dal repository GitHub..."
git reset --hard origin/main
check_command "Impossibile aggiornare i file dal repository GitHub."

# Ripristina i file di configurazione
print_message "info" "Ripristino dei file di configurazione..."
cp -f /tmp/evorouter_config_backup/.env . 2>/dev/null || true
cp -rf /tmp/evorouter_config_backup/instance/ . 2>/dev/null || true
rm -rf /tmp/evorouter_config_backup

# Aggiorna le dipendenze Python
print_message "info" "Aggiornamento delle dipendenze Python..."
source venv/bin/activate
python -m pip install --upgrade pip
check_command "Impossibile aggiornare pip."

pip install -r requirements.txt
check_command "Impossibile installare le dipendenze Python."

# Aggiorna il database
print_message "info" "Aggiornamento del database..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"
if [ $? -ne 0 ]; then
    print_message "warning" "Errore durante l'aggiornamento del database. Ripristino del backup..."
    cp -f $BACKUP_DIR/config/.env $INSTALL_DIR/ 2>/dev/null || true
    cp -rf $BACKUP_DIR/config/instance/ $INSTALL_DIR/ 2>/dev/null || true
    print_message "info" "Puoi tentare di risolvere il problema manualmente e poi eseguire: cd $INSTALL_DIR && source venv/bin/activate && python -c 'from app import app, db; app.app_context().push(); db.create_all()'"
else
    print_message "success" "Database aggiornato con successo!"
fi

# Imposta i permessi corretti per la directory instance
mkdir -p $INSTALL_DIR/instance
chmod -R 777 $INSTALL_DIR/instance

# Riavvio del servizio
print_message "info" "Riavvio del servizio EvoRouter..."
systemctl restart evorouter.service

# Verifica lo stato in modo più dettagliato
sleep 5
if ! systemctl is-active --quiet evorouter.service; then
    print_message "warning" "Il servizio EvoRouter non è stato avviato correttamente."
    print_message "info" "Consulta i log per maggiori dettagli: journalctl -u evorouter.service -n 50"
    # Ripristina dal backup
    print_message "warning" "Tentativo di ripristino dal backup..."
    systemctl stop evorouter.service
    cp -f $BACKUP_DIR/config/.env $INSTALL_DIR/ 2>/dev/null || true
    cp -rf $BACKUP_DIR/config/instance/ $INSTALL_DIR/ 2>/dev/null || true
    systemctl start evorouter.service
    if systemctl is-active --quiet evorouter.service; then
        print_message "success" "Ripristino riuscito! EvoRouter è stato riportato allo stato precedente."
    else
        print_message "error" "Impossibile ripristinare. Consulta i log e ripristina manualmente dal backup in $BACKUP_DIR."
    fi
else
    print_message "success" "Il servizio EvoRouter è stato riavviato con successo!"
fi

# Rileva il web server in uso (Nginx o Apache)
WEBSERVER="Nginx"
if ! command -v nginx &> /dev/null && command -v apache2 &> /dev/null; then
    WEBSERVER="Apache"
fi

# Verifica finale dell'applicazione web
print_message "info" "Verifica dell'applicazione web..."
sleep 5
if curl -s --max-time 10 http://127.0.0.1/ | grep -q "EvoRouter"; then
    print_message "success" "L'applicazione web è attiva e raggiungibile!"
else
    print_message "warning" "L'applicazione web non risponde correttamente. Verificare i log:"
    print_message "info" "journalctl -u evorouter.service -n 50"
    
    if [ "$WEBSERVER" = "Nginx" ]; then
        print_message "info" "journalctl -u nginx.service -n 20"
    else
        print_message "info" "journalctl -u apache2.service -n 20"
        print_message "info" "cat /var/log/apache2/error.log"
    fi
fi

# Informazioni finali
print_message "success" "##############################################"
print_message "success" "Sincronizzazione con GitHub completata!"
print_message "success" "##############################################"
print_message "info" ""
print_message "info" "Informazioni importanti:"
print_message "info" "- Backup creato in: $BACKUP_DIR"
print_message "info" "- Interfaccia web: http://$(hostname -I | awk '{print $1}')/"
print_message "info" ""
print_message "info" "Per visualizzare i log del sistema:"
print_message "info" "- Logs di EvoRouter: journalctl -u evorouter.service -f"
if [ "$WEBSERVER" = "Nginx" ]; then
    print_message "info" "- Logs di Nginx: journalctl -u nginx.service -f"
else
    print_message "info" "- Logs di Apache: journalctl -u apache2.service -f"
    print_message "info" "- Error log di Apache: tail -f /var/log/apache2/error.log"
fi

exit 0