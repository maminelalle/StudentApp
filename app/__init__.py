"""
Configuration et import des modèles
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "supnum_share.db")}'
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'zip'}

# Créer les dossiers s'ils n'existent pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)

# Moteur de base de données
engine = create_engine(DATABASE_URI, echo=False)
Session = scoped_session(sessionmaker(bind=engine))

# Importer les modèles
from .models import (
    Base,
    User,
    Filiere,
    Specialite,
    Semestre,
    Matiere,
    Devoir,
    Etudiant,
    Note,
    Document,
    DocumentVote,
    DocumentComment,
    Message,
    Notification,
)

# Créer les tables si nécessaire
Base.metadata.create_all(engine)

__all__ = [
    'engine',
    'Session',
    'Base',
    'User',
    'Filiere',
    'Specialite',
    'Semestre',
    'Matiere',
    'Devoir',
    'Etudiant',
    'Note',
    'Document',
    'DocumentVote',
    'DocumentComment',
    'Message',
    'Notification',
    'UPLOAD_FOLDER',
    'EXPORT_FOLDER',
    'MAX_UPLOAD_SIZE',
    'ALLOWED_EXTENSIONS',
]
