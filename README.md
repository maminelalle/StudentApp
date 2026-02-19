# Application Web de Suivi des Notes et Devoirs - SupNum

Application web complète et fonctionnelle pour la gestion des notes, devoirs et matières pour l'Institut Supérieur du Numérique (SupNum).

## 🎯 Objectif

Simplifier le suivi académique, la consultation des résultats et l'administration des données avec deux interfaces principales :
- **Admin** : Gestion complète (utilisateurs, filières, spécialités, matières, devoirs, notes)
- **Étudiant** : Consultation et suivi académique

## 🚀 Lancer l'application

### Installation

```bash
cd c:\Users\lalle\Desktop\StudentApp
pip install -r requirements.txt
```

### Démarrage

```bash
python app.py
```

Puis ouvrir dans le navigateur : **http://127.0.0.1:5000**

## 🔐 Comptes créés automatiquement

| Rôle     | Email                    | Mot de passe |
|----------|--------------------------|--------------|
| **Admin**   | `admin@studentapp.com`     | `admin123`   |
| **Étudiant** | `etudiant@studentapp.com` | `etudiant123` |

## ✨ Fonctionnalités

### 🔧 Interface Administrateur

#### Gestion Académique
- **Filières** : L1, L2, L3 avec descriptions
- **Spécialités** : DSI, RSS, CNM assignées aux filières
- **Semestres** : S1 à S6 avec numérotation
- **Matières** : Code, nom, semestre, filière, spécialité, seuil de validation, rattrapable

#### Gestion des Évaluations
- **Devoirs** : Nom, matière, date, type (TP/Écrit/Projet/Examen/Rattrapage), session (Normale/Rattrapage)
- **Notes** : Saisie, modification, suppression avec calcul automatique des moyennes

#### Gestion des Utilisateurs
- **Types** : Administrateurs, Enseignants, Étudiants
- **Étudiants** : Assignation filière + spécialité
- Aucun auto-enregistrement (création par admin uniquement)

#### Statistiques et Rapports
- Vue d'ensemble : Total matières/devoirs/étudiants, moyenne générale
- Répartition des notes par tranches
- Matières les plus difficiles
- Statistiques par filière et spécialité
- Indicateurs colorés (vert=validé, orange=rattrapage, rouge=non validé)

#### Export Excel
- Export complet de toutes les notes
- Export par filière (L1, L2, L3)
- Export par étudiant individuel
- Format professionnel avec en-têtes stylisés

### 📚 Interface Étudiant

#### Tableau de Bord
- Informations personnelles (nom, filière, spécialité)
- Moyenne générale
- Statut des matières avec semestres
- Devoirs sans note
- Export Excel personnel

#### Consultation
- **Mes Matières** : Liste avec moyennes et statuts
- **Mes Devoirs** : Détails (type, date, note) avec filtres par matière
- **Mes Résultats** : Vue complète des moyennes par matière

#### Fonctionnalités
- Filtrage par semestre
- Téléchargement des notes au format Excel
- Indicateurs visuels de progression (Validée/À rattraper/Non validée)

## 🛠️ Technologies

- **Backend** : Python 3 + Flask
- **Base de données** : SQLite (`student_grades.db`)
- **Frontend** : HTML + Bootstrap 5 + Bootstrap Icons
- **Export** : openpyxl (Excel)
- **Architecture** : SQLAlchemy ORM

## 📊 Structure de la Base de Données

- **Filiere** : Filières académiques (L1, L2, L3)
- **Specialite** : Spécialités par filière (DSI, RSS, CNM)
- **Semestre** : Semestres académiques (S1-S6)
- **Matiere** : Matières avec code, semestre, filière, spécialité
- **Devoir** : Devoirs/examens avec type et session
- **Etudiant** : Étudiants avec filière et spécialité
- **Utilisateur** : Admins et enseignants
- **Note** : Notes des étudiants

## 🎨 Design

- Couleurs harmonisées : bleu (#4A90E2), vert (#7ED321), orange (#F5A623), rouge (#D0021B)
- Interface responsive (PC, tablette, mobile)
- Navigation intuitive avec icônes
- Tableaux dynamiques et cartes statistiques

## 🔒 Sécurité

- Les étudiants ne voient que leurs données
- Les administrateurs gèrent tout
- Authentification par email + mot de passe
- Sessions sécurisées Flask

## 📝 Notes de Développement

### Données Initiales

Au premier lancement, l'application crée automatiquement :
- 1 compte admin
- 1 compte étudiant (L3 DSI)
- 3 filières (L1, L2, L3)
- 3 spécialités (DSI, RSS, CNM)
- 6 semestres (S1-S6)

### Migration depuis Ancienne Version

Si vous aviez une ancienne base de données, supprimez `student_grades.db` pour recréer la base avec la nouvelle structure.

---

**Développé pour l'Institut Supérieur du Numérique (SupNum)**
