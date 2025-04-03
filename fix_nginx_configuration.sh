#!/bin/bash
#
# Script per risolvere il problema 404 con Nginx su Ubuntu
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
   print_message "info" "Esegui: sudo $0"
   exit 1
fi

print_message "info" "#############################################"
print_message "info" "##                                         ##"
print_message "info" "##  CORREZIONE CONFIGURAZIONE NGINX       ##"
print_message "info" "##  EvoRouter R4 OS                       ##"
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "info" "Questo script correggerà la configurazione Nginx per EvoRouter."

# Rileva la distribuzione
DISTRO="Sconosciuta"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$NAME $VERSION_ID"
    print_message "info" "Distribuzione rilevata: $DISTRO"
else
    print_message "warning" "Impossibile rilevare la distribuzione. Assumerò Ubuntu."
fi

# Chiedi conferma prima di continuare
read -p "Continuare con la correzione? (s/n): " confirm
if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    print_message "info" "Operazione annullata."
    exit 0
fi

# Verifica se Nginx è installato
if ! command -v nginx &> /dev/null; then
    print_message "error" "Nginx non è installato. Installalo con 'apt install nginx' e riprova."
    exit 1
fi

# Rileva la versione di Nginx
NGINX_VERSION=$(nginx -v 2>&1 | awk -F/ '{print $2}')
print_message "info" "Versione Nginx rilevata: $NGINX_VERSION"

# Definizione delle variabili
NGINX_PATH="/etc/nginx"
SITES_AVAILABLE="$NGINX_PATH/sites-available"
SITES_ENABLED="$NGINX_PATH/sites-enabled"
DEFAULT_SITE="$SITES_AVAILABLE/default"
EVOROUTER_SITE="$SITES_AVAILABLE/evorouter"
EVOROUTER_SITE_ENABLED="$SITES_ENABLED/evorouter"
NGINX_HTML_PATH="/var/www/html"
DEFAULT_HTML="$NGINX_HTML_PATH/index.nginx-debian.html"
INSTALL_DIR="/opt/evorouter"

# Verifica se la directory di installazione esiste
if [ ! -d "$INSTALL_DIR" ]; then
    print_message "warning" "La directory $INSTALL_DIR non esiste."
    print_message "info" "Si presume che l'installazione sia in un'altra posizione o non sia ancora stata eseguita."
    
    read -p "Specificare la directory di installazione (premere Invio per utilizzare /opt/evorouter): " custom_dir
    if [ -n "$custom_dir" ]; then
        INSTALL_DIR="$custom_dir"
    fi
    
    # Verifica se la nuova directory esiste
    if [ ! -d "$INSTALL_DIR" ]; then
        print_message "info" "La directory $INSTALL_DIR non esiste. Verrà creata."
        mkdir -p "$INSTALL_DIR"
        check_command "Impossibile creare la directory $INSTALL_DIR."
    fi
fi

# Backup della configurazione esistente
print_message "info" "Backup della configurazione Nginx esistente..."
BACKUP_DIR="/tmp/nginx_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
check_command "Impossibile creare la directory di backup."

if [ -f "$DEFAULT_SITE" ]; then
    cp "$DEFAULT_SITE" "$BACKUP_DIR/"
    print_message "info" "Backup di $DEFAULT_SITE creato in $BACKUP_DIR/"
fi

if [ -f "$EVOROUTER_SITE" ]; then
    cp "$EVOROUTER_SITE" "$BACKUP_DIR/"
    print_message "info" "Backup di $EVOROUTER_SITE creato in $BACKUP_DIR/"
fi

# Disabilita il sito di default (se necessario)
if [ -f "$SITES_ENABLED/default" ]; then
    print_message "info" "Disabilitazione del sito di default..."
    rm -f "$SITES_ENABLED/default"
    check_command "Impossibile disabilitare il sito di default."
fi

# Crea la nuova configurazione per EvoRouter
print_message "info" "Creazione della nuova configurazione per EvoRouter..."
cat > "$EVOROUTER_SITE" << EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    # Impostazioni generali
    root /var/www/html;
    index index.html index.htm;
    
    # Aumenta il buffer per le intestazioni
    large_client_header_buffers 4 32k;
    
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

# Attiva la nuova configurazione
print_message "info" "Attivazione della nuova configurazione..."
ln -sf "$EVOROUTER_SITE" "$SITES_ENABLED/"
check_command "Impossibile attivare la configurazione."

# Rimuovi la pagina di default di Nginx
if [ -f "$DEFAULT_HTML" ]; then
    print_message "info" "Rimozione della pagina di default di Nginx..."
    mv "$DEFAULT_HTML" "${DEFAULT_HTML}.backup"
    check_command "Impossibile rinominare la pagina di default di Nginx."
    
    # Crea una pagina di redirect di fallback
    cat > "$NGINX_HTML_PATH/index.html" << EOF
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
    check_command "Impossibile creare la pagina di redirect."
fi

# Verifica la configurazione di Nginx
print_message "info" "Verifica della configurazione di Nginx..."
nginx -t
if [ $? -ne 0 ]; then
    print_message "error" "La configurazione di Nginx non è valida."
    print_message "info" "Ripristino della configurazione precedente..."
    
    # Ripristina dalla configurazione di backup
    if [ -f "$BACKUP_DIR/default" ]; then
        cp "$BACKUP_DIR/default" "$DEFAULT_SITE"
    fi
    if [ -f "$BACKUP_DIR/evorouter" ]; then
        cp "$BACKUP_DIR/evorouter" "$EVOROUTER_SITE"
    else
        rm -f "$EVOROUTER_SITE"
    fi
    
    # Riabilita la configurazione predefinita
    ln -sf "$DEFAULT_SITE" "$SITES_ENABLED/default"
    rm -f "$EVOROUTER_SITE_ENABLED"
    
    # Riavvia Nginx
    systemctl restart nginx
    
    print_message "error" "Ripristino della configurazione precedente completato. Controlla il file di configurazione manualmente."
    exit 1
fi

# Riavvia Nginx
print_message "info" "Riavvio di Nginx..."
systemctl restart nginx
check_command "Impossibile riavviare Nginx."

# Verifica che l'applicazione sia in esecuzione
print_message "info" "Verifica che l'applicazione EvoRouter sia in esecuzione..."
if systemctl -q is-active evorouter.service; then
    print_message "success" "Il servizio evorouter.service è attivo."
else
    print_message "warning" "Il servizio evorouter.service non sembra essere attivo."
    print_message "info" "Tentativo di avvio del servizio..."
    
    if systemctl -q is-enabled evorouter.service; then
        systemctl start evorouter.service
        if [ $? -ne 0 ]; then
            print_message "error" "Impossibile avviare il servizio evorouter.service."
            print_message "info" "Verifica lo stato con: systemctl status evorouter.service"
        else
            print_message "success" "Servizio evorouter.service avviato con successo."
        fi
    else
        print_message "warning" "Il servizio evorouter.service non è configurato."
        
        # Chiedi se l'utente vuole configurare il servizio
        read -p "Vuoi configurare il servizio systemd per EvoRouter? (s/n): " setup_service
        if [ "$setup_service" = "s" ] || [ "$setup_service" = "S" ]; then
            # Creazione del file di servizio
            SERVICE_FILE="/etc/systemd/system/evorouter.service"
            print_message "info" "Creazione del file di servizio systemd..."
            cat > "$SERVICE_FILE" << EOF
[Unit]
Description=EvoRouter R4 OS
After=network.target
Wants=nginx.service

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
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
            
            print_message "success" "Servizio EvoRouter configurato e avviato con successo!"
        else
            print_message "info" "Configurazione del servizio saltata."
            print_message "info" "Per avviare manualmente l'applicazione, esegui: cd $INSTALL_DIR && source venv/bin/activate && gunicorn --bind 127.0.0.1:5000 --workers 3 main:app"
        fi
    fi
fi

# Verifica l'accesso all'applicazione web
print_message "info" "Verifica dell'accesso all'applicazione web..."
sleep 5
if curl -s --max-time 10 http://localhost/ | grep -q "EvoRouter"; then
    print_message "success" "L'applicazione web è accessibile correttamente!"
else
    response=$(curl -s -I http://localhost/)
    if [ $? -ne 0 ]; then
        print_message "error" "Impossibile connettersi al server web locale."
    else
        print_message "warning" "La risposta non contiene 'EvoRouter'. Verificare manualmente."
        print_message "info" "Risposta HTTP: $response"
    fi
    
    print_message "info" "Verificare manualmente l'accesso all'applicazione tramite browser: http://localhost/"
    print_message "info" "Per verificare lo stato del servizio EvoRouter: systemctl status evorouter.service"
    print_message "info" "Per verificare i log di Nginx: journalctl -u nginx.service"
fi

# Informazioni finali
print_message "success" "##############################################"
print_message "success" "Configurazione Nginx completata!"
print_message "success" "##############################################"
print_message "info" ""
print_message "info" "Informazioni importanti:"
print_message "info" "- Backup della configurazione precedente: $BACKUP_DIR"
print_message "info" "- Configurazione Nginx: $EVOROUTER_SITE"
print_message "info" "- Directory di installazione: $INSTALL_DIR"
print_message "info" ""
print_message "info" "Per accedere all'applicazione, apri nel browser: http://localhost/"
print_message "info" ""
print_message "info" "Se riscontri ancora problemi, controlla i log:"
print_message "info" "- Logs di Nginx: journalctl -u nginx.service -f"
print_message "info" "- Logs di EvoRouter: journalctl -u evorouter.service -f"
print_message "info" ""
print_message "info" "Nota: Nel caso dovessi ripristinare la configurazione precedente, esegui:"
print_message "info" "sudo cp $BACKUP_DIR/default $DEFAULT_SITE"
print_message "info" "sudo ln -sf $DEFAULT_SITE $SITES_ENABLED/default"
print_message "info" "sudo rm -f $EVOROUTER_SITE_ENABLED"
print_message "info" "sudo systemctl restart nginx"

exit 0