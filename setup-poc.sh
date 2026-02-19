#!/bin/bash
# Script d'installation pour Phase 2 - POC
# Ce script configure une instance EC2 Ubuntu pour héberger StudentApp

echo "=========================================="
echo "Installation de StudentApp - Phase 2 POC"
echo "=========================================="

# Mise à jour du système
echo "Mise à jour du système..."
sudo apt update
sudo apt upgrade -y

# Installation Python et pip
echo "Installation de Python et pip..."
sudo apt install python3 python3-pip python3-venv -y

# Installation de SQLite
echo "Installation de SQLite..."
sudo apt install sqlite3 -y

# Création du répertoire de l'application
echo "Création du répertoire de l'application..."
cd /home/ubuntu
mkdir -p StudentApp
cd StudentApp

# Créer l'environnement virtuel
echo "Création de l'environnement virtuel Python..."
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances Python
echo "Installation des dépendances Python..."
pip install --upgrade pip
pip install Flask==3.0.2
pip install SQLAlchemy==2.0.29
pip install openpyxl==3.1.2

# Message final
echo ""
echo "=========================================="
echo "✓ Installation terminée avec succès!"
echo "=========================================="
echo ""
echo "Prochaines étapes :"
echo "1. Transférer vos fichiers app.py, templates/, static/"
echo "2. Modifier app.py pour écouter sur 0.0.0.0:5000"
echo "3. Lancer l'application : python3 app.py"
echo ""
echo "Répertoire de l'application : /home/ubuntu/StudentApp"
echo "=========================================="
