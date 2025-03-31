# Guida alla Migrazione su GitHub per EvoRouter R4 OS

Questa guida spiega come migrare il progetto EvoRouter R4 OS su GitHub. Il processo è progettato per essere semplice e diretto.

## Prerequisiti

Prima di iniziare, assicurati di avere:

1. Un account GitHub (registrati su https://github.com/join se non ne hai uno)
2. Git installato sul tuo computer (https://git-scm.com/downloads)
3. Conoscenze di base dei comandi Git

## Procedura passo-passo

### 1. Download del bundle

**Il bundle è già stato creato**. Per scaricare il file `evorouter.bundle`:

1. Vai alla sezione "Files" nel pannello a sinistra di Replit
2. Trova il file `evorouter.bundle`
3. Clicca con il tasto destro sul file
4. Seleziona "Download" dal menu contestuale
5. Salva il file sul tuo computer locale

### 2. Crea un nuovo repository su GitHub

1. Vai su https://github.com/new
2. Inserisci "evorouter" come nome del repository
3. Opzionalmente, aggiungi una descrizione (esempio: "Sistema operativo personalizzato per router EvoRouter R4")
4. Scegli se il repository deve essere pubblico o privato
5. **NON** selezionare l'opzione per inizializzare il repository con README o .gitignore
6. Clicca su "Create repository"

### 3. Clone e popolazione del repository

Dopo aver creato il repository vuoto, procedi con questi comandi:

```bash
# Clona il repository vuoto
git clone https://github.com/TUO-USERNAME/evorouter.git
cd evorouter

# Estrai il bundle nel repository
tar -xzf /percorso/al/evorouter.bundle
```

Sostituisci `TUO-USERNAME` con il tuo nome utente GitHub e aggiusta `/percorso/al/evorouter.bundle` con il percorso completo al file bundle.

### 4. Commit e push iniziale

Ora completa l'operazione con il primo commit e push:

```bash
# Aggiungi tutti i file
git add .

# Crea il commit iniziale
git commit -m "Versione iniziale di EvoRouter R4 OS v1.4.0"

# Invia i cambiamenti al repository remoto
git push origin main
```

### 5. Verifica

Visita `https://github.com/TUO-USERNAME/evorouter` nel tuo browser per verificare che tutti i file siano stati caricati correttamente.

## Note aggiuntive

- **Wiki**: Considera di attivare la Wiki del repository per documentazione aggiuntiva
- **Issues**: Abilita la sezione Issues per tracciare bug e richieste di funzionalità
- **Releases**: Crea una release ufficiale v1.4.0 taggando il commit

## Aggiornamenti futuri

Per aggiornare il repository in futuro, puoi utilizzare il normale flusso di lavoro Git:

```bash
# Aggiungi i file modificati
git add .

# Crea un nuovo commit
git commit -m "Descrizione delle modifiche"

# Invia i cambiamenti al repository remoto
git push origin main
```

## Configurazione di GitHub Pages (opzionale)

Se desideri creare un sito web per il progetto:

1. Vai alle impostazioni del repository
2. Scorri fino alla sezione "GitHub Pages"
3. Seleziona il branch "main" e la cartella "/docs" (se hai documentazione nella cartella docs)
4. Clicca su "Save"

Il sito sarà disponibile all'indirizzo `https://TUO-USERNAME.github.io/evorouter`.