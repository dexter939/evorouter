#!/bin/bash
#
# Script di installazione automatica per FreeSWITCH su EvoRouter R4
# Questo script aggiunge i repository necessari e installa FreeSWITCH con tutti i moduli richiesti
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

# Verifica se lo script è eseguito come root
if [ "$(id -u)" != "0" ]; then
   print_message "error" "Questo script deve essere eseguito come root (sudo)!"
   exit 1
fi

print_message "info" "Inizializzazione dell'installazione di FreeSWITCH su EvoRouter R4..."
print_message "info" "Questo processo potrebbe richiedere alcuni minuti."

# Aggiornamento dei repository
print_message "info" "Aggiornamento delle liste dei pacchetti..."
apt-get update || {
    print_message "error" "Impossibile aggiornare le liste dei pacchetti. Verifica la connessione internet."
    exit 1
}

# Installazione delle dipendenze necessarie
print_message "info" "Installazione delle dipendenze necessarie..."
apt-get install -y gnupg2 wget lsb-release ca-certificates apt-transport-https || {
    print_message "error" "Impossibile installare le dipendenze necessarie."
    exit 1
}

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
apt-get update || {
    print_message "error" "Impossibile aggiornare le liste dei pacchetti dopo l'aggiunta del repository FreeSWITCH."
    exit 1
}

# Installazione di FreeSWITCH e dei moduli necessari
print_message "info" "Installazione di FreeSWITCH e dei moduli necessari..."
apt-get install -y freeswitch freeswitch-meta-all || {
    print_message "error" "Impossibile installare FreeSWITCH. Tentativo con singoli moduli..."
    
    # Tentativo di installazione dei moduli principali singolarmente
    apt-get install -y freeswitch freeswitch-mod-console freeswitch-mod-sofia freeswitch-mod-voicemail \
    freeswitch-mod-loopback freeswitch-mod-commands freeswitch-mod-conference freeswitch-mod-db \
    freeswitch-mod-dptools freeswitch-mod-hash freeswitch-mod-esf freeswitch-mod-dialplan-xml \
    freeswitch-mod-sndfile freeswitch-mod-native-file freeswitch-mod-local-stream freeswitch-mod-tone-stream \
    freeswitch-mod-lua freeswitch-mod-spandsp || {
        print_message "error" "Installazione fallita. Tentativo di compilazione dai sorgenti..."
        
        # Se anche questo fallisce, offriamo la possibilità di compilare dai sorgenti
        print_message "warning" "Per compilare FreeSWITCH dai sorgenti, esegui lo script install_freeswitch_from_source.sh"
        exit 1
    }
}

# Configurazione del servizio FreeSWITCH
print_message "info" "Configurazione del servizio FreeSWITCH..."
systemctl enable freeswitch || {
    print_message "warning" "Impossibile abilitare il servizio FreeSWITCH all'avvio."
}

# Avvio del servizio FreeSWITCH
print_message "info" "Avvio del servizio FreeSWITCH..."
systemctl start freeswitch || {
    print_message "warning" "Impossibile avviare il servizio FreeSWITCH. Verifica lo stato con 'systemctl status freeswitch'."
}

# Verifica dello stato finale
if systemctl is-active --quiet freeswitch; then
    print_message "success" "FreeSWITCH è stato installato e avviato con successo!"
    print_message "info" "Puoi verificare lo stato del servizio con: systemctl status freeswitch"
    print_message "info" "Puoi accedere alla console di FreeSWITCH con: fs_cli"
else
    print_message "warning" "FreeSWITCH è stato installato ma il servizio non risulta attivo."
    print_message "info" "Verifica lo stato del servizio con: systemctl status freeswitch"
fi

# Informazioni aggiuntive
print_message "info" "Configurazione base di FreeSWITCH disponibile in: /etc/freeswitch/"
print_message "info" "Suoni e registrazioni disponibili in: /usr/share/freeswitch/sounds/"
print_message "info" "Log di sistema disponibili in: /var/log/freeswitch/"

print_message "success" "Installazione di FreeSWITCH completata!"
exit 0