#!/bin/bash
#
# Script per creare un bundle completo per il repository GitHub
# Questo script assembla tutti i file necessari per il repository GitHub
# escludendo file temporanei e di ambiente
#

# Directory di output
OUTPUT_DIR="./github_bundle"
BUNDLE_FILE="evorouter.bundle"

# Colori per i messaggi
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}[INFO]${NC} Creazione bundle per GitHub..."

# Crea la directory di output se non esiste
mkdir -p $OUTPUT_DIR

# Lista di file e directory da escludere
EXCLUDE=(
    "__pycache__"
    "*.pyc"
    ".git"
    ".pytest_cache"
    "venv"
    "*.db"
    "*.db-journal"
    "instance/*.db"
    "*.log"
    "github_bundle"
    $OUTPUT_DIR
    $BUNDLE_FILE
    "*.swp"
    "*.tmp"
    ".DS_Store"
)

# Costruisce la stringa di esclusione per rsync
EXCLUDES=""
for item in "${EXCLUDE[@]}"; do
    EXCLUDES="$EXCLUDES --exclude='$item'"
done

# Copia tutti i file nel bundle, escludendo quelli nella lista
echo -e "${BLUE}[INFO]${NC} Copiando i file nel bundle..."

# Pulizia della directory di output
rm -rf $OUTPUT_DIR
mkdir -p $OUTPUT_DIR

# Uso di find e cp per copiare i file, escludendo quelli non necessari
echo -e "${BLUE}[INFO]${NC} Creando lista di file da copiare..."
find . -type f -not -path "*/\.*" \
    -not -path "*/venv/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/instance/*" \
    -not -path "*/.pytest_cache/*" \
    -not -path "*/github_bundle/*" \
    -not -name "*.pyc" \
    -not -name "*.db" \
    -not -name "*.db-journal" \
    -not -name "*.log" \
    -not -name $BUNDLE_FILE \
    -not -name "*.swp" \
    -not -name "*.tmp" \
    -not -name ".DS_Store" \
    | while read file; do
        # Crea la directory di destinazione se non esiste
        dir=$(dirname "$file")
        mkdir -p "$OUTPUT_DIR/$dir"
        # Copia il file
        cp "$file" "$OUTPUT_DIR/$file"
        echo "Copiato: $file"
    done

# Aggiorna i riferimenti all'URL del repository nei file
echo -e "${BLUE}[INFO]${NC} Aggiornando i riferimenti all'URL del repository..."
sed -i 's|https://github.com/YOUR-USERNAME/evorouter.git|https://github.com/dexter939/evorouter.git|g' $OUTPUT_DIR/README.md $OUTPUT_DIR/INSTALL.md $OUTPUT_DIR/install_evorouter.sh $OUTPUT_DIR/install_evorouter_complete.sh 2>/dev/null || true

# Crea un archivio compresso del bundle
echo -e "${BLUE}[INFO]${NC} Creando l'archivio compresso..."
cd $OUTPUT_DIR
tar -czf ../$BUNDLE_FILE ./*
cd ..

echo -e "${GREEN}[SUCCESSO]${NC} Bundle creato con successo: $BUNDLE_FILE"
echo ""
echo -e "${BLUE}[INFO]${NC} Per caricare su GitHub:"
echo "1. Crea un nuovo repository su GitHub (https://github.com/new)"
echo "2. Clona il repository vuoto"
echo "3. Estrai il bundle nel repository locale"
echo "4. Commit e push dei cambiamenti"
echo ""
echo "Comandi di esempio:"
echo "  git clone https://github.com/dexter939/evorouter.git"
echo "  cd evorouter"
echo "  tar -xzf ../$BUNDLE_FILE"
echo "  git add ."
echo "  git commit -m \"Versione iniziale di EvoRouter R4 OS v1.4.0\""
echo "  git push origin main"
echo ""
echo -e "${BLUE}[INFO]${NC} Il bundle è pronto per l'uso."

exit 0