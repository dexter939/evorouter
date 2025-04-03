#!/bin/bash
#
# Script di disinstallazione per EvoRouter R4 OS
# Questo script automatizza il processo di disinstallazione completa del sistema
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

print_message "info" "#############################################"
print_message "info" "##                                         ##"
print_message "info" "##  DISINSTALLAZIONE EvoRouter R4 OS      ##"
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "warning" "ATTENZIONE: Questa operazione rimuoverà completamente EvoRouter R4 OS e tutti i dati associati."
print_message "warning" "I dati eliminati non potranno essere recuperati!"

# Chiedi conferma prima di continuare
read -p "Sei sicuro di voler procedere con la disinstallazione? (s/n): " confirm
if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    print_message "info" "Disinstallazione annullata."
    exit 0
fi

# Chiedi un'ulteriore conferma
read -p "Confermi di voler rimuovere EvoRouter R4 OS dal sistema? (s/n): " confirm2
if [ "$confirm2" != "s" ] && [ "$confirm2" != "S" ]; then
    print_message "info" "Disinstallazione annullata."
    exit 0
fi

# Arresto dei servizi
print_message "info" "Arresto dei servizi EvoRouter..."
systemctl stop evorouter.service
systemctl disable evorouter.service

# Verifica presenza FreeSWITCH e arrestalo se presente
if systemctl is-active --quiet freeswitch.service; then
    print_message "info" "Arresto del servizio FreeSWITCH..."
    systemctl stop freeswitch.service
    systemctl disable freeswitch.service
fi

# Rimozione della configurazione del servizio
print_message "info" "Rimozione della configurazione del servizio..."
rm -f /etc/systemd/system/evorouter.service
systemctl daemon-reload

# Creazione opzionale di backup prima della disinstallazione
read -p "Vuoi creare un backup dei dati prima della disinstallazione? (s/n): " backup_confirm
if [ "$backup_confirm" = "s" ] || [ "$backup_confirm" = "S" ]; then
    BACKUP_DIR="/opt/evorouter_backup_before_uninstall_$(date +%Y%m%d_%H%M%S)"
    print_message "info" "Creazione del backup in $BACKUP_DIR..."
    mkdir -p $BACKUP_DIR
    
    # Copia tutti i file nella directory di backup
    if [ -d "$INSTALL_DIR" ]; then
        cp -r $INSTALL_DIR/* $BACKUP_DIR/ 2>/dev/null
        cp -r $INSTALL_DIR/.* $BACKUP_DIR/ 2>/dev/null || true
        print_message "success" "Backup completato con successo!"
    else
        print_message "warning" "Directory di installazione non trovata. Nessun backup creato."
    fi
fi

# Rimuovi la directory di installazione
print_message "info" "Rimozione dei file dell'applicazione..."
rm -rf $INSTALL_DIR

# Rimuovi eventuali backup se l'utente lo desidera
if [ "$backup_confirm" != "s" ] && [ "$backup_confirm" != "S" ]; then
    read -p "Vuoi rimuovere anche tutti i backup precedenti? (s/n): " remove_backups
    if [ "$remove_backups" = "s" ] || [ "$remove_backups" = "S" ]; then
        print_message "info" "Rimozione di tutti i backup precedenti..."
        rm -rf /opt/evorouter_backup_*
    else
        print_message "info" "I backup precedenti sono stati mantenuti in /opt/evorouter_backup_*"
    fi
fi

# Rimozione della configurazione di Nginx
print_message "info" "Rimozione delle configurazioni di Nginx..."
if [ -f "/etc/nginx/sites-enabled/evorouter" ]; then
    rm -f /etc/nginx/sites-enabled/evorouter
    print_message "success" "Configurazione Nginx rimossa."
fi

if [ -f "/etc/nginx/sites-available/evorouter" ]; then
    rm -f /etc/nginx/sites-available/evorouter
    print_message "success" "File di configurazione Nginx rimosso."
fi

# Riavvio di Nginx
if systemctl is-active --quiet nginx.service; then
    print_message "info" "Riavvio del servizio Nginx..."
    systemctl restart nginx
fi

# Pulizia dei file di log
print_message "info" "Pulizia dei file di log..."
rm -f /var/log/evorouter*

# Rimozione di FreeSWITCH se l'utente lo desidera
if dpkg -l | grep -q freeswitch; then
    read -p "Vuoi disinstallare anche FreeSWITCH? (s/n): " remove_freeswitch
    if [ "$remove_freeswitch" = "s" ] || [ "$remove_freeswitch" = "S" ]; then
        print_message "info" "Disinstallazione di FreeSWITCH..."
        apt-get remove --purge -y freeswitch*
        apt-get autoremove -y
        print_message "success" "FreeSWITCH disinstallato."
    else
        print_message "info" "FreeSWITCH è stato mantenuto sul sistema."
    fi
fi

# Informazioni finali
print_message "success" "##############################################"
print_message "success" "Disinstallazione di EvoRouter R4 OS completata!"
print_message "success" "##############################################"

if [ "$backup_confirm" = "s" ] || [ "$backup_confirm" = "S" ]; then
    print_message "info" "Un backup è stato creato in: $BACKUP_DIR"
    print_message "info" "Se non hai più bisogno di questo backup, puoi rimuoverlo con:"
    print_message "info" "  rm -rf $BACKUP_DIR"
fi

print_message "info" ""
print_message "info" "Nota: Potrebbe essere necessario riconfigurare le impostazioni di rete"
print_message "info" "del dispositivo per ripristinare le funzionalità di base del router."
print_message "info" ""
print_message "info" "Grazie per aver utilizzato EvoRouter R4 OS!"

exit 0