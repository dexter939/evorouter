#!/bin/bash
# Script per creare un pacchetto di deployment per EvoRouter R4 OS

echo "Creazione del pacchetto di deployment per EvoRouter R4 OS..."

# Crea directory temporanea
TEMP_DIR="./deployment_tmp"
DEPLOY_PKG="evorouter_os.zip"

mkdir -p $TEMP_DIR

# Copia i file necessari
echo "Copiando i file essenziali..."
cp -r app.py main.py models.py config.py create_admin.py reset_admin_password.py $TEMP_DIR/
cp -r routes/ forms/ utils/ static/ templates/ $TEMP_DIR/
cp -r instance/ $TEMP_DIR/
mkdir -p $TEMP_DIR/logs

# Crea file requirements.txt
echo "Creando requirements.txt..."
cat > $TEMP_DIR/requirements.txt << EOL
flask
flask-login
flask-jwt-extended
flask-sqlalchemy
flask-wtf
gunicorn
psutil
psycopg2-binary
email-validator
EOL

# Copia la guida all'installazione
cp INSTALL.md $TEMP_DIR/

# Crea uno script di installazione
echo "Creando script di installazione..."
cat > $TEMP_DIR/install.sh << EOL
#!/bin/bash
# Script di installazione per EvoRouter R4 OS

echo "Installazione di EvoRouter R4 OS in corso..."

# Verifica se l'utente è root
if [ "\$(id -u)" -ne 0 ]; then
    echo "Questo script deve essere eseguito come root"
    exit 1
fi

# Directory di installazione
INSTALL_DIR="/opt/evorouter"
mkdir -p \$INSTALL_DIR

# Installa dipendenze di sistema
echo "Installazione delle dipendenze di sistema..."
apt update
apt install -y python3 python3-pip python3-venv nginx

# Crea e configura ambiente virtuale Python
echo "Configurazione dell'ambiente Python..."
python3 -m venv \$INSTALL_DIR/venv
source \$INSTALL_DIR/venv/bin/activate
pip install -r requirements.txt

# Copia i file nell'ubicazione di installazione
echo "Copiando i file nell'ubicazione di installazione..."
cp -r app.py main.py models.py config.py create_admin.py $TEMP_DIR/
cp -r routes/ forms/ utils/ static/ templates/ \$INSTALL_DIR/
cp -r instance/ \$INSTALL_DIR/
mkdir -p \$INSTALL_DIR/logs

# Crea utente admin se non esiste
echo "Inizializzazione del database..."
cd \$INSTALL_DIR
source venv/bin/activate
python create_admin.py

# Configura Nginx
echo "Configurazione di Nginx..."
cat > /etc/nginx/sites-available/evorouter << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/evorouter /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Configura systemd
echo "Configurazione del servizio systemd..."
cat > /etc/systemd/system/evorouter.service << EOF
[Unit]
Description=EvoRouter R4 OS
After=network.target

[Service]
User=root
WorkingDirectory=/opt/evorouter
ExecStart=/opt/evorouter/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable evorouter.service
systemctl start evorouter.service

echo "Installazione completata!"
echo "Puoi accedere all'interfaccia web tramite http://indirizzo-ip-del-dispositivo/"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "Si consiglia vivamente di cambiare la password al primo accesso."
EOL

# Rendi lo script eseguibile
chmod +x $TEMP_DIR/install.sh

# Crea il pacchetto ZIP
echo "Creando il pacchetto ZIP..."
cd $TEMP_DIR
zip -r ../$DEPLOY_PKG .
cd ..

# Pulizia
echo "Pulizia dei file temporanei..."
rm -rf $TEMP_DIR

echo "Pacchetto di deployment creato con successo: $DEPLOY_PKG"
echo "Puoi trasferire questo pacchetto al dispositivo EvoRouter R4 e seguire le istruzioni in INSTALL.md per l'installazione."