"""
SupNum Share - Plateforme Académique Professionnelle
Institut Supérieur du Numérique (SupNum)
Application principale
"""

from flask import Flask, render_template, redirect, url_for, session, flash, request
from functools import wraps
import os

# Imports de l'application
from app import (
    engine,
    Session,
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
    Notification,
    UPLOAD_FOLDER,
    EXPORT_FOLDER,
)

# Créer l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supnum-share-secret-key-2026'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max

# Créer les tables
Base.metadata.create_all(engine)


# ======================== DÉCORATEURS ========================

def login_required(f):
    """Décorateur pour vérifier l'authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Décorateur pour vérifier les permissions administrateur"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        
        db_session = Session()
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        db_session.close()
        
        if not user or not user.is_admin():
            flash('Vous n\'avez pas les permissions nécessaires.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


# ======================== ROUTES D'AUTHENTIFICATION ========================

@app.route('/')
def index():
    """Page d'accueil"""
    if 'user_id' in session:
        user = Session().query(User).filter_by(id=session['user_id']).first()
        if user and user.is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me')
        
        db_session = Session()
        user = db_session.query(User).filter_by(username=username).first()
        
        if user and user.check_password(password) and user.actif:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            if remember:
                session.permanent = True
            
            db_session.close()
            
            flash(f'Bienvenue {user.prenom} !', 'success')
            return redirect(url_for('index'))
        
        db_session.close()
        flash('Identifiants invalides ou compte inactif.', 'danger')
    
    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('login'))


# ======================== ROUTES TABLEAU DE BORD ========================

@app.route('/dashboard')
@login_required
def dashboard():
    """Redirection vers le dashboard approprié"""
    user = Session().query(User).filter_by(id=session['user_id']).first()
    if user.is_admin():
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Dashboard administrateur"""
    db_session = Session()
    
    total_etudiants = db_session.query(User).filter_by(role='etudiant', actif=True).count()
    total_matieres = db_session.query(Matiere).count()
    total_documents = db_session.query(Document).count()
    
    db_session.close()
    
    return render_template('admin/dashboard.html',
                         total_etudiants=total_etudiants,
                         total_matieres=total_matieres,
                         total_documents=total_documents)


@app.route('/student/dashboard')
@login_required
def student_dashboard():
    """Dashboard étudiant"""
    db_session = Session()
    
    user = db_session.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant
    
    if not etudiant:
        db_session.close()
        flash('Profil étudiant non trouvé.', 'danger')
        return redirect(url_for('logout'))
    
    # Récupérer les notes
    notes = db_session.query(Note).filter_by(etudiant_id=etudiant.id).all()
    matieres = db_session.query(Matiere).filter_by(semestre_id=etudiant.semestre_id).all()
    notifications = db_session.query(Notification).filter_by(user_id=session['user_id'], lue=False).all()
    
    db_session.close()
    
    return render_template('student/dashboard.html',
                         etudiant=etudiant,
                         notes=notes,
                         matieres=matieres,
                         notifications=notifications,
                         nb_notifications=len(notifications))


# ======================== GESTION DES UTILISATEURS (ADMIN) ========================

@app.route('/admin/utilisateurs')
@admin_required
def admin_utilisateurs():
    """Liste des utilisateurs"""
    db_session = Session()
    utilisateurs = db_session.query(User).all()
    db_session.close()
    
    return render_template('admin/utilisateurs.html', utilisateurs=utilisateurs)


@app.route('/admin/utilisateur/ajouter', methods=['GET', 'POST'])
@admin_required
def admin_ajouter_utilisateur():
    """Ajouter un nouvel utilisateur"""
    db_session = Session()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        prenom = request.form.get('prenom')
        nom = request.form.get('nom')
        password = request.form.get('password')
        role = request.form.get('role')  # admin ou etudiant
        
        # Vérifier l'unicité
        if db_session.query(User).filter_by(username=username).first():
            flash('Le nom d\'utilisateur existe déjà.', 'danger')
            return redirect(url_for('admin_ajouter_utilisateur'))
        
        if db_session.query(User).filter_by(email=email).first():
            flash('L\'email existe déjà.', 'danger')
            return redirect(url_for('admin_ajouter_utilisateur'))
        
        # Créer l'utilisateur
        user = User(
            username=username,
            email=email,
            prenom=prenom,
            nom=nom,
            role=role,
            actif=True
        )
        user.set_password(password)
        
        db_session.add(user)
        db_session.commit()
        
        # Si c'est un étudiant, créer le profil étudiant
        if role == 'etudiant':
            filiere_id = request.form.get('filiere_id')
            specialite_id = request.form.get('specialite_id')
            semestre_id = request.form.get('semestre_id')
            numero_inscription = request.form.get('numero_inscription')
            
            etudiant = Etudiant(
                user_id=user.id,
                filiere_id=filiere_id,
                specialite_id=specialite_id,
                semestre_id=semestre_id,
                numero_inscription=numero_inscription
            )
            db_session.add(etudiant)
            db_session.commit()
        
        db_session.close()
        flash(f'Utilisateur {username} créé avec succès.', 'success')
        return redirect(url_for('admin_utilisateurs'))
    
    filieres = db_session.query(Filiere).all()
    specialites = db_session.query(Specialite).all()
    semestres = db_session.query(Semestre).all()
    
    db_session.close()
    
    return render_template('admin/utilisateur_form.html',
                         filieres=filieres,
                         specialites=specialites,
                         semestres=semestres)


# ======================== GESTION DES MATIÈRES ========================

@app.route('/admin/matieres')
@admin_required
def admin_matieres():
    """Liste des matières"""
    db_session = Session()
    matieres = db_session.query(Matiere).all()
    db_session.close()
    
    return render_template('admin/matieres.html', matieres=matieres)


@app.route('/admin/matiere/ajouter', methods=['GET', 'POST'])
@admin_required
def admin_ajouter_matiere():
    """Ajouter une nouvelle matière"""
    db_session = Session()
    
    if request.method == 'POST':
        code = request.form.get('code')
        nom = request.form.get('nom')
        coefficient = float(request.form.get('coefficient', 1.0))
        semestre_id = request.form.get('semestre_id')
        filiere_id = request.form.get('filiere_id')
        specialite_id = request.form.get('specialite_id')
        seuil_validation = float(request.form.get('seuil_validation', 10.0))
        rattrapable = request.form.get('rattrapable') == 'on'
        
        if db_session.query(Matiere).filter_by(code=code).first():
            flash('Ce code matière existe déjà.', 'danger')
        else:
            matiere = Matiere(
                code=code,
                nom=nom,
                coefficient=coefficient,
                semestre_id=semestre_id,
                filiere_id=filiere_id,
                specialite_id=specialite_id,
                seuil_validation=seuil_validation,
                rattrapable=rattrapable
            )
            db_session.add(matiere)
            db_session.commit()
            flash('Matière ajoutée avec succès.', 'success')
        
        db_session.close()
        return redirect(url_for('admin_matieres'))
    
    semestres = db_session.query(Semestre).all()
    filieres = db_session.query(Filiere).all()
    specialites = db_session.query(Specialite).all()
    
    db_session.close()
    
    return render_template('admin/matiere_form.html',
                         semestres=semestres,
                         filieres=filieres,
                         specialites=specialites)


# ======================== GESTION DES NOTES ========================

@app.route('/admin/notes')
@admin_required
def admin_notes():
    """Gestion des notes"""
    db_session = Session()
    notes = db_session.query(Note).all()
    db_session.close()
    
    return render_template('admin/notes.html', notes=notes)


@app.route('/student/resultats')
@login_required
def student_resultats():
    """Résultats académiques de l'étudiant"""
    db_session = Session()
    
    user = db_session.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant
    notes = db_session.query(Note).filter_by(etudiant_id=etudiant.id).all()
    matieres = db_session.query(Matiere).filter_by(semestre_id=etudiant.semestre_id).all()
    
    db_session.close()
    
    return render_template('student/resultats.html',
                         etudiant=etudiant,
                         notes=notes,
                         matieres=matieres)


# ======================== GESTION DES COURS & ARCHIVES ========================

@app.route('/documents')
@login_required
def documents_list():
    """Liste des documents (accessible à tous)"""
    db_session = Session()
    documents = db_session.query(Document).all()
    db_session.close()
    
    return render_template('documents/list.html', documents=documents)


@app.route('/documents/<int:document_id>')
@login_required
def document_detail(document_id):
    """Détail d'un document"""
    db_session = Session()
    document = db_session.query(Document).filter_by(id=document_id).first()
    
    if not document:
        flash('Document non trouvé.', 'danger')
        db_session.close()
        return redirect(url_for('documents_list'))
    
    # Incrémenter les téléchargements
    document.telechargements += 1
    db_session.commit()
    
    votes = db_session.query(Document).filter_by(id=document_id).first().votes
    commentaires = db_session.query(Document).filter_by(id=document_id).first().commentaires
    
    db_session.close()
    
    return render_template('documents/detail.html',
                         document=document,
                         votes=votes,
                         commentaires=commentaires)


@app.route('/admin/documents/ajouter', methods=['GET', 'POST'])
@admin_required
def admin_ajouter_document():
    """Ajouter un nouveau document (admin)"""
    if request.method == 'POST':
        # Logique d'upload du fichier
        flash('Fonctionnalité en développement.', 'info')
        return redirect(url_for('documents_list'))
    
    db_session = Session()
    matieres = db_session.query(Matiere).all()
    semestres = db_session.query(Semestre).all()
    filieres = db_session.query(Filiere).all()
    specialites = db_session.query(Specialite).all()
    db_session.close()
    
    return render_template('admin/document_form.html',
                         matieres=matieres,
                         semestres=semestres,
                         filieres=filieres,
                         specialites=specialites)


# ======================== GESTION DES DONNÉES INITIALES ========================

def init_db():
    """Initialiser la base de données avec des données par défaut"""
    db_session = Session()
    
    # Vérifier si les données existent déjà
    if db_session.query(Filiere).count() > 0:
        db_session.close()
        return
    
    # Créer les filières
    filieres = [
        Filiere(nom='L1', description='Licence 1ère année'),
        Filiere(nom='L2', description='Licence 2ème année'),
        Filiere(nom='L3', description='Licence 3ème année'),
    ]
    db_session.add_all(filieres)
    db_session.commit()
    
    # Créer les spécialités
    specialites = [
        Specialite(nom='Développement Système Informatique', code='DSI', filiere_id=1),
        Specialite(nom='Réseau et Sécurité', code='RSS', filiere_id=1),
        Specialite(nom='Développement Multimédia', code='CNM', filiere_id=1),
        Specialite(nom='Développement Système Informatique', code='DSI', filiere_id=2),
        Specialite(nom='Réseau et Sécurité', code='RSS', filiere_id=2),
        Specialite(nom='Développement Multimédia', code='CNM', filiere_id=2),
        Specialite(nom='Développement Système Informatique', code='DSI', filiere_id=3),
        Specialite(nom='Réseau et Sécurité', code='RSS', filiere_id=3),
        Specialite(nom='Développement Multimédia', code='CNM', filiere_id=3),
    ]
    db_session.add_all(specialites)
    db_session.commit()
    
    # Créer les semestres
    semestres = [
        Semestre(nom='S1', numero=1),
        Semestre(nom='S2', numero=2),
        Semestre(nom='S3', numero=3),
        Semestre(nom='S4', numero=4),
        Semestre(nom='S5', numero=5),
        Semestre(nom='S6', numero=6),
    ]
    db_session.add_all(semestres)
    db_session.commit()
    
    # Créer un utilisateur admin par défaut
    admin = User(
        username='admin',
        email='admin@supnum.mr',
        prenom='Admin',
        nom='SupNum',
        role='admin',
        actif=True
    )
    admin.set_password('admin123')
    db_session.add(admin)
    db_session.commit()
    
    print("✓ Base de données initialisée avec succès!")
    db_session.close()


# ======================== GESTION DES ERREURS ========================

@app.errorhandler(404)
def page_not_found(e):
    """Gérer les erreurs 404"""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """Gérer les erreurs 500"""
    return render_template('errors/500.html'), 500


# ======================== PROGRAMME PRINCIPAL ========================

if __name__ == '__main__':
    # Initialiser la base de données
    init_db()
    
    # Configurer le contexte de l'application
    with app.app_context():
        # Lancer l'application
        app.run(host='0.0.0.0', port=5000, debug=False)
