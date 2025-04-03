#!/bin/bash
#
# Script per creare un bundle di installazione da un repository GitHub
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

print_message "info" "#############################################"
print_message "info" "##                                         ##"
print_message "info" "##  CREAZIONE BUNDLE GITHUB               ##"
print_message "info" "##  EvoRouter R4 OS                       ##"
print_message "info" "##                                         ##"
print_message "info" "#############################################"
print_message "info" ""
print_message "info" "Questo script creerà un bundle di installazione dal repository Git locale."

# Verifica se git è installato
if ! command -v git &> /dev/null; then
    print_message "error" "Git non è installato. Installalo con 'apt install git' e riprova."
    exit 1
fi

# Verifica se siamo in una directory git
if [ ! -d ".git" ]; then
    print_message "error" "Questa directory non è un repository Git."
    print_message "info" "Esegui questo script dalla directory principale del repository Git."
    exit 1
fi

# Determina il nome del repository
REPO_NAME=$(basename -s .git $(git config --get remote.origin.url 2>/dev/null) || basename $(pwd))

# Chiedi conferma prima di continuare
print_message "info" "Verrà creato un bundle per il repository '$REPO_NAME'"
read -p "Continuare? (s/n): " confirm
if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    print_message "info" "Operazione annullata."
    exit 0
fi

# Verifica lo stato del repository
print_message "info" "Verifica delle modifiche non salvate..."
if ! git diff-index --quiet HEAD --; then
    print_message "warning" "Ci sono modifiche non confermate nel repository."
    print_message "info" "Ti consigliamo di eseguire 'git commit' prima di creare il bundle."
    read -p "Vuoi continuare comunque? (s/n): " continue_anyway
    if [ "$continue_anyway" != "s" ] && [ "$continue_anyway" != "S" ]; then
        print_message "info" "Operazione annullata."
        exit 0
    fi
fi

# Ottieni il ramo corrente
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
print_message "info" "Utilizzerò il ramo corrente: $CURRENT_BRANCH"

# Crea il bundle
OUTPUT_FILE="${REPO_NAME}.bundle"
print_message "info" "Creazione del bundle $OUTPUT_FILE..."
git bundle create "$OUTPUT_FILE" $CURRENT_BRANCH --all
check_command "Impossibile creare il bundle Git."

# Crea un file README per il bundle
README_FILE="README_${REPO_NAME}.txt"
print_message "info" "Creazione del file di istruzioni $README_FILE..."

cat > "$README_FILE" << EOF
BUNDLE DI INSTALLAZIONE PER $REPO_NAME
================================================

Questo bundle contiene una copia del repository Git per $REPO_NAME.
Data di creazione: $(date +%d/%m/%Y)
Ramo principale: $CURRENT_BRANCH

ISTRUZIONI PER L'INSTALLAZIONE:
--------------------------------

1. Copia questo file bundle sul dispositivo di destinazione
2. Esegui i seguenti comandi:

   mkdir -p /opt/evorouter
   cd /opt/evorouter
   git clone $OUTPUT_FILE evorouter
   cd evorouter
   
   # Per eseguire l'installazione
   sudo ./install_evorouter.sh
   
   # Oppure, se preferisci usare lo script per Ubuntu/Debian
   sudo ./install_evorouter_ubuntu.sh

Per maggiori informazioni, consulta il file INSTALL.md nella root del repository.

EOF
check_command "Impossibile creare il file README."

print_message "success" "Bundle creato con successo!"
print_message "info" "Bundle: $OUTPUT_FILE"
print_message "info" "Istruzioni: $README_FILE"
print_message "info" ""
print_message "info" "Per utilizzare il bundle, copia entrambi i file sul dispositivo di destinazione e segui le istruzioni nel file README."

exit 0