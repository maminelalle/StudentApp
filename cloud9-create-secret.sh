#!/bin/bash
# Script pour créer le secret dans AWS Secrets Manager via Cloud9

# ============================================================================
# ÉTAPE 1: Créer le secret RDS
# ============================================================================

echo "=========================================="
echo "Création du secret AWS Secrets Manager"
echo "=========================================="

# MODIFIEZ CES VALEURS avec vos valeurs réelles
DB_ENDPOINT="studentapp-db.xxxxx.us-east-1.rds.amazonaws.com"  # À remplacer !
DB_USERNAME="admin"
DB_PASSWORD="StudentApp2026!"
DB_NAME="studentdb"
DB_PORT="3306"

# Créer le secret
aws secretsmanager create-secret \
    --name StudentAppDBSecret \
    --description "Database credentials for StudentApp RDS MySQL" \
    --secret-string "{\"host\":\"$DB_ENDPOINT\",\"port\":$DB_PORT,\"username\":\"$DB_USERNAME\",\"password\":\"$DB_PASSWORD\",\"dbname\":\"$DB_NAME\"}" \
    --region us-east-1

if [ $? -eq 0 ]; then
    echo "✓ Secret créé avec succès!"
else
    echo "✗ Erreur lors de la création du secret"
    exit 1
fi

# ============================================================================
# ÉTAPE 2: Vérifier le secret
# ============================================================================

echo ""
echo "Vérification du secret..."
aws secretsmanager get-secret-value \
    --secret-id StudentAppDBSecret \
    --region us-east-1 \
    --query SecretString \
    --output text | python3 -m json.tool

echo ""
echo "✓ Script terminé!"
echo ""
echo "Prochaines étapes:"
echo "1. Tester la connexion RDS depuis EC2"
echo "2. Lancer l'instance EC2 avec le profil IAM LabInstanceProfile"
echo "3. Déployer l'application avec app-rds-template.py"
