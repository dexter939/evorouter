#!/bin/bash
# Script per creare un bundle Git per il repository GitHub di EvoRouter R4 OS

echo "Creazione del bundle Git per EvoRouter R4 OS v1.3.0..."

# Nome del file bundle
BUNDLE_FILE="evorouter.bundle"

# Crea il bundle Git
echo "Creando il bundle Git..."
git bundle create $BUNDLE_FILE --all

echo "Bundle creato con successo: $BUNDLE_FILE"
echo ""
echo "Per inviare questo bundle su GitHub:"
echo "1. Copia il file $BUNDLE_FILE sul computer con accesso a GitHub"
echo "2. Esegui: git clone $BUNDLE_FILE evorouter-temp"
echo "3. Entra nella directory: cd evorouter-temp"
echo "4. Aggiungi il remote di GitHub: git remote add github https://github.com/dexter939/evorouter.git"
echo "5. Esegui il push: git push github main"
echo ""
echo "Nota: Assicurati di avere i permessi necessari per eseguire il push sul repository GitHub."