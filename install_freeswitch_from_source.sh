#!/bin/bash
#
# Script di installazione di FreeSWITCH dai sorgenti per EvoRouter R4
# Questo script compila e installa FreeSWITCH dai sorgenti ufficiali
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

print_message "info" "Inizializzazione dell'installazione di FreeSWITCH dai sorgenti su EvoRouter R4..."
print_message "warning" "Questo processo richiederà diverso tempo e risorse. Assicurati che il sistema non venga spento durante l'installazione."

# Directory di lavoro per la compilazione
WORK_DIR="/usr/src/freeswitch-build"
mkdir -p $WORK_DIR
cd $WORK_DIR

# Aggiornamento del sistema
print_message "info" "Aggiornamento del sistema..."
apt-get update && apt-get upgrade -y || {
    print_message "error" "Impossibile aggiornare il sistema."
    exit 1
}

# Installazione delle dipendenze per la compilazione
print_message "info" "Installazione delle dipendenze per la compilazione..."
apt-get install -y build-essential cmake automake autoconf libtool libtool-bin pkg-config \
    libssl-dev zlib1g-dev libjpeg-dev libsqlite3-dev libcurl4-openssl-dev libpcre3-dev \
    libspeexdsp-dev libldns-dev libedit-dev libtiff-dev yasm libopus-dev libsndfile1-dev \
    libshout3-dev libmpg123-dev libmp3lame-dev libvorbis-dev libvlc-dev libavformat-dev \
    libswscale-dev libavresample-dev liblua5.2-dev liblua5.2-0 python3-dev libpq-dev \
    unixodbc-dev libmariadb-dev-compat libmariadb-dev uuid-dev libcunit1-dev libcunit1 \
    libsofia-sip-ua-dev libspandsp-dev || {
    print_message "error" "Impossibile installare le dipendenze di compilazione."
    exit 1
}

# Clonazione del repository FreeSWITCH
print_message "info" "Download dei sorgenti di FreeSWITCH..."
cd $WORK_DIR
if [ -d "freeswitch" ]; then
    cd freeswitch
    git pull
else
    git clone -b v1.10 https://github.com/signalwire/freeswitch.git freeswitch || {
        print_message "error" "Impossibile scaricare i sorgenti di FreeSWITCH."
        exit 1
    }
    cd freeswitch
fi

# Generazione di configure
print_message "info" "Generazione dello script di configurazione..."
./bootstrap.sh -j || {
    print_message "error" "Impossibile generare lo script di configurazione."
    exit 1
}

# Configurazione
print_message "info" "Configurazione della build..."
./configure --enable-portable-binary --disable-dependency-tracking \
    --enable-core-pgsql-support --enable-core-odbc-support --enable-zrtp || {
    print_message "error" "Impossibile configurare la build."
    exit 1
}

# Compilazione
print_message "info" "Compilazione di FreeSWITCH (questo processo richiederà del tempo)..."
make -j$(nproc) || {
    print_message "error" "Impossibile compilare FreeSWITCH."
    exit 1
}

# Installazione
print_message "info" "Installazione di FreeSWITCH..."
make install || {
    print_message "error" "Impossibile installare FreeSWITCH."
    exit 1
}

# Installazione audio
print_message "info" "Installazione dei file audio..."
make cd-sounds-install cd-moh-install || {
    print_message "warning" "Impossibile installare alcuni file audio."
}

# Configurazione post-installazione
print_message "info" "Configurazione post-installazione..."

# Creazione dell'utente e gruppo freeswitch
if ! getent group freeswitch > /dev/null; then
    groupadd --system freeswitch
fi
if ! getent passwd freeswitch > /dev/null; then
    adduser --quiet --system --home /usr/local/freeswitch --gecos "FreeSWITCH Voice Platform" --ingroup freeswitch freeswitch
fi

# Impostazione dei permessi corretti
chown -R freeswitch:freeswitch /usr/local/freeswitch/
chmod -R ug=rwX,o= /usr/local/freeswitch/
chmod -R u=rwx,g=rx /usr/local/freeswitch/bin/

# Creazione dei link simbolici
ln -sf /usr/local/freeswitch/bin/freeswitch /usr/bin/
ln -sf /usr/local/freeswitch/bin/fs_cli /usr/bin/

# Creazione di un servizio systemd
cat > /etc/systemd/system/freeswitch.service << EOF
[Unit]
Description=FreeSWITCH Open Source SoftSwitch
After=syslog.target network.target local-fs.target

[Service]
Type=forking
PIDFile=/usr/local/freeswitch/run/freeswitch.pid
Environment="DAEMON_OPTS=-nc"
EnvironmentFile=-/etc/default/freeswitch
ExecStart=/usr/bin/freeswitch -u freeswitch -g freeswitch -ncwait \$DAEMON_OPTS
TimeoutSec=45s
Restart=always
RestartSec=5s
User=root
WorkingDirectory=/usr/local/freeswitch
LimitCORE=infinity
LimitNOFILE=100000
LimitNPROC=60000
LimitSTACK=250000
LimitRTPRIO=infinity
LimitRTTIME=infinity
IOSchedulingClass=realtime
IOSchedulingPriority=2
CPUSchedulingPolicy=rr
CPUSchedulingPriority=89

[Install]
WantedBy=multi-user.target
EOF

# Creazione del file di configurazione per i limiti di sistema
cat > /etc/security/limits.d/freeswitch.conf << EOF
freeswitch       soft    nofile  999999
freeswitch       hard    nofile  999999
freeswitch       soft    nproc   unlimited
freeswitch       hard    nproc   unlimited
freeswitch       soft    core    unlimited
freeswitch       hard    core    unlimited
freeswitch       soft    memlock unlimited
freeswitch       hard    memlock unlimited
EOF

# Creazione del file di configurazione per sysctl
cat > /etc/sysctl.d/10-freeswitch.conf << EOF
# Aumenta il buffer di rete per prestazioni VoIP migliori
net.core.rmem_max = 16777216
net.core.rmem_default = 8388608
net.core.wmem_max = 16777216
net.core.wmem_default = 8388608
net.core.netdev_max_backlog = 5000
EOF

# Ricaricamento delle configurazioni
sysctl -p /etc/sysctl.d/10-freeswitch.conf
systemctl daemon-reload

# Abilitazione del servizio all'avvio
systemctl enable freeswitch.service

# Avvio del servizio
print_message "info" "Avvio del servizio FreeSWITCH..."
systemctl start freeswitch.service || {
    print_message "warning" "Impossibile avviare il servizio FreeSWITCH. Verifica lo stato con 'systemctl status freeswitch'."
}

# Verifica dello stato finale
if systemctl is-active --quiet freeswitch; then
    print_message "success" "FreeSWITCH è stato compilato, installato e avviato con successo!"
    print_message "info" "Puoi verificare lo stato del servizio con: systemctl status freeswitch"
    print_message "info" "Puoi accedere alla console di FreeSWITCH con: fs_cli"
else
    print_message "warning" "FreeSWITCH è stato compilato e installato ma il servizio non risulta attivo."
    print_message "info" "Verifica lo stato del servizio con: systemctl status freeswitch"
fi

# Pulizia
print_message "info" "Vuoi mantenere i sorgenti per future compilazioni? (s/n)"
read -r KEEP_SOURCES

if [[ $KEEP_SOURCES =~ ^[Nn]$ ]]; then
    print_message "info" "Rimozione dei sorgenti per liberare spazio..."
    rm -rf $WORK_DIR
    print_message "info" "Sorgenti rimossi con successo."
else
    print_message "info" "I sorgenti sono stati mantenuti in $WORK_DIR per future compilazioni."
fi

# Informazioni finali
print_message "info" "Configurazione di FreeSWITCH disponibile in: /usr/local/freeswitch/conf/"
print_message "info" "Suoni e registrazioni disponibili in: /usr/local/freeswitch/sounds/"
print_message "info" "Log di sistema disponibili in: /usr/local/freeswitch/log/"

print_message "success" "Installazione di FreeSWITCH dai sorgenti completata!"
exit 0