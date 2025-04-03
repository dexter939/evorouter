#!/bin/bash
#
# Script di diagnostica avanzata per problemi Nginx su Ubuntu
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
   print_message "info" "Esegui: sudo $0"
   exit 1
fi

print_message "info" "#############################################"
print_message "info" "##                                         ##"
print_message "info" "##  DIAGNOSTICA AVANZATA NGINX            ##"
print_message "info" "##  EvoRouter R4 OS                       ##"
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "info" "Questo script eseguirà una diagnostica approfondita del problema Nginx."

# Rileva la distribuzione
DISTRO="Sconosciuta"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$NAME $VERSION_ID"
    print_message "info" "Distribuzione rilevata: $DISTRO"
else
    print_message "warning" "Impossibile rilevare la distribuzione. Assumerò Ubuntu."
fi

# Verifica se Nginx è installato
if ! command -v nginx &> /dev/null; then
    print_message "error" "Nginx non è installato. Installalo con 'apt install nginx' e riprova."
    print_message "info" "Comando per installare Nginx: sudo apt update && sudo apt install -y nginx"
    exit 1
fi

# Rileva la versione di Nginx
NGINX_VERSION=$(nginx -v 2>&1 | awk -F/ '{print $2}')
print_message "info" "Versione Nginx rilevata: $NGINX_VERSION"

# Definizione delle variabili dei percorsi
NGINX_PATH="/etc/nginx"
NGINX_CONF="$NGINX_PATH/nginx.conf"
SITES_AVAILABLE="$NGINX_PATH/sites-available"
SITES_ENABLED="$NGINX_PATH/sites-enabled"
DEFAULT_SITE="$SITES_AVAILABLE/default"
EVOROUTER_SITE="$SITES_AVAILABLE/evorouter"
NGINX_LOGS="/var/log/nginx"
ACCESS_LOG="$NGINX_LOGS/access.log"
ERROR_LOG="$NGINX_LOGS/error.log"
INSTALL_DIR="/opt/evorouter"

# Crea directory per il report
REPORT_DIR="/tmp/nginx_report_$(date +%Y%m%d_%H%M%S)"
mkdir -p $REPORT_DIR
print_message "info" "Report di diagnostica sarà salvato in $REPORT_DIR"

# Controlla se Nginx è in esecuzione
print_message "info" "Verifica dello stato di Nginx..."
if systemctl is-active --quiet nginx; then
    print_message "success" "Nginx è in esecuzione."
    NGINX_RUNNING=true
else
    print_message "warning" "Nginx non è in esecuzione."
    print_message "info" "Tentativo di avvio di Nginx..."
    systemctl start nginx
    if systemctl is-active --quiet nginx; then
        print_message "success" "Nginx avviato con successo."
        NGINX_RUNNING=true
    else
        print_message "error" "Impossibile avviare Nginx."
        print_message "info" "Output di 'systemctl status nginx':"
        systemctl status nginx | tee "$REPORT_DIR/nginx_status.txt"
        NGINX_RUNNING=false
    fi
fi

# Verifica la configurazione di Nginx
print_message "info" "Verifica della configurazione di Nginx..."
nginx -t 2>&1 | tee "$REPORT_DIR/nginx_config_test.txt"
NGINX_CONFIG_OK=$?
if [ $NGINX_CONFIG_OK -eq 0 ]; then
    print_message "success" "La configurazione di Nginx è valida."
else
    print_message "error" "La configurazione di Nginx contiene errori."
fi

# Controlla il file di configurazione principale
print_message "info" "Analisi del file di configurazione principale..."
if [ -f "$NGINX_CONF" ]; then
    cp "$NGINX_CONF" "$REPORT_DIR/nginx.conf"
    print_message "info" "File di configurazione principale copiato in $REPORT_DIR/nginx.conf"
    
    # Analizza il file di configurazione per rilevare problemi comuni
    grep -n "server_names_hash_bucket_size" "$NGINX_CONF" > /dev/null
    if [ $? -ne 0 ]; then
        print_message "warning" "server_names_hash_bucket_size non impostato, potrebbe causare problemi con nomi server lunghi."
    fi
else
    print_message "error" "File di configurazione principale non trovato: $NGINX_CONF"
fi

# Controlla i siti disponibili e abilitati
print_message "info" "Verifica dei siti disponibili e abilitati..."
if [ -d "$SITES_AVAILABLE" ]; then
    ls -la "$SITES_AVAILABLE" | tee "$REPORT_DIR/sites_available.txt"
    print_message "info" "Elenco dei siti disponibili salvato in $REPORT_DIR/sites_available.txt"
    
    # Conta il numero di siti
    SITES_COUNT=$(ls "$SITES_AVAILABLE" | wc -l)
    print_message "info" "Siti disponibili: $SITES_COUNT"
    
    # Copia tutti i file di configurazione dei siti
    mkdir -p "$REPORT_DIR/sites_available"
    cp "$SITES_AVAILABLE"/* "$REPORT_DIR/sites_available/" 2>/dev/null
    print_message "info" "File di configurazione dei siti copiati in $REPORT_DIR/sites_available/"
else
    print_message "error" "Directory dei siti disponibili non trovata: $SITES_AVAILABLE"
fi

if [ -d "$SITES_ENABLED" ]; then
    ls -la "$SITES_ENABLED" | tee "$REPORT_DIR/sites_enabled.txt"
    print_message "info" "Elenco dei siti abilitati salvato in $REPORT_DIR/sites_enabled.txt"
    
    # Conta il numero di siti abilitati
    ENABLED_SITES_COUNT=$(ls "$SITES_ENABLED" | wc -l)
    print_message "info" "Siti abilitati: $ENABLED_SITES_COUNT"
    
    # Verifica se ci sono più siti abilitati che potrebbero entrare in conflitto
    if [ $ENABLED_SITES_COUNT -gt 1 ]; then
        print_message "warning" "Più di un sito abilitato. Possibile conflitto di configurazione."
        
        # Verifica se più di un sito è configurato come default_server
        DEFAULT_SERVER_COUNT=$(grep -l "default_server" "$SITES_ENABLED"/* 2>/dev/null | wc -l)
        if [ $DEFAULT_SERVER_COUNT -gt 1 ]; then
            print_message "error" "Rilevati $DEFAULT_SERVER_COUNT siti configurati come default_server. Questo causa conflitti."
            print_message "info" "Siti configurati come default_server:"
            grep -l "default_server" "$SITES_ENABLED"/* 2>/dev/null | tee "$REPORT_DIR/default_servers.txt"
        fi
    fi
else
    print_message "error" "Directory dei siti abilitati non trovata: $SITES_ENABLED"
fi

# Verifica se esiste il sito EvoRouter
print_message "info" "Verifica della configurazione specifica per EvoRouter..."
if [ -f "$EVOROUTER_SITE" ]; then
    print_message "success" "Trovato file di configurazione per EvoRouter: $EVOROUTER_SITE"
    
    # Verifica se il sito è abilitato
    if [ -L "$SITES_ENABLED/evorouter" ]; then
        print_message "success" "Il sito EvoRouter è abilitato."
    else
        print_message "warning" "Il sito EvoRouter non è abilitato."
        print_message "info" "Per abilitare il sito: sudo ln -sf $EVOROUTER_SITE $SITES_ENABLED/"
    fi
    
    # Analisi della configurazione di EvoRouter
    grep -n "listen.*default_server" "$EVOROUTER_SITE" > /dev/null
    if [ $? -eq 0 ]; then
        print_message "success" "Il sito EvoRouter è configurato come server predefinito."
    else
        print_message "warning" "Il sito EvoRouter non è configurato come server predefinito."
        print_message "info" "Modifica la configurazione aggiungendo 'default_server' alla direttiva 'listen'."
    fi
    
    grep -n "proxy_pass.*127.0.0.1:5000" "$EVOROUTER_SITE" > /dev/null
    if [ $? -eq 0 ]; then
        print_message "success" "Il proxy verso l'applicazione EvoRouter è configurato correttamente."
    else
        print_message "error" "Il proxy verso l'applicazione EvoRouter non è configurato correttamente."
        print_message "info" "Verifica che ci sia una direttiva 'proxy_pass http://127.0.0.1:5000;' nella configurazione."
    fi
else
    print_message "warning" "File di configurazione per EvoRouter non trovato: $EVOROUTER_SITE"
    
    # Verifica se esiste il sito predefinito
    if [ -f "$DEFAULT_SITE" ]; then
        print_message "info" "Trovato file di configurazione predefinito: $DEFAULT_SITE"
        
        # Verifica se il sito predefinito è abilitato
        if [ -L "$SITES_ENABLED/default" ]; then
            print_message "info" "Il sito predefinito è abilitato."
            
            # Controlla se il sito predefinito ha un proxy pass per EvoRouter
            grep -n "proxy_pass.*127.0.0.1:5000" "$DEFAULT_SITE" > /dev/null
            if [ $? -eq 0 ]; then
                print_message "success" "Il sito predefinito è configurato per proxy a EvoRouter."
            else
                print_message "warning" "Il sito predefinito non ha una configurazione di proxy per EvoRouter."
                print_message "info" "Il file predefinito potrebbe bloccare le richieste a EvoRouter."
            fi
        else
            print_message "info" "Il sito predefinito non è abilitato."
        fi
    else
        print_message "warning" "File di configurazione predefinito non trovato: $DEFAULT_SITE"
    fi
fi

# Controlla i log di Nginx
print_message "info" "Analisi dei log di Nginx..."
if [ -d "$NGINX_LOGS" ]; then
    # Controlla gli ultimi errori nel log di errori
    if [ -f "$ERROR_LOG" ]; then
        tail -n 50 "$ERROR_LOG" > "$REPORT_DIR/error_log_tail.txt"
        print_message "info" "Ultimi 50 errori salvati in $REPORT_DIR/error_log_tail.txt"
        
        # Grep per errori comuni
        grep -i "permission denied" "$ERROR_LOG" | tail -n 20 > "$REPORT_DIR/permission_errors.txt"
        
        # Visualizza errori recenti
        RECENT_ERRORS=$(grep -i "error" "$ERROR_LOG" | tail -n 5)
        if [ -n "$RECENT_ERRORS" ]; then
            print_message "warning" "Errori recenti trovati nei log:"
            echo "$RECENT_ERRORS"
        fi
    else
        print_message "warning" "File di log degli errori non trovato: $ERROR_LOG"
    fi
    
    # Controlla gli accessi recenti
    if [ -f "$ACCESS_LOG" ]; then
        tail -n 20 "$ACCESS_LOG" > "$REPORT_DIR/access_log_tail.txt"
        print_message "info" "Ultimi 20 accessi salvati in $REPORT_DIR/access_log_tail.txt"
        
        # Controlla gli ultimi codici di stato HTTP
        HTTP_CODES=$(tail -n 100 "$ACCESS_LOG" | grep -o '"GET [^"]*" [0-9]*' | awk '{print $3}' | sort | uniq -c | sort -nr)
        if [ -n "$HTTP_CODES" ]; then
            print_message "info" "Analisi degli ultimi 100 codici di risposta HTTP:"
            echo "$HTTP_CODES" | tee "$REPORT_DIR/http_codes.txt"
            
            # Verifica se ci sono errori 404
            ERROR_404=$(echo "$HTTP_CODES" | grep " 404" | awk '{print $1}')
            if [ -n "$ERROR_404" ]; then
                print_message "warning" "Rilevati $ERROR_404 errori 404 (Not Found) negli ultimi 100 accessi."
                
                # Estrai quali URL stanno generando 404
                tail -n 500 "$ACCESS_LOG" | grep ' 404 ' | grep -o '"GET [^"]*"' | sort | uniq -c | sort -nr > "$REPORT_DIR/404_urls.txt"
                print_message "info" "URL che generano errori 404 salvati in $REPORT_DIR/404_urls.txt"
                print_message "info" "URL principali che generano errori 404:"
                head -n 5 "$REPORT_DIR/404_urls.txt"
            fi
        fi
    else
        print_message "warning" "File di log degli accessi non trovato: $ACCESS_LOG"
    fi
else
    print_message "error" "Directory dei log non trovata: $NGINX_LOGS"
fi

# Verifica se l'applicazione EvoRouter è in esecuzione
print_message "info" "Verifica se l'applicazione EvoRouter è in esecuzione..."
if systemctl -q is-active evorouter.service; then
    print_message "success" "Il servizio evorouter.service è attivo."
    systemctl status evorouter.service | head -n 20 > "$REPORT_DIR/evorouter_status.txt"
else
    print_message "warning" "Il servizio evorouter.service non è attivo o non esiste."
    
    # Verifica se ci sono processi in ascolto sulla porta 5000
    print_message "info" "Verifica dei processi in ascolto sulla porta 5000..."
    PROCESS_5000=$(netstat -tuln | grep ":5000" || ss -tuln | grep ":5000")
    if [ -n "$PROCESS_5000" ]; then
        print_message "success" "Trovato processo in ascolto sulla porta 5000:"
        echo "$PROCESS_5000" | tee "$REPORT_DIR/port_5000.txt"
        
        # Verifica quale processo è in ascolto
        print_message "info" "Identificazione del processo in ascolto sulla porta 5000..."
        PROCESS_INFO=$(netstat -tulnp 2>/dev/null | grep ":5000" || ss -tulnp | grep ":5000")
        if [ -n "$PROCESS_INFO" ]; then
            echo "$PROCESS_INFO" >> "$REPORT_DIR/port_5000.txt"
            print_message "info" "Informazioni processo: $PROCESS_INFO"
        else
            print_message "warning" "Impossibile identificare il processo (potrebbe richiedere privilegi di root)."
        fi
    else
        print_message "error" "Nessun processo in ascolto sulla porta 5000."
        print_message "info" "L'applicazione Flask/Gunicorn non sembra essere in esecuzione."
        
        # Verifica se il servizio può essere avviato
        if systemctl list-unit-files | grep -q evorouter.service; then
            print_message "info" "Il servizio evorouter.service esiste ma non è in esecuzione."
            print_message "info" "Per avviarlo: sudo systemctl start evorouter.service"
        else
            print_message "warning" "Il servizio evorouter.service non è definito nel sistema."
            print_message "info" "Verifica se l'applicazione è installata correttamente in $INSTALL_DIR"
            print_message "info" "Altrimenti, esegui manualmente: cd $INSTALL_DIR && source venv/bin/activate && gunicorn --bind 127.0.0.1:5000 main:app"
        fi
    fi
fi

# Test di connettività a localhost:5000
print_message "info" "Test di connettività a localhost:5000..."
curl -v localhost:5000 > "$REPORT_DIR/curl_localhost_5000.txt" 2>&1
if [ $? -eq 0 ]; then
    print_message "success" "Connessione a localhost:5000 riuscita."
else
    print_message "error" "Impossibile connettersi a localhost:5000."
    print_message "info" "Dettagli della connessione salvati in $REPORT_DIR/curl_localhost_5000.txt"
fi

# Test di connettività a localhost porta 80 (Nginx)
print_message "info" "Test di connettività a localhost (porta 80)..."
curl -v localhost > "$REPORT_DIR/curl_localhost_80.txt" 2>&1
if [ $? -eq 0 ]; then
    print_message "success" "Connessione a localhost (porta 80) riuscita."
else
    print_message "error" "Impossibile connettersi a localhost (porta 80)."
    print_message "info" "Dettagli della connessione salvati in $REPORT_DIR/curl_localhost_80.txt"
fi

# Generazione del report finale
print_message "info" "Generazione del report finale..."
cat > "$REPORT_DIR/report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Diagnostica Nginx - EvoRouter R4 OS</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1 { color: #333; }
        h2 { color: #0066cc; margin-top: 30px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow: auto; }
        .container { max-width: 1200px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Report Diagnostico Nginx - EvoRouter R4 OS</h1>
        <p>Data: $(date)</p>
        <p>Sistema: $DISTRO</p>
        <p>Versione Nginx: $NGINX_VERSION</p>
        
        <h2>Stato di Nginx</h2>
        <p>Nginx in esecuzione: $(if [ "$NGINX_RUNNING" = true ]; then echo "<span class='success'>Sì</span>"; else echo "<span class='error'>No</span>"; fi)</p>
        <p>Configurazione valida: $(if [ $NGINX_CONFIG_OK -eq 0 ]; then echo "<span class='success'>Sì</span>"; else echo "<span class='error'>No</span>"; fi)</p>
        
        <h2>Configurazioni attive</h2>
        <p>Siti disponibili: $SITES_COUNT</p>
        <p>Siti abilitati: $ENABLED_SITES_COUNT</p>
        
        <h2>Accessi recenti</h2>
        <pre>$(if [ -f "$REPORT_DIR/http_codes.txt" ]; then cat "$REPORT_DIR/http_codes.txt"; else echo "Dati non disponibili"; fi)</pre>
        
        <h2>Errori 404 principali</h2>
        <pre>$(if [ -f "$REPORT_DIR/404_urls.txt" ]; then head -n 10 "$REPORT_DIR/404_urls.txt"; else echo "Dati non disponibili"; fi)</pre>
        
        <h2>Stato dell'applicazione</h2>
        <pre>$(if [ -f "$REPORT_DIR/evorouter_status.txt" ]; then cat "$REPORT_DIR/evorouter_status.txt"; else echo "Dati non disponibili"; fi)</pre>
        
        <h2>Test di connettività</h2>
        <p>localhost:5000: $(if grep -q "< HTTP/1.1 200 OK\|< HTTP/1.1 302 FOUND" "$REPORT_DIR/curl_localhost_5000.txt" 2>/dev/null; then echo "<span class='success'>Successo</span>"; else echo "<span class='error'>Fallito</span>"; fi)</p>
        <p>localhost:80: $(if grep -q "< HTTP/1.1 200 OK\|< HTTP/1.1 302 FOUND" "$REPORT_DIR/curl_localhost_80.txt" 2>/dev/null; then echo "<span class='success'>Successo</span>"; else echo "<span class='error'>Fallito</span>"; fi)</p>
        
        <h2>Raccomandazioni</h2>
        <ul>
EOF

# Aggiungi raccomandazioni basate sui problemi rilevati
if [ "$NGINX_RUNNING" != true ]; then
    echo "<li class='error'>Avviare Nginx: sudo systemctl start nginx</li>" >> "$REPORT_DIR/report.html"
fi

if [ $NGINX_CONFIG_OK -ne 0 ]; then
    echo "<li class='error'>Correggere gli errori nella configurazione di Nginx</li>" >> "$REPORT_DIR/report.html"
fi

if [ ! -f "$EVOROUTER_SITE" ]; then
    echo "<li class='warning'>Creare un file di configurazione per EvoRouter: $EVOROUTER_SITE</li>" >> "$REPORT_DIR/report.html"
elif [ ! -L "$SITES_ENABLED/evorouter" ]; then
    echo "<li class='warning'>Abilitare il sito EvoRouter: sudo ln -sf $EVOROUTER_SITE $SITES_ENABLED/</li>" >> "$REPORT_DIR/report.html"
fi

if grep -q " 404 " "$REPORT_DIR/http_codes.txt" 2>/dev/null; then
    echo "<li class='warning'>Correggere gli errori 404 verificando gli URL richiesti</li>" >> "$REPORT_DIR/report.html"
fi

if ! grep -q ":5000" "$REPORT_DIR/port_5000.txt" 2>/dev/null; then
    echo "<li class='error'>Avviare l'applicazione EvoRouter sulla porta 5000</li>" >> "$REPORT_DIR/report.html"
fi

# Controlla se il sito predefinito potrebbe bloccare le richieste
if [ -L "$SITES_ENABLED/default" ] && [ -L "$SITES_ENABLED/evorouter" ]; then
    echo "<li class='warning'>Possibile conflitto: sia il sito predefinito che EvoRouter sono abilitati. Considera di disabilitare il sito predefinito: sudo rm $SITES_ENABLED/default</li>" >> "$REPORT_DIR/report.html"
fi

# Completa il report HTML
cat >> "$REPORT_DIR/report.html" << EOF
        </ul>
        
        <h2>Passi per la correzione</h2>
        <ol>
            <li>Assicurati che l'applicazione EvoRouter sia in esecuzione sulla porta 5000</li>
            <li>Verifica che Nginx sia configurato correttamente per fare da proxy all'applicazione</li>
            <li>Controlla che non ci siano configurazioni in conflitto che bloccano le richieste</li>
            <li>Riavvia Nginx dopo ogni modifica: sudo systemctl restart nginx</li>
            <li>Controlla i log per identificare eventuali errori: sudo tail -f $ERROR_LOG</li>
        </ol>
        
        <h2>Supporto</h2>
        <p>Per assistenza specifica in base a questo report, contatta il supporto tecnico.</p>
    </div>
</body>
</html>
EOF

print_message "success" "Report di diagnostica generato in $REPORT_DIR/report.html"

# Creazione di uno script di correzione personalizzato
print_message "info" "Creazione di uno script di correzione personalizzato..."
REPAIR_SCRIPT="$REPORT_DIR/repair_nginx.sh"

cat > "$REPAIR_SCRIPT" << EOF
#!/bin/bash
#
# Script di correzione personalizzato generato da diagnose_nginx.sh
# Data: $(date)
#

# Funzione per visualizzare messaggi colorati
print_message() {
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
    
    case \$1 in
        "info")
            echo -e "\${BLUE}[INFO]\${NC} \$2"
            ;;
        "success")
            echo -e "\${GREEN}[SUCCESSO]\${NC} \$2"
            ;;
        "error")
            echo -e "\${RED}[ERRORE]\${NC} \$2"
            ;;
        "warning")
            echo -e "\${YELLOW}[AVVISO]\${NC} \$2"
            ;;
        *)
            echo "\$2"
            ;;
    esac
}

print_message "info" "Inizializzazione della riparazione di Nginx..."
EOF

# Aggiungi comandi di riparazione in base ai problemi rilevati
echo "# Verifica se Nginx è in esecuzione" >> "$REPAIR_SCRIPT"
echo "if ! systemctl is-active --quiet nginx; then" >> "$REPAIR_SCRIPT"
echo "    print_message \"info\" \"Avvio di Nginx...\"" >> "$REPAIR_SCRIPT"
echo "    systemctl start nginx" >> "$REPAIR_SCRIPT"
echo "fi" >> "$REPAIR_SCRIPT"
echo "" >> "$REPAIR_SCRIPT"

# Se il sito predefinito è abilitato ed è anche presente il sito EvoRouter, disabilita il sito predefinito
if [ -L "$SITES_ENABLED/default" ] && ([ -f "$EVOROUTER_SITE" ] || [ -L "$SITES_ENABLED/evorouter" ]); then
    echo "# Disabilitazione del sito predefinito per evitare conflitti" >> "$REPAIR_SCRIPT"
    echo "if [ -L \"$SITES_ENABLED/default\" ]; then" >> "$REPAIR_SCRIPT"
    echo "    print_message \"info\" \"Disabilitazione del sito predefinito per evitare conflitti...\"" >> "$REPAIR_SCRIPT"
    echo "    rm -f \"$SITES_ENABLED/default\"" >> "$REPAIR_SCRIPT"
    echo "fi" >> "$REPAIR_SCRIPT"
    echo "" >> "$REPAIR_SCRIPT"
fi

# Se non esiste il sito EvoRouter, crealo
if [ ! -f "$EVOROUTER_SITE" ]; then
    echo "# Creazione del file di configurazione per EvoRouter" >> "$REPAIR_SCRIPT"
    echo "print_message \"info\" \"Creazione del file di configurazione per EvoRouter...\"" >> "$REPAIR_SCRIPT"
    echo "cat > \"$EVOROUTER_SITE\" << 'EOFEVOROUTER'" >> "$REPAIR_SCRIPT"
    echo "server {" >> "$REPAIR_SCRIPT"
    echo "    listen 80 default_server;" >> "$REPAIR_SCRIPT"
    echo "    listen [::]:80 default_server;" >> "$REPAIR_SCRIPT"
    echo "    server_name _;" >> "$REPAIR_SCRIPT"
    echo "" >> "$REPAIR_SCRIPT"
    echo "    # Impostazioni generali" >> "$REPAIR_SCRIPT"
    echo "    root /var/www/html;" >> "$REPAIR_SCRIPT"
    echo "    index index.html index.htm;" >> "$REPAIR_SCRIPT"
    echo "    " >> "$REPAIR_SCRIPT"
    echo "    # Aumenta il buffer per le intestazioni" >> "$REPAIR_SCRIPT"
    echo "    large_client_header_buffers 4 32k;" >> "$REPAIR_SCRIPT"
    echo "    " >> "$REPAIR_SCRIPT"
    echo "    # Configurazione del proxy per l'applicazione EvoRouter" >> "$REPAIR_SCRIPT"
    echo "    location / {" >> "$REPAIR_SCRIPT"
    echo "        proxy_pass http://127.0.0.1:5000;" >> "$REPAIR_SCRIPT"
    echo "        proxy_set_header Host \$host;" >> "$REPAIR_SCRIPT"
    echo "        proxy_set_header X-Real-IP \$remote_addr;" >> "$REPAIR_SCRIPT"
    echo "        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;" >> "$REPAIR_SCRIPT"
    echo "        proxy_set_header X-Forwarded-Proto \$scheme;" >> "$REPAIR_SCRIPT"
    echo "        " >> "$REPAIR_SCRIPT"
    echo "        # Timeout estesi per operazioni di lunga durata" >> "$REPAIR_SCRIPT"
    echo "        proxy_connect_timeout 300s;" >> "$REPAIR_SCRIPT"
    echo "        proxy_send_timeout 300s;" >> "$REPAIR_SCRIPT"
    echo "        proxy_read_timeout 300s;" >> "$REPAIR_SCRIPT"
    echo "        " >> "$REPAIR_SCRIPT"
    echo "        # Buffering migliorato" >> "$REPAIR_SCRIPT"
    echo "        proxy_buffer_size 128k;" >> "$REPAIR_SCRIPT"
    echo "        proxy_buffers 4 256k;" >> "$REPAIR_SCRIPT"
    echo "        proxy_busy_buffers_size 256k;" >> "$REPAIR_SCRIPT"
    echo "        " >> "$REPAIR_SCRIPT"
    echo "        # Gestione degli errori quando il backend non è disponibile" >> "$REPAIR_SCRIPT"
    echo "        proxy_intercept_errors on;" >> "$REPAIR_SCRIPT"
    echo "        error_page 502 503 504 /50x.html;" >> "$REPAIR_SCRIPT"
    echo "    }" >> "$REPAIR_SCRIPT"
    echo "    " >> "$REPAIR_SCRIPT"
    echo "    # Pagina di errore personalizzata quando l'applicazione non è raggiungibile" >> "$REPAIR_SCRIPT"
    echo "    location = /50x.html {" >> "$REPAIR_SCRIPT"
    echo "        root /var/www/html;" >> "$REPAIR_SCRIPT"
    echo "        internal;" >> "$REPAIR_SCRIPT"
    echo "    }" >> "$REPAIR_SCRIPT"
    echo "    " >> "$REPAIR_SCRIPT"
    echo "    # Permettere l'accesso alle risorse statiche direttamente" >> "$REPAIR_SCRIPT"
    echo "    location /static/ {" >> "$REPAIR_SCRIPT"
    echo "        alias $INSTALL_DIR/static/;" >> "$REPAIR_SCRIPT"
    echo "        expires 7d;" >> "$REPAIR_SCRIPT"
    echo "    }" >> "$REPAIR_SCRIPT"
    echo "}" >> "$REPAIR_SCRIPT"
    echo "EOFEVOROUTER" >> "$REPAIR_SCRIPT"
    echo "" >> "$REPAIR_SCRIPT"
elif ! grep -q "proxy_pass.*127.0.0.1:5000" "$EVOROUTER_SITE"; then
    # Se il sito esiste ma non contiene proxy_pass, aggiornalo
    echo "# Aggiornamento della configurazione per includere proxy_pass" >> "$REPAIR_SCRIPT"
    echo "print_message \"info\" \"Aggiornamento della configurazione per includere proxy_pass...\"" >> "$REPAIR_SCRIPT"
    echo "sed -i '/location \\/ {/a\\        proxy_pass http://127.0.0.1:5000;' \"$EVOROUTER_SITE\"" >> "$REPAIR_SCRIPT"
    echo "" >> "$REPAIR_SCRIPT"
fi

# Se il sito EvoRouter non è abilitato, abilitalo
if [ ! -L "$SITES_ENABLED/evorouter" ] && [ -f "$EVOROUTER_SITE" ]; then
    echo "# Abilitazione del sito EvoRouter" >> "$REPAIR_SCRIPT"
    echo "if [ ! -L \"$SITES_ENABLED/evorouter\" ]; then" >> "$REPAIR_SCRIPT"
    echo "    print_message \"info\" \"Abilitazione del sito EvoRouter...\"" >> "$REPAIR_SCRIPT"
    echo "    ln -sf \"$EVOROUTER_SITE\" \"$SITES_ENABLED/\"" >> "$REPAIR_SCRIPT"
    echo "fi" >> "$REPAIR_SCRIPT"
    echo "" >> "$REPAIR_SCRIPT"
fi

# Aggiungi comandi finali di verifica e riavvio
cat >> "$REPAIR_SCRIPT" << EOF
# Verifica della configurazione di Nginx
print_message "info" "Verifica della configurazione di Nginx..."
nginx -t
if [ \$? -ne 0 ]; then
    print_message "error" "La configurazione di Nginx contiene errori. Verifica manualmente."
    exit 1
fi

# Riavvio di Nginx
print_message "info" "Riavvio di Nginx..."
systemctl restart nginx
if [ \$? -ne 0 ]; then
    print_message "error" "Impossibile riavviare Nginx. Verifica manualmente."
    exit 1
fi

# Verifica dell'applicazione EvoRouter
print_message "info" "Verifica se l'applicazione EvoRouter è in esecuzione..."
if ! netstat -tuln | grep -q ":5000" && ! ss -tuln | grep -q ":5000"; then
    print_message "warning" "L'applicazione EvoRouter non sembra essere in esecuzione sulla porta 5000."
    
    if systemctl list-unit-files | grep -q evorouter.service; then
        print_message "info" "Tentativo di avvio del servizio evorouter.service..."
        systemctl restart evorouter.service
    else
        print_message "warning" "Il servizio evorouter.service non è definito nel sistema."
        print_message "info" "È necessario avviare manualmente l'applicazione EvoRouter."
    fi
else
    print_message "success" "L'applicazione EvoRouter è in esecuzione sulla porta 5000."
fi

# Test di connettività
print_message "info" "Test di connettività a localhost (porta 80)..."
curl -s -o /dev/null -w "%{http_code}" localhost
HTTP_CODE=\$?
if [ \$HTTP_CODE -eq 0 ]; then
    print_message "success" "Connessione a localhost (porta 80) riuscita."
    print_message "success" "Riparazione completata con successo!"
else
    print_message "error" "Ancora problemi con la connessione a localhost."
    print_message "info" "Potrebbero essere necessari ulteriori interventi manuali."
fi

print_message "info" "Per un'analisi più approfondita, esegui nuovamente diagnose_nginx.sh dopo la riparazione."
EOF

chmod +x "$REPAIR_SCRIPT"
print_message "success" "Script di riparazione creato in $REPAIR_SCRIPT"

# Suggerimenti finali
print_message "info" ""
print_message "info" "Diagnostica completata. Ecco i risultati principali:"
print_message "info" ""

if [ $NGINX_CONFIG_OK -eq 0 ]; then
    print_message "success" "✅ La configurazione di Nginx è valida."
else
    print_message "error" "❌ La configurazione di Nginx contiene errori."
fi

if [ "$NGINX_RUNNING" = true ]; then
    print_message "success" "✅ Nginx è in esecuzione."
else
    print_message "error" "❌ Nginx non è in esecuzione."
fi

if command -v netstat &> /dev/null && netstat -tuln | grep -q ":5000" || command -v ss &> /dev/null && ss -tuln | grep -q ":5000"; then
    print_message "success" "✅ L'applicazione è in ascolto sulla porta 5000."
else
    print_message "error" "❌ Nessuna applicazione in ascolto sulla porta 5000."
fi

print_message "info" ""
print_message "info" "Il report completo è disponibile in $REPORT_DIR/report.html"
print_message "info" "Uno script di riparazione personalizzato è stato creato in $REPAIR_SCRIPT"
print_message "info" ""
print_message "info" "Per eseguire lo script di riparazione:"
print_message "info" "sudo $REPAIR_SCRIPT"
print_message "info" ""
print_message "info" "Dopo la riparazione, verifica nuovamente accedendo a http://localhost/ nel browser."
print_message "info" ""

exit 0