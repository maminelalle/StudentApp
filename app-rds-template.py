# Configuration pour AWS RDS
# Modifiez votre app.py pour utiliser cette version

import boto3
import json
from datetime import date
from flask import Flask, render_template, redirect, url_for, request, flash, session
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey, func, select
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
import os
from functools import wraps

# ============================================================================
# Configuration AWS et Secrets Manager
# ============================================================================

def get_db_credentials():
    """
    Récupère les credentials RDS depuis AWS Secrets Manager
    """
    secret_name = "StudentAppDBSecret"
    region_name = "us-east-1"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret
    except Exception as e:
        # Fallback pour développement local (SQLite)
        print(f"Warning: Could not fetch from Secrets Manager: {e}")
        print("Using local SQLite database instead")
        return None

# Obtenir les credentials
db_creds = get_db_credentials()

if db_creds:
    # Connexion à RDS MySQL
    DATABASE_URL = f"mysql+pymysql://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}:{db_creds['port']}/{db_creds['dbname']}"
else:
    # Fallback SQLite pour développement
    DATABASE_URL = "sqlite:///student_grades.db"

print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'SQLite'}")

# ============================================================================
# SQLAlchemy Configuration
# ============================================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Important pour RDS - teste la connexion avant usage
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)
Base = declarative_base()

# ============================================================================
# ORM Models
# ============================================================================

class Filiere(Base):
    __tablename__ = "filiere"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False, unique=True)
    specialites = relationship("Specialite", back_populates="filiere")
    etudiants = relationship("Etudiant", back_populates="filiere")

class Specialite(Base):
    __tablename__ = "specialite"
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    nom = Column(String, nullable=False)
    filiere_id = Column(Integer, ForeignKey("filiere.id"), nullable=False)
    filiere = relationship("Filiere", back_populates="specialites")
    etudiants = relationship("Etudiant", back_populates="specialite")

class Semestre(Base):
    __tablename__ = "semestre"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False, unique=True)
    numero = Column(Integer, nullable=False)
    matieres = relationship("Matiere", back_populates="semestre")

class Matiere(Base):
    __tablename__ = "matiere"
    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    nom = Column(String, nullable=False)
    semestre_id = Column(Integer, ForeignKey("semestre.id"), nullable=True)
    filiere_id = Column(Integer, ForeignKey("filiere.id"), nullable=True)
    specialite_id = Column(Integer, ForeignKey("specialite.id"), nullable=True)
    seuil_validation = Column(Float, default=10.0)
    rattrapable = Column(String, default="Oui")
    semestre = relationship("Semestre", back_populates="matieres")
    devoirs = relationship("Devoir", back_populates="matiere")
    notes = relationship("Note", back_populates="matiere")

class Devoir(Base):
    __tablename__ = "devoir"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    matiere_id = Column(Integer, ForeignKey("matiere.id"), nullable=False)
    type = Column(String, default="Écrit")
    session = Column(String, default="Normale")
    date = Column(Date)
    matiere = relationship("Matiere", back_populates="devoirs")
    notes = relationship("Note", back_populates="devoir")

class Etudiant(Base):
    __tablename__ = "etudiant"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True)
    password_hash = Column(String)
    filiere_id = Column(Integer, ForeignKey("filiere.id"), nullable=True)
    specialite_id = Column(Integer, ForeignKey("specialite.id"), nullable=True)
    filiere = relationship("Filiere", back_populates="etudiants")
    specialite = relationship("Specialite", back_populates="etudiants")
    notes = relationship("Note", back_populates="etudiant")

class Utilisateur(Base):
    __tablename__ = "utilisateur"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(String, default="enseignant")

class Note(Base):
    __tablename__ = "note"
    id = Column(Integer, primary_key=True)
    etudiant_id = Column(Integer, ForeignKey("etudiant.id"), nullable=False)
    devoir_id = Column(Integer, ForeignKey("devoir.id"), nullable=False)
    matiere_id = Column(Integer, ForeignKey("matiere.id"), nullable=False)
    valeur = Column(Float, nullable=False)
    etudiant = relationship("Etudiant", back_populates="notes")
    devoir = relationship("Devoir", back_populates="notes")
    matiere = relationship("Matiere", back_populates="notes")

# ============================================================================
# Créer les tables
# ============================================================================

def init_db():
    """Crée les tables dans la base de données"""
    Base.metadata.create_all(bind=engine)
    print("Tables créées ou vérifiées avec succès!")

# ============================================================================
# Application Flask
# ============================================================================

app = Flask(__name__)
app.secret_key = "your-secret-key-change-in-production"
app.config['SESSION_TYPE'] = 'filesystem'

# ============================================================================
# Database Functions
# ============================================================================

def get_db():
    """Retourne une session de base de données"""
    return db_session

# ============================================================================
# Authentication
# ============================================================================

def current_user():
    """Retourne l'utilisateur actuel depuis la session"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    db = get_db()
    # Chercher d'abord dans Utilisateur (admin/enseignant)
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    if user:
        return {
            "id": user.id,
            "nom": user.nom,
            "email": user.email,
            "role": user.role,
            "type": "utilisateur"
        }
    
    # Sinon dans Etudiant
    etudiant = db.query(Etudiant).filter(Etudiant.id == user_id).first()
    if etudiant:
        return {
            "id": etudiant.id,
            "nom": etudiant.nom,
            "email": etudiant.email,
            "role": "etudiant",
            "type": "etudiant"
        }
    
    return None

def login_required(role=None):
    """Décorateur pour vérifier l'authentification et le rôle"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Vous devez être connecté.", "error")
                return redirect(url_for('login'))
            if role and user.get("role") not in role:
                flash("Vous n'avez pas les permissions nécessaires.", "error")
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ============================================================================
# Routes
# ============================================================================

@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        db = get_db()
        
        # Vérifier dans Utilisateur
        user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
        if user and user.password_hash == password:
            session['user_id'] = user.id
            session['user_role'] = user.role
            flash(f"Bienvenue {user.nom}!", "success")
            if user.role == "admin":
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        
        # Vérifier dans Etudiant
        etudiant = db.query(Etudiant).filter(Etudiant.email == email).first()
        if etudiant and etudiant.password_hash == password:
            session['user_id'] = etudiant.id
            session['user_role'] = "etudiant"
            flash(f"Bienvenue {etudiant.nom}!", "success")
            return redirect(url_for('student_dashboard'))
        
        flash("Email ou mot de passe incorrect.", "error")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for('login'))

# ============================================================================
# Routes Admin (exemple)
# ============================================================================

@app.route("/admin/dashboard")
@login_required(role=("admin",))
def admin_dashboard():
    db = get_db()
    user = current_user()
    
    # Statistiques
    total_etudiants = db.query(Etudiant).count()
    total_matieres = db.query(Matiere).count()
    total_notes = db.query(Note).count()
    
    return render_template(
        "admin/dashboard.html",
        user=user,
        total_etudiants=total_etudiants,
        total_matieres=total_matieres,
        total_notes=total_notes
    )

# ============================================================================
# Routes Etudiant (exemple)
# ============================================================================

@app.route("/etudiant/dashboard")
@login_required(role=("etudiant",))
def student_dashboard():
    db = get_db()
    user = current_user()
    
    etudiant = db.query(Etudiant).get(user["id"])
    
    # Récupérer les notes
    notes = db.query(Note).filter(Note.etudiant_id == user["id"]).all()
    
    return render_template(
        "etudiant/dashboard.html",
        user=user,
        etudiant=etudiant,
        notes=notes
    )

# ============================================================================
# Initialisation et Seed Data
# ============================================================================

def seed_data():
    """Crée les données de test"""
    db = get_db()
    
    # Vérifier si les données existent déjà
    if db.query(Utilisateur).count() > 0:
        print("Base de données déjà peuplée.")
        return
    
    # Admin
    admin = Utilisateur(
        nom="Admin",
        email="admin",
        password_hash="admin",
        role="admin"
    )
    db.add(admin)
    
    # Filières
    l1 = Filiere(nom="L1")
    l2 = Filiere(nom="L2")
    l3 = Filiere(nom="L3")
    db.add_all([l1, l2, l3])
    db.flush()
    
    # Spécialités
    dsi = Specialite(nom="Développement et Systèmes Informatiques", code="DSI", filiere_id=l3.id)
    rss = Specialite(nom="Réseaux et Sécurité des Systèmes", code="RSS", filiere_id=l3.id)
    cnm = Specialite(nom="Cloud et Nouvelles Mobilités", code="CNM", filiere_id=l3.id)
    db.add_all([dsi, rss, cnm])
    db.flush()
    
    # Semestres
    semestres = []
    for i in range(1, 7):
        s = Semestre(nom=f"S{i}", numero=i)
        db.add(s)
        semestres.append(s)
    db.flush()
    
    # Exemple d'étudiant
    etudiant = Etudiant(
        nom="Demo Student",
        email="demo",
        password_hash="demo",
        filiere_id=l3.id,
        specialite_id=dsi.id
    )
    db.add(etudiant)
    db.commit()
    
    print("Données de test créées avec succès!")

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Initialiser la base de données et créer les tables
    with app.app_context():
        init_db()
        seed_data()
    
    # Lancer l'application
    # IMPORTANT: Pour AWS, écouter sur 0.0.0.0:5000
    # Le port 5000 fonctionne, pas besoin de 80 pour le moment
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False  # debug=True uniquement en développement
    )
