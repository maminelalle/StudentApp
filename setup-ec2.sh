#!/bin/bash
# Script de démarrage automatique pour l'application StudentApp en AWS

# Mettre à jour le système
sudo apt update
sudo apt upgrade -y

# Installer Python et dépendances
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Créer le répertoire de l'application
cd /home/ubuntu
mkdir -p StudentApp
cd StudentApp

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
pip install --upgrade pip
pip install Flask==3.0.2 SQLAlchemy==2.0.29 openpyxl==3.1.2 boto3==1.34.0 pymysql==1.1.0 cryptography==42.0.0

# Créer le service systemd pour démarrer automatiquement l'app
sudo tee /etc/systemd/system/studentapp.service > /dev/null << EOF
[Unit]
Description=StudentApp Flask Application
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/StudentApp
Environment="PATH=/home/ubuntu/StudentApp/venv/bin"
ExecStart=/home/ubuntu/StudentApp/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Recharger systemd et activer le service
sudo systemctl daemon-reload
sudo systemctl enable studentapp

# Créer le répertoire de logs
sudo touch /var/log/studentapp.log
sudo chown ubuntu:ubuntu /var/log/studentapp.log

echo "Setup script terminé. Prêt à lancer l'application!"
echo "Les fichiers de l'application doivent être copiés dans /home/ubuntu/StudentApp/"
