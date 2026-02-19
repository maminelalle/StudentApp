"""
Models package - définit toutes les classes de base de données
"""

from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

# Modèles d'authentification et utilisateurs
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    prenom = Column(String(50), nullable=False)
    nom = Column(String(50), nullable=False)
    role = Column(String(20), default="etudiant")  # admin ou etudiant
    actif = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    etudiant = relationship("Etudiant", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    votes = relationship("DocumentVote", back_populates="etudiant")
    commentaires = relationship("DocumentComment", back_populates="etudiant")
    
    def set_password(self, password):
        """Hash et stocke le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == "admin"
    
    def is_student(self):
        return self.role == "etudiant"
    
    def __repr__(self):
        return f"<User {self.username}>"


# Modèles académiques
class Filiere(Base):
    __tablename__ = "filieres"
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(50), nullable=False, unique=True)  # L1, L2, L3
    description = Column(String(255))
    
    etudiants = relationship("Etudiant", back_populates="filiere")
    specialites = relationship("Specialite", back_populates="filiere")
    matieres = relationship("Matiere", back_populates="filiere")
    
    def __repr__(self):
        return f"<Filiere {self.nom}>"


class Specialite(Base):
    __tablename__ = "specialites"
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)  # DSI, RSS, CNM
    code = Column(String(20), nullable=False)
    description = Column(String(255))
    filiere_id = Column(Integer, ForeignKey("filieres.id"), nullable=False)
    
    filiere = relationship("Filiere", back_populates="specialites")
    etudiants = relationship("Etudiant", back_populates="specialite")
    matieres = relationship("Matiere", back_populates="specialite")
    
    def __repr__(self):
        return f"<Specialite {self.nom}>"


class Semestre(Base):
    __tablename__ = "semestres"
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(10), nullable=False, unique=True)  # S1, S2, ..., S6
    numero = Column(Integer, nullable=False)  # 1, 2, 3, 4, 5, 6
    
    matieres = relationship("Matiere", back_populates="semestre")
    
    def __repr__(self):
        return f"<Semestre {self.nom}>"


class Matiere(Base):
    __tablename__ = "matieres"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False, unique=True)  # INFO101
    nom = Column(String(100), nullable=False)
    coefficient = Column(Float, default=1.0)
    semestre_id = Column(Integer, ForeignKey("semestres.id"), nullable=False)
    filiere_id = Column(Integer, ForeignKey("filieres.id"), nullable=False)
    specialite_id = Column(Integer, ForeignKey("specialites.id"), nullable=False)
    seuil_validation = Column(Float, default=10.0)
    rattrapable = Column(Boolean, default=True)
    
    semestre = relationship("Semestre", back_populates="matieres")
    filiere = relationship("Filiere", back_populates="matieres")
    specialite = relationship("Specialite", back_populates="matieres")
    devoirs = relationship("Devoir", back_populates="matiere", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="matiere", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="matiere")
    
    def __repr__(self):
        return f"<Matiere {self.nom}>"


class Devoir(Base):
    __tablename__ = "devoirs"
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    description = Column(Text)
    date = Column(Date, nullable=False)
    type_examen = Column(String(20), nullable=False)  # TP, Écrit, Projet, Machine
    session = Column(String(20), nullable=False, default="Normale")  # Normale, Rattrapage
    coefficient = Column(Float, default=1.0)
    matiere_id = Column(Integer, ForeignKey("matieres.id"), nullable=False)
    
    matiere = relationship("Matiere", back_populates="devoirs")
    notes = relationship("Note", back_populates="devoir", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Devoir {self.nom}>"


class Etudiant(Base):
    __tablename__ = "etudiants"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    filiere_id = Column(Integer, ForeignKey("filieres.id"), nullable=False)
    specialite_id = Column(Integer, ForeignKey("specialites.id"), nullable=False)
    semestre_id = Column(Integer, ForeignKey("semestres.id"), nullable=False)
    numero_inscription = Column(String(50), unique=True, nullable=False)
    
    user = relationship("User", back_populates="etudiant")
    filiere = relationship("Filiere", back_populates="etudiants")
    specialite = relationship("Specialite", back_populates="etudiants")
    semestre = relationship("Semestre")
    notes = relationship("Note", back_populates="etudiant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Etudiant {self.user.prenom} {self.user.nom}>"


class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True)
    valeur = Column(Float, nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_modification = Column(DateTime, onupdate=datetime.utcnow)
    etudiant_id = Column(Integer, ForeignKey("etudiants.id"), nullable=False)
    matiere_id = Column(Integer, ForeignKey("matieres.id"), nullable=False)
    devoir_id = Column(Integer, ForeignKey("devoirs.id"), nullable=True)
    
    etudiant = relationship("Etudiant", back_populates="notes")
    matiere = relationship("Matiere", back_populates="notes")
    devoir = relationship("Devoir", back_populates="notes")
    
    def __repr__(self):
        return f"<Note {self.valeur}>"


# Modèles pour le module Cours & Archives
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    titre = Column(String(200), nullable=False)
    description = Column(Text)
    type_document = Column(String(30), nullable=False)  # Cours, Résumé, Examen, TD, TP, Projet
    matiere_id = Column(Integer, ForeignKey("matieres.id"), nullable=False)
    semestre_id = Column(Integer, ForeignKey("semestres.id"), nullable=False)
    filiere_id = Column(Integer, ForeignKey("filieres.id"), nullable=False)
    specialite_id = Column(Integer, ForeignKey("specialites.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    fichier_path = Column(String(255), nullable=False)
    taille_fichier = Column(Integer)  # en bytes
    date_upload = Column(DateTime, default=datetime.utcnow)
    date_modification = Column(DateTime, onupdate=datetime.utcnow)
    telechargements = Column(Integer, default=0)
    
    matiere = relationship("Matiere", back_populates="documents")
    votes = relationship("DocumentVote", back_populates="document", cascade="all, delete-orphan")
    commentaires = relationship("DocumentComment", back_populates="document", cascade="all, delete-orphan")
    
    def moyenne_votes(self):
        """Calcule la moyenne des votes"""
        if not self.votes:
            return 0
        return sum(v.note for v in self.votes) / len(self.votes)
    
    def __repr__(self):
        return f"<Document {self.titre}>"


class DocumentVote(Base):
    __tablename__ = "document_votes"
    
    id = Column(Integer, primary_key=True)
    note = Column(Integer, nullable=False)  # 1-5 étoiles
    date_creation = Column(DateTime, default=datetime.utcnow)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    etudiant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    document = relationship("Document", back_populates="votes")
    etudiant = relationship("User", back_populates="votes")
    
    __table_args__ = (
        # Un étudiant ne peut voter qu'une fois par document
        # Sera géré au niveau applicatif
    )
    
    def __repr__(self):
        return f"<DocumentVote {self.note}/5>"


class DocumentComment(Base):
    __tablename__ = "document_comments"
    
    id = Column(Integer, primary_key=True)
    contenu = Column(Text, nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_modification = Column(DateTime, onupdate=datetime.utcnow)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    etudiant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    document = relationship("Document", back_populates="commentaires")
    etudiant = relationship("User", back_populates="commentaires")
    
    def __repr__(self):
        return f"<Comment {self.contenu[:50]}>"


# Modèle pour les notifications
class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True)
    titre = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type_notification = Column(String(30), nullable=False)  # note, devoir, document
    lue = Column(Boolean, default=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification {self.titre}>"


# Modèle pour la communication entre étudiants
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    contenu = Column(Text, nullable=False)
    type_message = Column(String(30), nullable=False)  # public (chat), private, cours_share
    # Pour public: semestre_id, pour private: destinataire_id, pour cours_share: document_id
    semestre_id = Column(Integer, ForeignKey("semestres.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    destinataire_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    expediteur_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_modification = Column(DateTime, onupdate=datetime.utcnow)
    lu = Column(Boolean, default=False)
    
    # Fichier joint optionnel pour partage
    fichier_path = Column(String(255), nullable=True)
    filename = Column(String(255), nullable=True)
    
    expediteur = relationship("User", foreign_keys=[expediteur_id])
    destinataire = relationship("User", foreign_keys=[destinataire_id])
    semestre = relationship("Semestre")
    document = relationship("Document")
    
    def __repr__(self):
        return f"<Message {self.contenu[:50]}>"


__all__ = [
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
]
