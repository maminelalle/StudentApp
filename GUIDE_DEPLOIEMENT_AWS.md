# Guide Complet de Déploiement sur AWS Academy
## Application Web StudentApp - Haute Disponibilité

---

## 📋 PHASE 1 : PLANIFICATION ET ESTIMATION DES COÛTS

### Tâche 1.1 : Créer le Schéma d'Architecture

**Outils nécessaires :**
- Draw.io (https://app.diagrams.net/) ou
- Lucidchart (https://www.lucidchart.com/)
- Icônes AWS : https://aws.amazon.com/architecture/icons/

**Architecture à dessiner :**

```
Internet
    ↓
[Internet Gateway]
    ↓
[Application Load Balancer] (Public Subnets - 2 AZs)
    ↓
[Auto Scaling Group]
    ├── [EC2 Instance 1] (Private Subnet AZ-1)
    ├── [EC2 Instance 2] (Private Subnet AZ-2)
    └── [EC2 Instance n] (selon la charge)
    ↓
[Amazon RDS MySQL] (Private Subnet)
    ↑
[AWS Secrets Manager] (pour les credentials)
```

**Composants à inclure dans le schéma :**
1. **VPC** (Virtual Private Cloud)
2. **Subnets publics** (2 zones de disponibilité)
3. **Subnets privés** (2 zones de disponibilité)
4. **Internet Gateway**
5. **NAT Gateway** (pour les instances privées)
6. **Application Load Balancer**
7. **Auto Scaling Group** avec instances EC2
8. **Amazon RDS MySQL**
9. **AWS Secrets Manager**
10. **Security Groups** (avec flèches pour montrer les flux)

### Tâche 1.2 : Estimation des Coûts

**Accéder à AWS Pricing Calculator :**
1. Ouvrir : https://calculator.aws/
2. Cliquer sur "Create estimate"
3. Région : **us-east-1**

**Services à estimer (12 mois) :**

**1. Amazon EC2 (Serveurs Web)**
- Service : Amazon EC2
- Région : US East (N. Virginia)
- Instance type : t3.micro (ou t2.micro)
- Nombre d'instances : 2 (minimum pour HA)
- Utilisation : 730 heures/mois
- OS : Linux
- Coût estimé : ~$15-20/mois

**2. Application Load Balancer**
- Service : Elastic Load Balancing
- Type : Application Load Balancer
- Nombre : 1
- Data processed : 1 GB/mois (estimation POC)
- Coût estimé : ~$22/mois

**3. Amazon RDS MySQL**
- Service : Amazon RDS for MySQL
- Instance class : db.t3.micro
- Deployment : Single-AZ (comme spécifié)
- Storage : 20 GB (General Purpose SSD)
- Backup storage : 20 GB
- Coût estimé : ~$25/mois

**4. AWS Secrets Manager**
- Nombre de secrets : 1
- API calls : 1000/mois
- Coût estimé : ~$0.40/mois

**5. VPC et Networking**
- NAT Gateway : 1 (pour instances privées)
- Data transfer : 1 GB/mois
- Coût estimé : ~$35/mois

**6. Auto Scaling**
- Gratuit (aucun coût supplémentaire)

**COÛT TOTAL ESTIMÉ : ~$100-120 USD/mois soit ~$1200-1440/an**

---

## 📋 PHASE 2 : CRÉATION APPLICATION WEB DE BASE

### Tâche 2.1 : Créer un Réseau Virtuel (VPC)

**Étapes détaillées :**

1. **Connexion à AWS Academy**
   - Aller sur votre cours AWS Academy
   - Cliquer sur "Modules" → "Learner Lab"
   - Cliquer sur "Start Lab" (attendre que le point devienne vert)
   - Cliquer sur "AWS" (bouton vert) pour ouvrir la console

2. **Créer le VPC**
   - Dans la console AWS, chercher "VPC" dans la barre de recherche
   - Cliquer sur "Create VPC"
   - Sélectionner **"VPC and more"** (création assistée)
   
   **Configuration VPC :**
   ```
   Name tag: StudentApp-VPC
   IPv4 CIDR block: 10.0.0.0/16
   
   Availability Zones: 2
   
   Public subnets: 2
   Private subnets: 2
   
   NAT gateways: In 1 AZ (pour économiser)
   VPC endpoints: None
   
   DNS hostnames: Enable
   DNS resolution: Enable
   ```

3. **Vérifier la création**
   - VPC créé : StudentApp-VPC (10.0.0.0/16)
   - 2 subnets publics : 10.0.0.0/24 et 10.0.1.0/24
   - 2 subnets privés : 10.0.128.0/24 et 10.0.129.0/24
   - Internet Gateway attaché
   - NAT Gateway dans un subnet public
   - Route tables configurées

### Tâche 2.2 : Créer une Machine Virtuelle (EC2)

**Étapes détaillées :**

1. **Préparer les fichiers de l'application**
   
   Créer un fichier `setup-poc.sh` sur votre ordinateur :
   ```bash
   #!/bin/bash
   # Script d'installation pour Phase 2 - POC

   # Mise à jour du système
   sudo apt update
   sudo apt upgrade -y

   # Installation Python et pip
   sudo apt install python3 python3-pip python3-venv -y

   # Installation de SQLite
   sudo apt install sqlite3 -y

   # Création du répertoire de l'application
   cd /home/ubuntu
   mkdir StudentApp
   cd StudentApp

   # Créer l'environnement virtuel
   python3 -m venv venv
   source venv/bin/activate

   # Installation des dépendances Python
   pip install Flask==3.0.2
   pip install SQLAlchemy==2.0.29
   pip install openpyxl==3.1.2

   # Télécharger votre code (vous devrez le copier manuellement)
   echo "Application prête. Copiez maintenant vos fichiers app.py, templates/, static/"
   ```

2. **Lancer l'instance EC2**
   
   Dans la console AWS :
   - Services → EC2 → "Launch Instance"
   
   **Configuration :**
   ```
   Name: StudentApp-POC-Server
   
   Application and OS Images:
   - Ubuntu Server 22.04 LTS (Free tier eligible)
   - Architecture: 64-bit (x86)
   
   Instance type: t2.micro (Free tier eligible)
   
   Key pair: 
   - Cliquer "Create new key pair"
   - Name: studentapp-key
   - Type: RSA
   - Format: .pem
   - Télécharger et SAUVEGARDER le fichier .pem
   
   Network settings:
   - VPC: StudentApp-VPC
   - Subnet: Choisir un PUBLIC subnet (10.0.0.0/24)
   - Auto-assign public IP: Enable
   - Create security group: Yes
     - Name: StudentApp-POC-SG
     - Description: Security group for POC server
     - Inbound rules:
       * SSH (22) - Source: My IP (votre IP)
       * HTTP (80) - Source: Anywhere (0.0.0.0/0)
       * Custom TCP (5000) - Source: Anywhere (0.0.0.0/0)
   
   Configure storage:
   - 8 GB (default) - gp3
   
   Advanced details:
   - User data: (Coller le script setup-poc.sh)
   ```

3. **Lancer l'instance**
   - Cliquer "Launch instance"
   - Attendre que l'état soit "Running"
   - Noter l'adresse IP publique

4. **Se connecter à l'instance**

   **Option A : Via EC2 Instance Connect (plus simple)**
   - Sélectionner votre instance
   - Cliquer "Connect"
   - Onglet "EC2 Instance Connect"
   - Cliquer "Connect"

   **Option B : Via SSH (depuis votre PC)**
   - Ouvrir PowerShell
   ```powershell
   # Aller dans le dossier où est votre clé
   cd Downloads
   
   # Se connecter
   ssh -i "studentapp-key.pem" ubuntu@<IP-PUBLIQUE>
   ```

5. **Transférer votre application**

   Depuis votre PC (PowerShell) :
   ```powershell
   # Transférer app.py
   scp -i "studentapp-key.pem" c:\Users\lalle\Desktop\StudentApp\app.py ubuntu@<IP-PUBLIQUE>:/home/ubuntu/StudentApp/
   
   # Transférer requirements.txt
   scp -i "studentapp-key.pem" c:\Users\lalle\Desktop\StudentApp\requirements.txt ubuntu@<IP-PUBLIQUE>:/home/ubuntu/StudentApp/
   
   # Transférer le dossier templates
   scp -i "studentapp-key.pem" -r c:\Users\lalle\Desktop\StudentApp\templates ubuntu@<IP-PUBLIQUE>:/home/ubuntu/StudentApp/
   
   # Transférer le dossier static
   scp -i "studentapp-key.pem" -r c:\Users\lalle\Desktop\StudentApp\static ubuntu@<IP-PUBLIQUE>:/home/ubuntu/StudentApp/
   ```

6. **Configurer et lancer l'application**

   Dans votre connexion SSH sur EC2 :
   ```bash
   cd /home/ubuntu/StudentApp
   source venv/bin/activate
   
   # Installer les dépendances
   pip install -r requirements.txt
   
   # Modifier app.py pour écouter sur 0.0.0.0 au lieu de localhost
   # (Voir modification ci-dessous)
   
   # Lancer l'application
   python3 app.py
   ```

7. **Modification nécessaire dans app.py**

   À la dernière ligne de votre fichier app.py, modifier :
   ```python
   # Remplacer
   app.run(debug=True)
   
   # Par
   app.run(host='0.0.0.0', port=5000, debug=False)
   ```

### Tâche 2.3 : Tester le Déploiement

1. **Accéder à l'application**
   - Ouvrir un navigateur
   - Aller à : `http://<IP-PUBLIQUE>:5000`
   - Vous devriez voir la page de login

2. **Tester les fonctionnalités**
   - Se connecter avec : admin / admin
   - Ajouter un étudiant
   - Ajouter une matière
   - Ajouter une note
   - Vérifier l'export Excel

3. **Si ça ne fonctionne pas :**
   - Vérifier le Security Group (port 5000 ouvert)
   - Vérifier les logs : `journalctl -u studentapp`
   - Vérifier que l'app écoute sur 0.0.0.0 : `netstat -tlnp | grep 5000`

---

## 📋 PHASE 3 : DÉCOUPLAGE DES COMPOSANTS

### Tâche 3.1 : Modifier la Configuration du VPC

**Les subnets privés existent déjà (créés en Phase 2), vérifier :**
- Services → VPC → Subnets
- Vous devez avoir 2 subnets privés dans 2 AZs différentes

### Tâche 3.2 : Créer la Base de Données Amazon RDS

**Étapes détaillées :**

1. **Créer un Subnet Group pour RDS**
   - Services → RDS → Subnet groups
   - Cliquer "Create DB subnet group"
   ```
   Name: studentapp-db-subnet-group
   Description: Subnet group for StudentApp database
   VPC: StudentApp-VPC
   
   Add subnets:
   - Availability Zones: Sélectionner 2 AZs
   - Subnets: Sélectionner les 2 PRIVATE subnets
   ```
   - Cliquer "Create"

2. **Créer un Security Group pour RDS**
   - Services → EC2 → Security Groups → Create security group
   ```
   Name: StudentApp-RDS-SG
   Description: Security group for RDS MySQL database
   VPC: StudentApp-VPC
   
   Inbound rules:
   - Type: MySQL/Aurora (port 3306)
   - Source: Custom
   - CIDR: 10.0.0.0/16 (tout le VPC)
   - Description: Allow MySQL from VPC
   
   Outbound rules: Default (tout autorisé)
   ```
   - Cliquer "Create security group"

3. **Créer la base de données RDS**
   - Services → RDS → Databases → "Create database"
   
   **Configuration :**
   ```
   Choose a database creation method: Standard create
   
   Engine options:
   - Engine type: MySQL
   - Version: MySQL 8.0.35 (ou la version stable la plus récente)
   
   Templates: Free tier (si disponible) OU Dev/Test
   
   Settings:
   - DB instance identifier: studentapp-db
   - Master username: admin
   - Master password: StudentApp2026! (NOTEZ CE MOT DE PASSE)
   - Confirm password: StudentApp2026!
   
   Instance configuration:
   - DB instance class: Burstable classes - db.t3.micro
   
   Storage:
   - Storage type: General Purpose SSD (gp2)
   - Allocated storage: 20 GB
   - Disable storage autoscaling
   
   Connectivity:
   - VPC: StudentApp-VPC
   - DB subnet group: studentapp-db-subnet-group
   - Public access: No
   - VPC security group: Choose existing
     - Remove default
     - Add: StudentApp-RDS-SG
   - Availability Zone: No preference
   
   Database authentication: Password authentication
   
   Additional configuration:
   - Initial database name: studentdb
   - DB parameter group: default
   - Backup:
     - Enable automated backups: Yes
     - Backup retention: 7 days
   - Encryption: Disable (pour économiser)
   - Enhanced monitoring: Disable (comme demandé)
   - Log exports: None
   - Maintenance: Enable auto minor version upgrade
   - Deletion protection: Disable (pour le POC)
   ```

4. **Créer la base de données**
   - Cliquer "Create database"
   - Attendre 5-10 minutes (Status: Creating → Available)
   - Noter l'**Endpoint** (exemple: studentapp-db.xxxxx.us-east-1.rds.amazonaws.com)

### Tâche 3.3 : Configurer AWS Cloud9

1. **Créer l'environnement Cloud9**
   - Services → Cloud9 → "Create environment"
   ```
   Name: StudentApp-Dev
   Description: Development environment for StudentApp
   
   Environment type: New EC2 instance
   Instance type: t3.micro
   Platform: Amazon Linux 2023
   
   Network settings:
   - VPC: StudentApp-VPC
   - Subnet: Choisir un PUBLIC subnet
   
   Connection: AWS Systems Manager (SSM)
   ```
   - Cliquer "Create"
   - Attendre que l'environnement soit prêt (2-3 minutes)

2. **Ouvrir Cloud9**
   - Cliquer "Open" sur votre environnement
   - Une fenêtre s'ouvre avec un IDE en ligne

### Tâche 3.4 : Créer le Secret dans Secrets Manager

1. **Dans Cloud9, créer un fichier de script**

   Dans le terminal Cloud9 (en bas) :
   ```bash
   # Créer un fichier pour le script
   cat > create-secret.sh << 'EOF'
   #!/bin/bash
   
   # Variables - MODIFIEZ AVEC VOS VALEURS
   DB_ENDPOINT="studentapp-db.xxxxx.us-east-1.rds.amazonaws.com"
   DB_USERNAME="admin"
   DB_PASSWORD="StudentApp2026!"
   DB_NAME="studentdb"
   
   # Créer le secret
   aws secretsmanager create-secret \
     --name StudentAppDBSecret \
     --description "Database credentials for StudentApp" \
     --secret-string "{\"host\":\"$DB_ENDPOINT\",\"port\":3306,\"username\":\"$DB_USERNAME\",\"password\":\"$DB_PASSWORD\",\"dbname\":\"$DB_NAME\"}" \
     --region us-east-1
   
   echo "Secret créé avec succès!"
   EOF
   
   # Rendre le script exécutable
   chmod +x create-secret.sh
   
   # Exécuter le script (APRÈS avoir modifié DB_ENDPOINT)
   nano create-secret.sh  # Modifier l'endpoint
   ./create-secret.sh
   ```

2. **Vérifier le secret**
   - Services → Secrets Manager
   - Vous devriez voir "StudentAppDBSecret"

### Tâche 3.5 : Créer le Serveur Web avec RDS

1. **Modifier votre app.py pour utiliser MySQL et Secrets Manager**

   Sur votre PC, créer un nouveau fichier `app-rds.py` basé sur votre `app.py` :

   ```python
   # Ajouter en haut du fichier (après les imports)
   import boto3
   import json
   from sqlalchemy import create_engine
   
   # Fonction pour récupérer les credentials depuis Secrets Manager
   def get_db_credentials():
       secret_name = "StudentAppDBSecret"
       region_name = "us-east-1"
       
       session = boto3.session.Session()
       client = session.client(
           service_name='secretsmanager',
           region_name=region_name
       )
       
       try:
           get_secret_value_response = client.get_secret_value(
               SecretId=secret_name
           )
       except Exception as e:
           raise e
       
       secret = json.loads(get_secret_value_response['SecretString'])
       return secret
   
   # Modifier la connexion à la base de données
   # REMPLACER LA LIGNE engine = create_engine("sqlite:///student_grades.db")
   # PAR:
   
   db_creds = get_db_credentials()
   DATABASE_URL = f"mysql+pymysql://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}:{db_creds['port']}/{db_creds['dbname']}"
   engine = create_engine(DATABASE_URL)
   ```

2. **Créer requirements-rds.txt**
   ```
   Flask==3.0.2
   SQLAlchemy==2.0.29
   openpyxl==3.1.2
   boto3==1.34.0
   pymysql==1.1.0
   cryptography==42.0.0
   ```

3. **Créer une nouvelle instance EC2**
   
   - Services → EC2 → Launch Instance
   ```
   Name: StudentApp-WebServer
   
   AMI: Ubuntu 22.04 LTS
   Instance type: t2.micro
   Key pair: studentapp-key
   
   Network:
   - VPC: StudentApp-VPC
   - Subnet: PUBLIC subnet
   - Auto-assign IP: Enable
   - Security group: Create new
     - Name: StudentApp-Web-SG
     - Rules:
       * SSH (22) - My IP
       * HTTP (80) - Anywhere
       * Custom TCP (5000) - Anywhere
   
   Advanced details:
   - IAM instance profile: LabInstanceProfile (IMPORTANT!)
   ```

4. **Se connecter et configurer**
   ```bash
   ssh -i "studentapp-key.pem" ubuntu@<NOUVELLE-IP>
   
   # Installation
   sudo apt update
   sudo apt install python3 python3-pip python3-venv -y
   
   # Créer l'application
   mkdir StudentApp && cd StudentApp
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Transférer les fichiers modifiés**
   ```powershell
   scp -i "studentapp-key.pem" app-rds.py ubuntu@<IP>:/home/ubuntu/StudentApp/app.py
   scp -i "studentapp-key.pem" requirements-rds.txt ubuntu@<IP>:/home/ubuntu/StudentApp/requirements.txt
   scp -i "studentapp-key.pem" -r templates ubuntu@<IP>:/home/ubuntu/StudentApp/
   scp -i "studentapp-key.pem" -r static ubuntu@<IP>:/home/ubuntu/StudentApp/
   ```

6. **Installer et lancer**
   ```bash
   cd /home/ubuntu/StudentApp
   source venv/bin/activate
   pip install -r requirements.txt
   python3 app.py
   ```

### Tâche 3.6 : Migrer les Données

1. **Dans Cloud9, créer le script de migration**

   ```bash
   cat > migrate-data.sh << 'EOF'
   #!/bin/bash
   
   # Variables - MODIFIEZ
   RDS_ENDPOINT="studentapp-db.xxxxx.us-east-1.rds.amazonaws.com"
   RDS_USER="admin"
   RDS_PASS="StudentApp2026!"
   RDS_DB="studentdb"
   OLD_SERVER_IP="<IP-DE-LANCIEN-SERVEUR-POC>"
   
   # Exporter les données de l'ancien serveur (SQLite)
   echo "Export depuis SQLite..."
   ssh -i ~/environment/studentapp-key.pem ubuntu@$OLD_SERVER_IP \
     "sqlite3 /home/ubuntu/StudentApp/student_grades.db .dump" > dump.sql
   
   # Convertir pour MySQL (enlever les commandes SQLite)
   sed -i '/PRAGMA/d' dump.sql
   sed -i 's/AUTOINCREMENT/AUTO_INCREMENT/g' dump.sql
   
   # Importer dans RDS
   echo "Import vers RDS MySQL..."
   mysql -h $RDS_ENDPOINT -u $RDS_USER -p$RDS_PASS $RDS_DB < dump.sql
   
   echo "Migration terminée!"
   EOF
   
   chmod +x migrate-data.sh
   nano migrate-data.sh  # Modifier les variables
   ./migrate-data.sh
   ```

### Tâche 3.7 : Tester l'Application

1. Accéder à `http://<IP-NOUVEAU-SERVEUR>:5000`
2. Se connecter avec admin/admin
3. Vérifier que les données sont présentes
4. Ajouter/modifier des données pour tester

---

## 📋 PHASE 4 : HAUTE DISPONIBILITÉ ET MISE À L'ÉCHELLE

### Tâche 4.1 : Créer l'Application Load Balancer

1. **Modifier le Security Group du Web Server**
   - EC2 → Security Groups → StudentApp-Web-SG
   - Modifier les Inbound rules :
   ```
   Supprimer : Custom TCP 5000 from Anywhere
   Ajouter : HTTP 80 from Anywhere (0.0.0.0/0)
   ```

2. **Modifier app.py pour écouter sur port 80**
   ```python
   # À la fin de app.py
   app.run(host='0.0.0.0', port=80, debug=False)
   ```
   
   Sur le serveur :
   ```bash
   # Lancer avec sudo (port 80 nécessite root)
   sudo /home/ubuntu/StudentApp/venv/bin/python3 app.py
   ```

3. **Créer un Target Group**
   - EC2 → Target Groups → Create target group
   ```
   Target type: Instances
   
   Basic configuration:
   - Target group name: StudentApp-TG
   - Protocol: HTTP
   - Port: 80
   - VPC: StudentApp-VPC
   - Protocol version: HTTP1
   
   Health checks:
   - Protocol: HTTP
   - Path: /
   - Advanced:
     - Healthy threshold: 2
     - Unhealthy threshold: 2
     - Timeout: 5
     - Interval: 30
   ```
   - Next → Ne sélectionner AUCUNE instance pour l'instant
   - Create target group

4. **Créer l'Application Load Balancer**
   - EC2 → Load Balancers → Create load balancer
   - Sélectionner "Application Load Balancer"
   
   ```
   Basic configuration:
   - Name: StudentApp-ALB
   - Scheme: Internet-facing
   - IP address type: IPv4
   
   Network mapping:
   - VPC: StudentApp-VPC
   - Mappings: Sélectionner 2 zones de disponibilité
     - Choisir les 2 PUBLIC subnets
   
   Security groups:
   - Create new:
     - Name: StudentApp-ALB-SG
     - Inbound: HTTP (80) from Anywhere (0.0.0.0/0)
   
   Listeners and routing:
   - Protocol: HTTP
   - Port: 80
   - Default action: Forward to StudentApp-TG
   ```
   - Create load balancer
   - Attendre que Status = Active (2-3 minutes)
   - Noter le DNS name (exemple: StudentApp-ALB-xxxxx.us-east-1.elb.amazonaws.com)

5. **Tester le Load Balancer**
   - Ouvrir le DNS du Load Balancer dans un navigateur
   - Vous devriez voir votre application (si vous avez déjà des instances)

### Tâche 4.2 : Créer l'AMI et l'Auto Scaling

1. **Préparer l'instance pour l'AMI**
   
   Se connecter à votre instance StudentApp-WebServer :
   ```bash
   # Créer un script de démarrage
   cat > /home/ubuntu/startup.sh << 'EOF'
   #!/bin/bash
   cd /home/ubuntu/StudentApp
   source venv/bin/activate
   sudo /home/ubuntu/StudentApp/venv/bin/python3 app.py >> /var/log/studentapp.log 2>&1
   EOF
   
   chmod +x /home/ubuntu/startup.sh
   
   # Créer un service systemd pour démarrer automatiquement
   sudo bash -c 'cat > /etc/systemd/system/studentapp.service << EOF
   [Unit]
   Description=StudentApp Flask Application
   After=network.target
   
   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/StudentApp
   ExecStart=/home/ubuntu/StudentApp/venv/bin/python3 app.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   EOF'
   
   # Activer le service
   sudo systemctl daemon-reload
   sudo systemctl enable studentapp
   sudo systemctl start studentapp
   
   # Vérifier
   sudo systemctl status studentapp
   ```

2. **Créer une AMI**
   - EC2 → Instances → Sélectionner StudentApp-WebServer
   - Actions → Image and templates → Create image
   ```
   Image name: StudentApp-WebServer-AMI
   Image description: Web server with StudentApp configured
   No reboot: Décoché (pour cohérence)
   ```
   - Create image
   - Attendre que l'AMI soit Available (AMIs dans le menu)

3. **Créer un Launch Template**
   - EC2 → Launch Templates → Create launch template
   ```
   Launch template name: StudentApp-LT
   Template version description: Initial version
   
   Application and OS Images:
   - My AMIs → Owned by me
   - Sélectionner StudentApp-WebServer-AMI
   
   Instance type: t2.micro
   
   Key pair: studentapp-key
   
   Network settings:
   - Ne PAS inclure dans le template (on le fera dans l'ASG)
   
   Advanced details:
   - IAM instance profile: LabInstanceProfile
   - User data: (vide ou le script de startup si besoin)
   ```
   - Create launch template

4. **Créer un Auto Scaling Group**
   - EC2 → Auto Scaling Groups → Create Auto Scaling group
   
   **Step 1: Choose launch template**
   ```
   Name: StudentApp-ASG
   Launch template: StudentApp-LT
   ```
   - Next
   
   **Step 2: Choose instance launch options**
   ```
   VPC: StudentApp-VPC
   Availability Zones: Sélectionner les 2 PRIVATE subnets
   ```
   - Next
   
   **Step 3: Configure advanced options**
   ```
   Load balancing: Attach to an existing load balancer
   - Choose from your load balancer target groups
   - StudentApp-TG
   
   Health checks:
   - ELB: Cocher
   - Health check grace period: 300 seconds
   ```
   - Next
   
   **Step 4: Configure group size and scaling**
   ```
   Group size:
   - Desired capacity: 2
   - Minimum capacity: 2
   - Maximum capacity: 4
   
   Scaling policies: Target tracking scaling policy
   - Metric type: Average CPU utilization
   - Target value: 50
   - Instances need: 300 seconds (warm-up)
   ```
   - Next
   
   **Step 5: Add notifications** (Skip)
   - Next
   
   **Step 6: Add tags**
   ```
   Key: Name
   Value: StudentApp-ASG-Instance
   ```
   - Next
   
   **Step 7: Review**
   - Create Auto Scaling group

5. **Attendre et vérifier**
   - EC2 → Instances : Vous devriez voir 2 nouvelles instances se lancer
   - EC2 → Target Groups → StudentApp-TG : Vérifier que les instances sont "healthy"
   - Attendre 2-3 minutes

### Tâche 4.3 : Accéder à l'Application

1. **Obtenir l'URL du Load Balancer**
   - EC2 → Load Balancers → StudentApp-ALB
   - Copier le "DNS name"

2. **Tester l'application**
   - Ouvrir : `http://<ALB-DNS-NAME>`
   - Se connecter : admin / admin
   - Tester toutes les fonctionnalités
   - Actualiser plusieurs fois → le load balancer distribue entre les instances

### Tâche 4.4 : Test de Charge

1. **Dans Cloud9, installer l'outil de test**
   ```bash
   # Installer Node.js et npm
   sudo yum install nodejs npm -y
   
   # Installer loadtest
   sudo npm install -g loadtest
   ```

2. **Créer le script de test**
   ```bash
   cat > load-test.sh << 'EOF'
   #!/bin/bash
   
   # URL du Load Balancer - MODIFIEZ
   ALB_URL="http://StudentApp-ALB-xxxxx.us-east-1.elb.amazonaws.com"
   
   echo "Démarrage du test de charge..."
   echo "Monitoring : Surveillez CloudWatch et l'Auto Scaling Group"
   
   # Test : 100 requêtes par seconde pendant 10 minutes
   loadtest -c 100 --rps 100 -t 600 $ALB_URL
   
   echo "Test terminé!"
   EOF
   
   chmod +x load-test.sh
   nano load-test.sh  # Modifier l'URL
   ```

3. **Surveiller avant de lancer le test**
   - EC2 → Auto Scaling Groups → StudentApp-ASG
   - Onglet "Monitoring" → Ouvrir dans CloudWatch
   - EC2 → Instances → Observer le nombre d'instances

4. **Lancer le test**
   ```bash
   ./load-test.sh
   ```

5. **Observer le scaling**
   - Après 2-3 minutes, si le CPU dépasse 50%, de nouvelles instances se lancent
   - Maximum 4 instances (comme configuré)
   - Après le test, les instances diminuent automatiquement

---

## 📊 CHECKLIST FINALE

### Phase 1 ✅
- [ ] Schéma d'architecture créé
- [ ] Estimation de coûts calculée (~$100-120/mois)

### Phase 2 ✅
- [ ] VPC créé avec 2 AZs
- [ ] 2 subnets publics + 2 subnets privés
- [ ] Internet Gateway et NAT Gateway
- [ ] Instance EC2 fonctionnelle
- [ ] Application accessible publiquement

### Phase 3 ✅
- [ ] RDS MySQL créé et accessible
- [ ] AWS Secrets Manager configuré
- [ ] Cloud9 environnement créé
- [ ] Application connectée à RDS
- [ ] Données migrées

### Phase 4 ✅
- [ ] Application Load Balancer créé
- [ ] Target Group configuré
- [ ] AMI créée
- [ ] Launch Template créé
- [ ] Auto Scaling Group fonctionnel (2-4 instances)
- [ ] Test de charge réussi

---

## 🔐 SÉCURITÉ - Points de Contrôle

- [ ] Base de données dans subnets PRIVÉS uniquement
- [ ] Security Group RDS : port 3306 uniquement du VPC
- [ ] Security Group ALB : port 80 de partout
- [ ] Security Group Instances : port 80 de l'ALB uniquement
- [ ] Credentials dans Secrets Manager (pas en dur)
- [ ] IAM Role (LabInstanceProfile) attaché aux instances

---

## 💰 GESTION DU BUDGET

**Services qui consomment le budget :**
1. **EC2 Instances** - Plus d'instances = plus cher
2. **NAT Gateway** - Coût par heure (~$0.045/h) + transfert
3. **RDS** - Instance + storage
4. **Load Balancer** - Coût par heure + données
5. **Data Transfer** - Sortie vers Internet

**Conseils pour économiser :**
- Arrêtez les instances EC2 quand vous ne travaillez pas
- Utilisez 1 NAT Gateway au lieu de 2
- Supprimez les snapshots/AMIs inutiles
- Surveillez le budget dans AWS Academy (en haut)

**Arrêter les ressources en fin de journée :**
```bash
# Mettre l'ASG à 0
# EC2 → Auto Scaling Groups → StudentApp-ASG → Edit
# Desired: 0, Min: 0, Max: 4

# Arrêter RDS
# RDS → Databases → studentapp-db → Actions → Stop temporarily
```

---

## 🆘 DÉPANNAGE

### Problème : Instance ne démarre pas
- Vérifier le User Data
- Voir les logs : EC2 → Instance → Actions → Monitor and troubleshoot → Get system log

### Problème : Application non accessible
- Vérifier Security Group (port 80 ouvert)
- Vérifier que l'app écoute sur 0.0.0.0
- SSH dans l'instance : `sudo systemctl status studentapp`

### Problème : Load Balancer unhealthy
- Target Group → Health check path doit être "/"
- Security Group des instances doit accepter le traffic du Load Balancer

### Problème : RDS inaccessible
- Vérifier que les instances sont dans le VPC
- Security Group RDS doit autoriser port 3306 du VPC (10.0.0.0/16)
- Tester: `mysql -h <endpoint> -u admin -p`

### Problème : Secrets Manager erreur
- Vérifier IAM Role (LabInstanceProfile) sur les instances
- Tester dans l'instance : `aws secretsmanager get-secret-value --secret-id StudentAppDBSecret --region us-east-1`

### Problème : Budget dépassé
- Supprimer NAT Gateway
- Réduire nombre d'instances (ASG à 1-2)
- Arrêter RDS quand non utilisé

---

## 📦 RESSOURCES ET LIENS

**Code source modifié :**
- Votre application est dans : `c:\Users\lalle\Desktop\StudentApp\`
- Fichiers modifiés pour AWS dans ce guide

**AWS Academy :**
- Console : Via le bouton vert "AWS" 
- Documentation : Module Resources dans votre cours

**Outils externes :**
- Draw.io : https://app.diagrams.net/
- AWS Pricing Calculator : https://calculator.aws/

**Support :**
- Forum AWS Academy dans votre cours
- Votre instructeur

---

## ✅ PRÉSENTATION FINALE

**À préparer :**
1. **Slides PowerPoint** (template fourni par le prof)
   - Slide 1 : Schéma d'architecture
   - Slide 2 : Estimation des coûts
   - Slide 3 : Capture d'écran de l'application fonctionnelle
   - Slide 4 : Résultats du test de charge
   - Slide 5 : Leçons apprises

2. **Démonstration live**
   - Accès via Load Balancer URL
   - Ajouter/modifier/supprimer des données
   - Montrer CloudWatch avec les métriques

3. **Documentation technique**
   - Ce guide avec vos notes
   - Captures d'écran des configurations
   - Liste des ressources créées

**Bonne chance ! 🎓**
