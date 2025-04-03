#!/bin/bash
#
# Script di aggiornamento per EvoRouter R4 OS
# Questo script automatizza il processo di aggiornamento del sistema operativo
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
print_message "info" "##  AGGIORNAMENTO EvoRouter R4 OS         ##"
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "info" "Inizializzazione dell'aggiornamento di EvoRouter R4 OS..."
print_message "info" "Questo processo potrebbe richiedere alcuni minuti."

# Chiedi conferma prima di continuare
read -p "Questo script aggiornerà EvoRouter R4 OS in $INSTALL_DIR. Continuare? (s/n): " confirm
if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    print_message "info" "Aggiornamento annullato."
    exit 0
fi

# Backup dei file di configurazione
print_message "info" "Creazione del backup dei file di configurazione..."
BACKUP_DIR="/opt/evorouter_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR/config

# Backup del file .env e di altri file di configurazione importanti
cp -f $INSTALL_DIR/.env $BACKUP_DIR/config/ 2>/dev/null || print_message "warning" "File .env non trovato, nessun backup creato."
cp -f $INSTALL_DIR/instance/*.db $BACKUP_DIR/config/ 2>/dev/null || print_message "warning" "Database SQLite non trovato, nessun backup creato."

print_message "success" "Backup dei file di configurazione creato in $BACKUP_DIR"

# Aggiornamento del codice
print_message "info" "Passo 1: Aggiornamento del codice sorgente..."

# Chiedi all'utente quale metodo di aggiornamento preferisce
echo ""
echo "Seleziona il metodo di aggiornamento:"
echo "1) Download dal repository GitHub (consigliato)"
echo "2) Trasferimento manuale di un archivio ZIP"
read -p "Scelta (1/2): " update_method

case $update_method in
    1)
        # Download dal repository GitHub
        print_message "info" "Download del codice dal repository GitHub..."
        read -p "Inserisci l'URL del repository GitHub (predefinito: https://github.com/dexter939/evorouter.git): " github_url
        github_url=${github_url:-https://github.com/dexter939/evorouter.git}
        
        cd $INSTALL_DIR
        # Arresta il servizio prima dell'aggiornamento
        systemctl stop evorouter.service
        
        # Backup completo dell'installazione corrente
        print_message "info" "Creazione di un backup completo dell'installazione corrente..."
        cp -r $INSTALL_DIR/* $BACKUP_DIR/ 2>/dev/null
        cp -r $INSTALL_DIR/.* $BACKUP_DIR/ 2>/dev/null || true
        
        # Clona il repository in una directory temporanea
        print_message "info" "Clonazione del repository..."
        git clone $github_url /tmp/evorouter_update
        check_command "Impossibile clonare il repository GitHub."
        
        # Rimuovi i file esistenti ma mantieni i file di configurazione e l'ambiente virtuale
        print_message "info" "Aggiornamento dei file..."
        find $INSTALL_DIR -type f -not -path "$INSTALL_DIR/venv*" -not -path "$INSTALL_DIR/.env" -not -path "$INSTALL_DIR/instance*" -delete
        
        # Copia i nuovi file
        cp -r /tmp/evorouter_update/* $INSTALL_DIR/
        cp -r /tmp/evorouter_update/.* $INSTALL_DIR/ 2>/dev/null || true
        rm -rf /tmp/evorouter_update
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
        
        # Arresta il servizio prima dell'aggiornamento
        systemctl stop evorouter.service
        
        # Backup completo dell'installazione corrente
        print_message "info" "Creazione di un backup completo dell'installazione corrente..."
        cp -r $INSTALL_DIR/* $BACKUP_DIR/ 2>/dev/null
        cp -r $INSTALL_DIR/.* $BACKUP_DIR/ 2>/dev/null || true
        
        # Estrazione dell'archivio
        print_message "info" "Estrazione dei file di aggiornamento..."
        mkdir -p /tmp/evorouter_update
        unzip -q "$zip_path" -d /tmp/evorouter_update
        check_command "Impossibile estrarre l'archivio ZIP."
        
        # Rimuovi i file esistenti ma mantieni i file di configurazione e l'ambiente virtuale
        print_message "info" "Aggiornamento dei file..."
        find $INSTALL_DIR -type f -not -path "$INSTALL_DIR/venv*" -not -path "$INSTALL_DIR/.env" -not -path "$INSTALL_DIR/instance*" -delete
        
        # Copia i nuovi file
        cp -r /tmp/evorouter_update/* $INSTALL_DIR/
        cp -r /tmp/evorouter_update/.* $INSTALL_DIR/ 2>/dev/null || true
        rm -rf /tmp/evorouter_update
        ;;
    *)
        print_message "error" "Opzione non valida. Aggiornamento annullato."
        exit 1
        ;;
esac

# Aggiornamento delle dipendenze
print_message "info" "Passo 2: Aggiornamento delle dipendenze Python..."
cd $INSTALL_DIR
source venv/bin/activate

# Aggiorna pip stesso
python -m pip install --upgrade pip
check_command "Impossibile aggiornare pip."

# Installa/aggiorna le dipendenze
pip install -r requirements.txt
check_command "Impossibile installare le dipendenze Python."

# Aggiornamento del database
print_message "info" "Passo 3: Aggiornamento del database..."

# Imposta permessi corretti per il database
if [[ "$DATABASE_URL" == sqlite* ]]; then
    # Crea la directory instance per SQLite se necessario
    mkdir -p $INSTALL_DIR/instance
    # Imposta permessi molto permissivi per assicurare l'accesso
    chmod -R 777 $INSTALL_DIR/instance
    
    # Verifica il percorso del database
    set -a
    source $INSTALL_DIR/.env
    set +a
    
    # Estrai il percorso del file database dall'URL
    DB_FILE_PATH=${DATABASE_URL#sqlite:///}
    
    # Se è un percorso relativo, lo rendiamo assoluto
    if [[ "$DB_FILE_PATH" != /* ]]; then
        DB_FILE_PATH="$INSTALL_DIR/$DB_FILE_PATH"
    fi
    
    # Imposta i permessi corretti
    DB_DIR=$(dirname "$DB_FILE_PATH")
    chmod -R 777 "$DB_DIR"
    print_message "info" "Permessi impostati per database SQLite in $DB_DIR"
fi

# Esegui le migrazioni del database
cd $INSTALL_DIR
python -c "from app import app, db; app.app_context().push(); db.create_all()"
if [ $? -ne 0 ]; then
    print_message "warning" "Errore durante l'aggiornamento del database. Ripristino del backup..."
    cp $BACKUP_DIR/config/.env $INSTALL_DIR/ 2>/dev/null || true
    cp $BACKUP_DIR/config/*.db $INSTALL_DIR/instance/ 2>/dev/null || true
    print_message "info" "Puoi tentare di risolvere il problema manualmente e poi eseguire: cd $INSTALL_DIR && source venv/bin/activate && python -c 'from app import app, db; app.app_context().push(); db.create_all()'"
else
    print_message "success" "Database aggiornato con successo!"
fi

# Riavvio del servizio
print_message "info" "Passo 4: Riavvio del servizio..."

# Aggiorna il file di servizio systemd
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
check_command "Impossibile ricaricare la configurazione di systemd."

# Riavvia il servizio
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
    rm -rf $INSTALL_DIR/*
    rm -rf $INSTALL_DIR/.*
    cp -r $BACKUP_DIR/* $INSTALL_DIR/
    cp -r $BACKUP_DIR/.* $INSTALL_DIR/ 2>/dev/null || true
    systemctl start evorouter.service
    if systemctl is-active --quiet evorouter.service; then
        print_message "success" "Ripristino riuscito! EvoRouter è stato riportato allo stato precedente."
    else
        print_message "error" "Impossibile ripristinare. Consulta i log e ripristina manualmente dal backup in $BACKUP_DIR."
    fi
else
    print_message "success" "Il servizio EvoRouter è stato riavviato con successo!"
fi

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

# Pulisci i backup vecchi di più di 7 giorni
print_message "info" "Pulizia dei backup più vecchi di 7 giorni..."
find /opt -maxdepth 1 -name "evorouter_backup_*" -type d -mtime +7 -exec rm -rf {} \;

# Informazioni finali
print_message "success" "##############################################"
print_message "success" "Aggiornamento di EvoRouter R4 OS completato!"
print_message "success" "##############################################"
print_message "info" ""
print_message "info" "Informazioni importanti:"
print_message "info" "- Backup creato in: $BACKUP_DIR"
print_message "info" "- Interfaccia web: http://$(hostname -I | awk '{print $1}')/"
print_message "info" ""
print_message "info" "Per visualizzare i log del sistema:"
print_message "info" "- Logs di EvoRouter: journalctl -u evorouter.service -f"
print_message "info" "- Logs di Nginx: journalctl -u nginx.service -f"
print_message "info" ""

# Riavvia Nginx per sicurezza
systemctl restart nginx

print_message "info" "Grazie per aver aggiornato EvoRouter R4 OS!"

exit 0