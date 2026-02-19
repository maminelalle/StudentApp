"""
SupNum Share - Plateforme Académique Moderne 2026
Design Professionnel avec Interface Responsive
"""

from flask import Flask, render_template_string, redirect, url_for, session, flash, request, send_file
from functools import wraps
from datetime import date
from werkzeug.utils import secure_filename
from markupsafe import Markup
import uuid
import os

from app import (
    engine, Session, Base, User, Filiere, Specialite, Semestre, 
    Matiere, Devoir, Etudiant, Note, Message, Document, UPLOAD_FOLDER,
    MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supnum-share-secret-2026'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE
Base.metadata.create_all(engine)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = Session().query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin():
            flash('Accès refusé.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def get_navbar(active='', is_admin=False, username=''):
    """Barre de navigation réutilisable"""
    admin_items = """
    <li class="nav-item"><a class="nav-link" href="/admin/dashboard"><i class="fas fa-chart-line"></i> Tableau de Bord</a></li>
    <li class="nav-item"><a class="nav-link" href="/admin/utilisateurs"><i class="fas fa-users"></i> Utilisateurs</a></li>
    <li class="nav-item"><a class="nav-link" href="/admin/matieres"><i class="fas fa-book"></i> Matières</a></li>
    <li class="nav-item"><a class="nav-link" href="/admin/documents"><i class="fas fa-folder-open"></i> Cours/Archives</a></li>
    <li class="nav-item"><a class="nav-link" href="/admin/notes"><i class="fas fa-chart-bar"></i> Notes</a></li>
    """
    student_items = """
    <li class="nav-item"><a class="nav-link" href="/student/dashboard"><i class="fas fa-home"></i> Tableau de Bord</a></li>
    <li class="nav-item"><a class="nav-link" href="/student/matieres"><i class="fas fa-book"></i> Mes Matières</a></li>
    <li class="nav-item"><a class="nav-link" href="/student/resultats"><i class="fas fa-award"></i> Résultats</a></li>
    <li class="nav-item"><a class="nav-link" href="/etudiant/ressources"><i class="fas fa-archive"></i> Ressources</a></li>
    <li class="nav-item"><a class="nav-link" href="/etudiant/chat"><i class="fas fa-comments"></i> Communication</a></li>
    """
    
    items = admin_items if is_admin else student_items
    
    return Markup(f"""
    <style>
        body {{
            background: #eef1f5 !important;
            color: #2f3b4a;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .container-fluid {{ padding: 24px 20px; max-width: 1200px; }}
        .title {{ color: #3b4a5a !important; font-weight: 700; }}
        .subtitle {{ color: #6b7a8a !important; }}
        .card {{
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
        }}
        .table thead {{ background-color: #f5f7fb !important; }}
        .btn-primary {{ background: #2f6fb2 !important; border: none !important; }}
        .btn-success {{ background: #2f8f55 !important; border: none !important; }}
        .btn-danger {{ background: #d14b4b !important; border: none !important; }}
    </style>
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top" style="background: #2f6fb2; box-shadow: 0 2px 8px rgba(0,0,0,0.12);">
        <div class="container-fluid">
            <a class="navbar-brand fw-bold" href="/" style="font-size: 22px; cursor: pointer; text-decoration: none;">
                <i class="fas fa-graduation-cap" style="color: #3b82f6;"></i> 
                <span style="color: #fff;">SupNum</span><span style="color: #3b82f6;">Share</span>
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    {items}
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user-circle"></i> {username}
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="/profile"><i class="fas fa-cog"></i> Profil</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt"></i> Déconnexion</a></li>
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    """)

@app.route('/')
def index():
    if 'user_id' in session:
        user = Session().query(User).filter_by(id=session['user_id']).first()
        return redirect(url_for('admin_dashboard' if user.is_admin() else 'student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Session().query(User).filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Bienvenue {user.prenom}!', 'success')
            return redirect(url_for('index'))
        flash('⚠️ Identifiants invalides', 'danger')
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SupNum Share - Connexion</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: #eef1f5;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .login-box {
                background: #ffffff;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 8px 20px rgba(0,0,0,0.08);
                padding: 50px 40px;
                max-width: 420px;
                width: 100%;
            }
            .login-header i {
                font-size: 56px;
                color: #2f6fb2;
                display: block;
                margin-bottom: 15px;
            }
            .login-header h1 {
                color: #1f2937;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            .form-control {
                border: 2px solid #e5e7eb;
                padding: 12px 16px;
                border-radius: 8px;
                transition: all 0.3s;
            }
            .form-control:focus {
                border-color: #2f6fb2;
                box-shadow: 0 0 0 3px rgba(47, 111, 178, 0.1);
            }
            .btn-login {
                background: #2f6fb2;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: 600;
                box-shadow: 0 4px 12px rgba(47, 111, 178, 0.3);
                transition: all 0.3s;
                color: white;
            }
            .btn-login:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <div class="login-header text-center">
                <i class="fas fa-graduation-cap"></i>
                <h1>SupNum<span style="color: #667eea;">Share</span></h1>
                <p class="text-muted">Plateforme Académique</p>
            </div>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="POST">
                <div class="mb-3">
                    <label class="form-label"><i class="fas fa-user"></i> Username</label>
                    <input type="text" class="form-control" name="username" required autofocus>
                </div>
                <div class="mb-3">
                    <label class="form-label"><i class="fas fa-lock"></i> Mot de passe</label>
                    <input type="password" class="form-control" name="password" required>
                </div>
                <button type="submit" class="btn btn-login w-100">
                    <i class="fas fa-sign-in-alt"></i> Connexion
                </button>
            </form>

            <hr>
            <p class="text-center text-muted small mt-3">
                © 2026 SupNum Share - Institut Supérieur du Numérique
            </p>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """)

@app.route('/logout')
def logout():
    session.clear()
    flash('Déconnecté avec succès.', 'info')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    
    # Créer les données de statistiques
    username = user.prenom
    stats = {
        'etudiants': db.query(User).filter_by(role='etudiant', actif=True).count(),
        'matieres': db.query(Matiere).count(),
        'admins': db.query(User).filter_by(role='admin', actif=True).count(),
        'total': db.query(User).count()
    }
    db.close()
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Admin Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; font-family: 'Segoe UI'; }
            .container-fluid { padding: 30px 20px; }
            .title { color: white; font-weight: 700; font-size: 28px; margin-bottom: 10px; }
            .subtitle { color: #cbd5e1; font-size: 14px; margin-bottom: 30px; }
            .stat-card {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-left: 5px solid #3b82f6;
                transition: all 0.3s;
                animation: slideInUp 0.6s ease;
            }
            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 30px rgba(0,0,0,0.15);
            }
            @keyframes slideInUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .stat-icon {
                font-size: 40px;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 10px;
                color: white;
            }
            .stat-icon.blue { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
            .stat-icon.green { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
            .stat-icon.purple { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); }
            .stat-icon.orange { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
            .stat-number { font-size: 32px; font-weight: 700; color: #1f2937; margin-top: 10px; }
            .stat-label { font-size: 14px; color: #6b7280; margin-top: 5px; }
            .action-card {
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin-top: 30px;
            }
            .btn-action {
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 600;
                border: none;
                margin-right: 10px;
                margin-bottom: 10px;
                transition: all 0.3s;
                color: white;
            }
            .btn-primary-grad {
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            }
            .btn-primary-grad:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
                color: white;
            }
            .btn-success-grad {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            }
            .btn-success-grad:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
                color: white;
            }
            .footer { text-align: center; color: #94a3b8; padding: 30px; border-top: 1px solid #334155; margin-top: 40px; }
        </style>
    </head>
    <body>
        {{ navbar }}
        <main class="container-fluid">
            <h1 class="title"><i class="fas fa-tachometer-alt"></i> Dashboard Admin</h1>
            <p class="subtitle">Gestion complète de la plateforme SupNum Share</p>

            <div class="row g-4">
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="d-flex justify-content-between">
                            <div>
                                <p class="stat-label">Étudiants</p>
                                <p class="stat-number">{{ stats['etudiants'] }}</p>
                            </div>
                            <div class="stat-icon blue"><i class="fas fa-users"></i></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="d-flex justify-content-between">
                            <div>
                                <p class="stat-label">Matières</p>
                                <p class="stat-number">{{ stats['matieres'] }}</p>
                            </div>
                            <div class="stat-icon green"><i class="fas fa-book"></i></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="d-flex justify-content-between">
                            <div>
                                <p class="stat-label">Administrateurs</p>
                                <p class="stat-number">{{ stats['admins'] }}</p>
                            </div>
                            <div class="stat-icon purple"><i class="fas fa-user-shield"></i></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="d-flex justify-content-between">
                            <div>
                                <p class="stat-label">Total Utilisateurs</p>
                                <p class="stat-number">{{ stats['total'] }}</p>
                            </div>
                            <div class="stat-icon orange"><i class="fas fa-chart-pie"></i></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="action-card">
                <h5 style="color: #1f2937; font-weight: 700; margin-bottom: 20px;">
                    <i class="fas fa-bolt"></i> Actions Rapides
                </h5>
                <a href="/admin/utilisateur/ajouter" class="btn btn-action btn-primary-grad">
                    <i class="fas fa-user-plus"></i> Ajouter Utilisateur
                </a>
                <a href="/admin/utilisateurs" class="btn btn-action btn-success-grad">
                    <i class="fas fa-list"></i> Gérer Utilisateurs
                </a>
                <a href="/admin/matieres" class="btn btn-action" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);">
                    <i class="fas fa-book-plus"></i> Gérer Matières
                </a>
                <a href="/admin/notes" class="btn btn-action" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
                    <i class="fas fa-chart-bar"></i> Gestion des Notes
                </a>
            </div>
        </main>
        <div class="footer">
            <p>© 2026 SupNum Share - Institut Supérieur du Numérique</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('admin_dashboard', True, username), stats=stats)

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant
    
    # Charger les relations avant de fermer la session
    if etudiant:
        filiere_nom = etudiant.filiere.nom if etudiant.filiere else "—"
        specialite_code = etudiant.specialite.code if etudiant.specialite else "—"
        semestre_nom = etudiant.semestre.nom if etudiant.semestre else "—"
        numero_inscription = etudiant.numero_inscription
        matieres = db.query(Matiere).filter_by(semestre_id=etudiant.semestre_id).all()
        notes = db.query(Note).filter_by(etudiant_id=etudiant.id).all()
    else:
        filiere_nom = specialite_code = semestre_nom = numero_inscription = "—"
        matieres = []
        notes = []
    
    moyenne = round(sum(n.valeur for n in notes) / len(notes), 2) if notes else 0
    
    # Créer des copie des données avant de fermer
    matieres_data = [(m.nom, m.code, m.coefficient) for m in matieres]
    notes_data = [(n.valeur, n.matiere.nom if n.matiere else "—") for n in notes]
    
    db.close()
    
    matieres_html = ''.join([f"""
    <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); border-left: 4px solid #3b82f6;">
        <div style="display: flex; justify-content: space-between;">
            <div>
                <div style="font-weight: 700; color: #1f2937;">{nom}</div>
                <div style="color: #6b7280; font-size: 12px; margin-top: 5px;">Code: {code}</div>
            </div>
            <span style="background: #f0f9ff; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;">Coef: {coef}</span>
        </div>
    </div>
    """ for nom, code, coef in matieres_data])
    
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Tableau de Bord Étudiant</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; font-family: 'Segoe UI'; }}
            .container-fluid {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 10px; }}
            .subtitle {{ color: #cbd5e1; font-size: 14px; margin-bottom: 30px; }}
            .profile-card {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-top: 5px solid #3b82f6;
                margin-bottom: 25px;
            }}
            .profile-avatar {{
                width: 80px;
                height: 80px;
                border-radius: 50%;
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 40px;
            }}
            .footer {{ text-align: center; color: #94a3b8; padding: 30px; border-top: 1px solid #334155; margin-top: 40px; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class="container-fluid">
            <h1 class="title"><i class="fas fa-home"></i> Tableau de Bord</h1>
            <p class="subtitle">Bienvenue {user.prenom}, consultez vos cours et résultats</p>

            <div class="profile-card">
                <div style="display: flex; gap: 20px; align-items: center;">
                    <div class="profile-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div>
                        <h5 style="color: #1f2937; font-weight: 700; margin-bottom: 5px;">
                            {user.prenom} {user.nom}
                        </h5>
                        <p style="color: #6b7280; margin-bottom: 8px;"><i class="fas fa-id-badge"></i> #{numero_inscription}</p>
                        <p style="color: #6b7280; margin-bottom: 0;">
                            <strong>{filiere_nom}</strong> • 
                            <strong>{specialite_code}</strong> • 
                            <strong>{semestre_nom}</strong>
                        </p>
                    </div>
                </div>
            </div>

            <div class="row g-4">
                <div class="col-md-8">
                    <h6 style="color: white; font-weight: 700; margin-bottom: 15px;">
                        <i class="fas fa-book"></i> Mes Matières ({len(matieres_data)})
                    </h6>
                    {matieres_html if matieres_html else '<p style="color: #cbd5e1;">Aucune matière assignée.</p>'}
                </div>

                <div class="col-md-4">
                    <h6 style="color: white; font-weight: 700; margin-bottom: 15px;">
                        <i class="fas fa-chart-line"></i> Statistiques
                    </h6>
                    <div style="background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
                        <div style="text-align: center; padding: 15px 0; border-bottom: 1px solid #e5e7eb;">
                            <div style="font-size: 32px; font-weight: 700; color: #3b82f6;">{len(notes_data)}</div>
                            <div style="color: #6b7280; font-size: 14px;">Notes Enregistrées</div>
                        </div>
                        <div style="text-align: center; padding: 15px 0;">
                            <div style="font-size: 28px; font-weight: 700; color: #10b981; margin-bottom: 5px;">{moyenne}</div>
                            <div style="color: #6b7280; font-size: 14px;">Moyenne Générale</div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
        <div class="footer">
            <p>© 2026 SupNum Share</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('student_dashboard', False, session.get('username')))

@app.route('/student/matieres')
@login_required
def student_matieres():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant

    if not etudiant:
        db.close()
        return redirect(url_for('student_dashboard'))

    matieres = db.query(Matiere).filter_by(semestre_id=etudiant.semestre_id).all()
    matieres_data = [(m.nom, m.code, m.coefficient, m.seuil_validation) for m in matieres]
    username = user.prenom
    db.close()

    matieres_html = ''.join([f"""
    <tr>
        <td><strong>{nom}</strong></td>
        <td><span class="badge bg-light text-dark">{code}</span></td>
        <td><span class="badge bg-info">{coeff}</span></td>
        <td>{seuil}</td>
    </tr>
    """ for nom, code, coeff, seuil in matieres_data])

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Mes Matières</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container-fluid {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class="container-fluid">
            <h1 class="title"><i class="fas fa-book"></i> Mes Matières du Semestre</h1>

            <div class="card">
                <div class="card-body">
                    <table class="table table-hover">
                        <thead style="background-color: #f0f9ff;">
                            <tr>
                                <th>Matière</th>
                                <th>Code</th>
                                <th>Coefficient</th>
                                <th>Seuil</th>
                            </tr>
                        </thead>
                        <tbody>
                            {matieres_html if matieres_html else '<tr><td colspan="4" style="text-align: center; color: #6b7280;">Aucune matière</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('matieres', False, username))

@app.route('/student/resultats')
@login_required
def student_resultats():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant
    notes = db.query(Note).filter_by(etudiant_id=etudiant.id).all() if etudiant else []
    
    # Charger les données avant de fermer la session
    notes_data = []
    for n in notes:
        notes_data.append({
            'valeur': n.valeur,
            'matiere_nom': n.matiere.nom if n.matiere else "—",
            'date': str(n.devoir.date) if n.devoir else "—"
        })
    
    db.close()
    
    notes_html = ''.join([f"""
    <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #3b82f6;">
        <div>
            <h6 style="color: #1f2937; font-weight: 700; margin-bottom: 5px;">{n['matiere_nom']}</h6>
            <p style="color: #6b7280; font-size: 13px; margin-bottom: 0;"><i class="fas fa-calendar"></i> {n['date']}</p>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: #10b981;">{n['valeur']}</div>
            <span style="font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 20px; background: {'#d1fae5; color: #065f46;' if n['valeur'] >= 10 else '#fee2e2; color: #991b1b;'}">
                {'✓ Validée' if n['valeur'] >= 10 else '✗ Non validée'}
            </span>
        </div>
    </div>
    """ for n in notes_data])
    
    return render_template_string(f"""
    <!DOCTYPE html> 
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Mes Résultats</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; font-family: 'Segoe UI'; }}
            .container-fluid {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 10px; }}
            .subtitle {{ color: #cbd5e1; font-size: 14px; margin-bottom: 30px; }}
            .footer {{ text-align: center; color: #94a3b8; padding: 30px; border-top: 1px solid #334155; margin-top: 40px; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class="container-fluid">
            <h1 class="title"><i class="fas fa-award"></i> Mes Résultats</h1>
            <p class="subtitle">Consultez vos notes et résultats académiques</p>

            <div class="row">
                <div class="col-md-12">
                    {notes_html}
                    {'<p style="color: #cbd5e1; text-align: center; padding: 40px;">Aucune note enregistrée pour le moment.</p>' if not notes_data else ''}
                </div>
            </div>
        </main>
        <div class="footer">
            <p>© 2026 SupNum Share</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('resultats', False, session.get('username')))

@app.route('/admin/utilisateurs')
@admin_required
def admin_utilisateurs():
    db = Session()
    users = db.query(User).all()
    # Load all data BEFORE closing session
    users_data = [(u.username, u.email, u.prenom, u.nom, u.role, u.actif) for u in users]
    db.close()
    
    users_html = ''.join([f"""
    <tr>
        <td><strong>{username}</strong></td>
        <td>{email}</td>
        <td>{prenom} {nom}</td>
        <td><span class="badge bg-primary">{role}</span></td>
        <td><span class="badge {'bg-success' if actif else 'bg-secondary'}">{'✓ Actif' if actif else 'Inactif'}</span></td>
    </tr>
    """ for username, email, prenom, nom, role, actif in users_data])
    
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Utilisateurs</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container-fluid {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .btn-primary {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none; }}
            .btn-primary:hover {{ color: white; }}
            .footer {{ text-align: center; color: #94a3b8; padding: 30px; border-top: 1px solid #334155; margin-top: 40px; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class="container-fluid">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                <h1 class="title"><i class="fas fa-users"></i> Gestion des Utilisateurs</h1>
                <a href="/admin/utilisateur/ajouter" class="btn btn-primary"><i class="fas fa-user-plus"></i> Ajouter</a>
            </div>

            <div class="card">
                <div class="card-body">
                    <table class="table table-hover">
                        <thead style="background-color: #f0f9ff;">
                            <tr>
                                <th><i class="fas fa-user"></i> Username</th>
                                <th><i class="fas fa-envelope"></i> Email</th>
                                <th><i class="fas fa-id-card"></i> Nom Complet</th>
                                <th><i class="fas fa-shield"></i> Rôle</th>
                                <th><i class="fas fa-check-circle"></i> Statut</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
        <div class="footer">
            <p>© 2026 SupNum Share</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('utilisateurs', True, session.get('username')))

@app.route('/admin/utilisateur/ajouter', methods=['GET', 'POST'])
@admin_required
def admin_ajouter_utilisateur():
    if request.method == 'POST':
        db = Session()
        try:
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                prenom=request.form['prenom'],
                nom=request.form['nom'],
                role=request.form.get('role', 'etudiant'),
                actif=True
            )
            user.set_password(request.form['password'])
            db.add(user)
            db.commit()
            
            if user.role == 'etudiant':
                etudiant = Etudiant(
                    user_id=user.id,
                    filiere_id=request.form.get('filiere_id'),
                    specialite_id=request.form.get('specialite_id'),
                    semestre_id=request.form.get('semestre_id'),
                    numero_inscription=request.form.get('numero_inscription', '')
                )
                db.add(etudiant)
                db.commit()
            
            db.close()
            flash(f'✓ Utilisateur {user.username} créé avec succès!', 'success')
            return redirect(url_for('admin_utilisateurs'))
        except Exception as e:
            db.close()
            flash(f'❌ Erreur: {str(e)}', 'danger')
    
    db = Session()
    filieres = db.query(Filiere).all()
    specialites = db.query(Specialite).all()
    semestres = db.query(Semestre).all()
    # Load all data BEFORE closing session
    filieres_data = [(f.id, f.nom) for f in filieres]
    specialites_data = [(s.id, s.nom) for s in specialites]
    semestres_data = [(s.id, s.nom) for s in semestres]
    db.close()
    
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Ajouter Utilisateur</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .btn-primary {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none; }}
            .btn-primary:hover {{ color: white; }}
            .footer {{ text-align: center; color: #94a3b8; padding: 30px; border-top: 1px solid #334155; margin-top: 40px; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <div class="container" style="max-width: 600px;">
            <h1 class="title"><i class="fas fa-user-plus"></i> Ajouter Utilisateur</h1>

            <div class="card">
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input type="text" class="form-control" name="username" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-control" name="email" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Prénom</label>
                            <input type="text" class="form-control" name="prenom" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Nom</label>
                            <input type="text" class="form-control" name="nom" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Mot de passe</label>
                            <input type="password" class="form-control" name="password" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Rôle</label>
                            <select class="form-control" name="role" id="role" onchange="toggleStudentFields()" required>
                                <option value="etudiant">Étudiant</option>
                                <option value="admin">Administrateur</option>
                            </select>
                        </div>

                        <div id="studentFields">
                            <div class="mb-3">
                                <label class="form-label">Filière</label>
                                <select class="form-control" name="filiere_id">
                                    <option>-- Sélectionner --</option>
                                    {''.join([f'<option value="{fid}">{fname}</option>' for fid, fname in filieres_data])}
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Spécialité</label>
                                <select class="form-control" name="specialite_id">
                                    <option>-- Sélectionner --</option>
                                    {''.join([f'<option value="{sid}">{snom}</option>' for sid, snom in specialites_data])}
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Semestre</label>
                                <select class="form-control" name="semestre_id">
                                    <option>-- Sélectionner --</option>
                                    {''.join([f'<option value="{sid}">{snom}</option>' for sid, snom in semestres_data])}
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Numéro d'inscription</label>
                                <input type="text" class="form-control" name="numero_inscription">
                            </div>
                        </div>

                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-save"></i> Créer
                        </button>
                    </form>
                </div>
            </div>
        </div>

        <script>
            function toggleStudentFields() {{
                document.getElementById('studentFields').style.display = 
                    document.getElementById('role').value === 'etudiant' ? 'block' : 'none';
            }}
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('ajouter_utilisateur', True, session.get('username')))

@app.route('/admin/matieres')
@admin_required
def admin_matieres():
    db = Session()
    semestres = db.query(Semestre).order_by(Semestre.numero).all()
    semestres_data = []
    for semestre in semestres:
        matieres = (
            db.query(Matiere)
            .filter_by(semestre_id=semestre.id)
            .order_by(Matiere.nom)
            .all()
        )
        matieres_rows = [(m.code, m.nom, m.coefficient, m.seuil_validation) for m in matieres]
        semestres_data.append((semestre.nom, matieres_rows))

    user = db.query(User).filter_by(id=session['user_id']).first()
    username = user.prenom if user else ''
    db.close()

    semestres_html = ""
    for semestre_nom, matieres_rows in semestres_data:
        if matieres_rows:
            rows_html = ''.join([f"""
            <tr>
                <td><span class="badge bg-light text-dark">{code}</span></td>
                <td><strong>{nom}</strong></td>
                <td><span class="badge bg-info">{coefficient}</span></td>
                <td>{seuil}</td>
            </tr>
            """ for code, nom, coefficient, seuil in matieres_rows])
        else:
            rows_html = "<tr><td colspan=\"4\" style=\"text-align: center; color: #6b7280;\">Aucune matière</td></tr>"

        semestres_html += f"""
        <div class="card" style="margin-bottom: 20px;">
            <div class="card-body">
                <h5 style=\"margin-bottom: 15px; color: #1f2937;\">{semestre_nom}</h5>
                <table class=\"table table-hover\">
                    <thead style=\"background-color: #f0f9ff;\">
                        <tr>
                            <th>Code</th>
                            <th>Matière</th>
                            <th>Coefficient</th>
                            <th>Seuil</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        """

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Matières</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: #eef1f5; min-height: 100vh; }
            .container-fluid { padding: 24px 20px; max-width: 1200px; }
            .title { color: #3b4a5a; font-weight: 700; font-size: 26px; margin-bottom: 24px; }
            .card { background: white; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
            .btn-success { background: #2f8f55; border: none; }
            .btn-success:hover { color: white; }
            .footer { text-align: center; color: #6b7a8a; padding: 24px; margin-top: 30px; }
        </style>
    </head>
    <body>
        {{ navbar }}
        <main class="container-fluid">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                <h1 class="title"><i class="fas fa-book"></i> Gestion des Matières</h1>
                <a href="/admin/matiere/ajouter" class="btn btn-success"><i class="fas fa-plus"></i> Ajouter</a>
            </div>

            {{ semestres_html }}
        </main>
        <div class="footer">
            <p>© 2026 SupNum Share</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('matieres', True, username), semestres_html=Markup(semestres_html))

@app.route('/admin/matiere/ajouter', methods=['GET', 'POST'])
@admin_required
def admin_ajouter_matiere():
    if request.method == 'POST':
        db = Session()
        try:
            matiere = Matiere(
                code=request.form['code'],
                nom=request.form['nom'],
                coefficient=float(request.form['coefficient']),
                semestre_id=request.form['semestre_id'],
                filiere_id=request.form['filiere_id'],
                specialite_id=request.form['specialite_id'],
                seuil_validation=float(request.form['seuil_validation'])
            )
            db.add(matiere)
            db.commit()
            db.close()
            flash('✓ Matière ajoutée avec succès!', 'success')
            return redirect(url_for('admin_matieres'))
        except Exception as e:
            db.close()
            flash(f'❌ Erreur: {str(e)}', 'danger')
    
    db = Session()
    semestres = db.query(Semestre).all()
    filieres = db.query(Filiere).all()
    specialites = db.query(Specialite).all()
    # Load all data BEFORE closing session
    semestres_data = [(s.id, s.nom) for s in semestres]
    filieres_data = [(f.id, f.nom) for f in filieres]
    specialites_data = [(s.id, s.nom) for s in specialites]
    db.close()
    
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Ajouter Matière</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .btn-success {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); border: none; }}
            .btn-success:hover {{ color: white; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <div class="container" style="max-width: 600px;">
            <h1 class="title"><i class="fas fa-plus"></i> Ajouter Matière</h1>

            <div class="card">
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Code</label>
                            <input type="text" class="form-control" name="code" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Nom</label>
                            <input type="text" class="form-control" name="nom" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Coefficient</label>
                            <input type="number" class="form-control" name="coefficient" step="0.5" value="1.0" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Semestre</label>
                            <select class="form-control" name="semestre_id" required>
                                <option>-- Sélectionner --</option>
                                {''.join([f'<option value="{sid}">{snom}</option>' for sid, snom in semestres_data])}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Filière</label>
                            <select class="form-control" name="filiere_id" required>
                                <option>-- Sélectionner --</option>
                                {''.join([f'<option value="{fid}">{fname}</option>' for fid, fname in filieres_data])}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Spécialité</label>
                            <select class="form-control" name="specialite_id" required>
                                <option>-- Sélectionner --</option>
                                {''.join([f'<option value="{sid}">{snom}</option>' for sid, snom in specialites_data])}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Seuil de Validation</label>
                            <input type="number" class="form-control" name="seuil_validation" step="0.5" value="10.0" required>
                        </div>
                        <button type="submit" class="btn btn-success w-100">
                            <i class="fas fa-save"></i> Créer
                        </button>
                    </form>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('ajouter_matiere', True, session.get('username')))

@app.route('/admin/notes', methods=['GET', 'POST'])
@admin_required
def admin_notes():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    username = user.prenom if user else ''

    if request.method == 'POST':
        try:
            note = Note(
                valeur=float(request.form.get('valeur')),
                etudiant_id=int(request.form.get('etudiant_id')),
                matiere_id=int(request.form.get('matiere_id')),
                devoir_id=int(request.form.get('devoir_id')) if request.form.get('devoir_id') else None
            )
            db.add(note)
            db.commit()
            flash('Note ajoutée.', 'success')
        except Exception as e:
            db.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    etudiants = db.query(Etudiant).all()
    matieres = db.query(Matiere).all()
    devoirs = db.query(Devoir).all()
    notes = db.query(Note).all()

    etudiants_data = [
        (e.id, f"{e.user.prenom} {e.user.nom} ({e.numero_inscription})")
        for e in etudiants
    ]
    matieres_data = [(m.id, f"{m.nom} ({m.code})") for m in matieres]
    devoirs_data = [(d.id, d.nom) for d in devoirs]

    notes_rows = []
    for n in notes:
        etu = n.etudiant
        filiere = etu.filiere.nom if etu and etu.filiere else '—'
        specialite = etu.specialite.nom if etu and etu.specialite else '—'
        etu_nom = f"{etu.user.prenom} {etu.user.nom}" if etu and etu.user else '—'
        matiere_nom = n.matiere.nom if n.matiere else '—'
        devoir_nom = n.devoir.nom if n.devoir else '—'
        date_note = n.date_creation.strftime('%d/%m/%Y') if n.date_creation else '—'
        notes_rows.append((filiere, specialite, etu_nom, matiere_nom, devoir_nom, n.valeur, date_note, n.id))

    grouped = {}
    for row in notes_rows:
        filiere, specialite = row[0], row[1]
        grouped.setdefault(filiere, {}).setdefault(specialite, []).append(row)

    sections_html = ""
    if grouped:
        for filiere, specs in grouped.items():
            sections_html += f"""
            <div class=\"card\" style=\"margin-bottom: 20px;\">
                <div class=\"card-body\">
                    <h5 style=\"margin-bottom: 10px; color: #2f3b4a;\">Filière: {filiere}</h5>
            """
            for specialite, rows in specs.items():
                rows_html = ''.join([f"""
                <tr>
                    <td>{etu_nom}</td>
                    <td>{matiere_nom}</td>
                    <td>{devoir_nom}</td>
                    <td><strong>{valeur}</strong></td>
                    <td>{date_note}</td>
                    <td>
                        <a href=\"/admin/note/edit/{note_id}\" class=\"btn btn-sm btn-primary\">Éditer</a>
                        <a href=\"/admin/note/delete/{note_id}\" class=\"btn btn-sm btn-danger\" onclick=\"return confirm('Supprimer cette note ?')\">Supprimer</a>
                    </td>
                </tr>
                """ for _, _, etu_nom, matiere_nom, devoir_nom, valeur, date_note, note_id in rows])

                sections_html += f"""
                <div style=\"margin-top: 15px;\">
                    <h6 style=\"color: #6b7a8a;\">Spécialité: {specialite}</h6>
                    <table class=\"table table-hover\">
                        <thead style=\"background-color: #f5f7fb;\">
                            <tr>
                                <th>Étudiant</th>
                                <th>Matière</th>
                                <th>Devoir</th>
                                <th>Note</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
                """
            sections_html += "</div></div>"
    else:
        sections_html = "<div class=\"card\"><div class=\"card-body\"><p>Aucune note enregistrée.</p></div></div>"

    db.close()

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang=\"fr\">
    <head>
        <meta charset=\"UTF-8\">
        <title>Gestion des Notes</title>
        <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
        <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css\">
        <style>
            body {{ background: #eef1f5; min-height: 100vh; }}
            .container-fluid {{ padding: 24px 20px; max-width: 1200px; }}
            .title {{ color: #3b4a5a; font-weight: 700; font-size: 26px; margin-bottom: 20px; }}
            .card {{ background: white; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class=\"container-fluid\">
            <h1 class=\"title\"><i class=\"fas fa-chart-bar\"></i> Gestion des Notes</h1>

            <div class=\"card\" style=\"margin-bottom: 20px;\">
                <div class=\"card-body\">
                    <h5 style=\"margin-bottom: 15px;\">Ajouter une note</h5>
                    <form method=\"POST\">
                        <div class=\"row g-3\">
                            <div class=\"col-md-3\">
                                <label class=\"form-label\">Étudiant</label>
                                <select class=\"form-control\" name=\"etudiant_id\" required>
                                    {''.join([f'<option value="{eid}">{ename}</option>' for eid, ename in etudiants_data])}
                                </select>
                            </div>
                            <div class=\"col-md-3\">
                                <label class=\"form-label\">Matière</label>
                                <select class=\"form-control\" name=\"matiere_id\" required>
                                    {''.join([f'<option value="{mid}">{mname}</option>' for mid, mname in matieres_data])}
                                </select>
                            </div>
                            <div class=\"col-md-3\">
                                <label class=\"form-label\">Devoir (optionnel)</label>
                                <select class=\"form-control\" name=\"devoir_id\">
                                    <option value=\"\">—</option>
                                    {''.join([f'<option value="{did}">{dname}</option>' for did, dname in devoirs_data])}
                                </select>
                            </div>
                            <div class=\"col-md-3\">
                                <label class=\"form-label\">Note</label>
                                <input type=\"number\" name=\"valeur\" step=\"0.5\" class=\"form-control\" required>
                            </div>
                        </div>
                        <div style=\"margin-top: 15px;\">
                            <button class=\"btn btn-primary\" type=\"submit\">Ajouter</button>
                        </div>
                    </form>
                </div>
            </div>

            {sections_html}
        </main>
        <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js\"></script>
    </body>
    </html>
    """, navbar=get_navbar('notes', True, username))

@app.route('/admin/note/edit/<int:note_id>', methods=['GET', 'POST'])
@admin_required
def admin_note_edit(note_id):
    db = Session()
    note = db.query(Note).filter_by(id=note_id).first()
    if not note:
        db.close()
        flash('Note introuvable.', 'danger')
        return redirect(url_for('admin_notes'))

    if request.method == 'POST':
        try:
            note.valeur = float(request.form.get('valeur'))
            note.etudiant_id = int(request.form.get('etudiant_id'))
            note.matiere_id = int(request.form.get('matiere_id'))
            note.devoir_id = int(request.form.get('devoir_id')) if request.form.get('devoir_id') else None
            db.commit()
            db.close()
            flash('Note modifiée.', 'success')
            return redirect(url_for('admin_notes'))
        except Exception as e:
            db.rollback()
            flash(f'Erreur: {str(e)}', 'danger')

    etudiants = db.query(Etudiant).all()
    matieres = db.query(Matiere).all()
    devoirs = db.query(Devoir).all()
    etudiants_data = [(e.id, f"{e.user.prenom} {e.user.nom} ({e.numero_inscription})") for e in etudiants]
    matieres_data = [(m.id, f"{m.nom} ({m.code})") for m in matieres]
    devoirs_data = [(d.id, d.nom) for d in devoirs]

    selected = {
        'etudiant_id': note.etudiant_id,
        'matiere_id': note.matiere_id,
        'devoir_id': note.devoir_id,
        'valeur': note.valeur
    }
    db.close()

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang=\"fr\">
    <head>
        <meta charset=\"UTF-8\">
        <title>Modifier Note</title>
        <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
        <style>
            body {{ background: #eef1f5; min-height: 100vh; }}
            .container {{ padding: 24px 20px; max-width: 700px; }}
            .card {{ background: white; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <div class=\"container\">
            <div class=\"card\">
                <div class=\"card-body\">
                    <h5 style=\"margin-bottom: 15px;\">Modifier une note</h5>
                    <form method=\"POST\">
                        <div class=\"row g-3\">
                            <div class=\"col-md-6\">
                                <label class=\"form-label\">Étudiant</label>
                                <select class=\"form-control\" name=\"etudiant_id\" required>
                                    {''.join([f'<option value="{eid}" {"selected" if eid == selected["etudiant_id"] else ""}>{ename}</option>' for eid, ename in etudiants_data])}
                                </select>
                            </div>
                            <div class=\"col-md-6\">
                                <label class=\"form-label\">Matière</label>
                                <select class=\"form-control\" name=\"matiere_id\" required>
                                    {''.join([f'<option value="{mid}" {"selected" if mid == selected["matiere_id"] else ""}>{mname}</option>' for mid, mname in matieres_data])}
                                </select>
                            </div>
                            <div class=\"col-md-6\">
                                <label class=\"form-label\">Devoir (optionnel)</label>
                                <select class=\"form-control\" name=\"devoir_id\">
                                    <option value=\"\">—</option>
                                    {''.join([f'<option value="{did}" {"selected" if selected["devoir_id"] == did else ""}>{dname}</option>' for did, dname in devoirs_data])}
                                </select>
                            </div>
                            <div class=\"col-md-6\">
                                <label class=\"form-label\">Note</label>
                                <input type=\"number\" name=\"valeur\" step=\"0.5\" class=\"form-control\" value=\"{selected['valeur']}\" required>
                            </div>
                        </div>
                        <div style=\"margin-top: 15px;\">
                            <button class=\"btn btn-primary\" type=\"submit\">Enregistrer</button>
                            <a href=\"/admin/notes\" class=\"btn btn-secondary\">Annuler</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js\"></script>
    </body>
    </html>
    """, navbar=get_navbar('notes', True, session.get('username')))

@app.route('/admin/note/delete/<int:note_id>')
@admin_required
def admin_note_delete(note_id):
    db = Session()
    note = db.query(Note).filter_by(id=note_id).first()
    if note:
        db.delete(note)
        db.commit()
        flash('Note supprimée.', 'success')
    else:
        flash('Note introuvable.', 'danger')
    db.close()
    return redirect(url_for('admin_notes'))

@app.route('/documents')
@login_required
def documents():
    user = Session().query(User).filter_by(id=session['user_id']).first()
    if user and user.is_admin():
        return redirect(url_for('admin_documents'))
    return redirect(url_for('etudiant_ressources'))

@app.route('/admin/documents', methods=['GET', 'POST'])
@admin_required
def admin_documents():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    username = user.prenom if user else ''

    if request.method == 'POST':
        fichier = request.files.get('fichier')
        if not fichier or fichier.filename == '':
            flash('Veuillez choisir un fichier.', 'warning')
        elif not allowed_file(fichier.filename):
            flash('Type de fichier non autorisé.', 'danger')
        else:
            safe_name = secure_filename(fichier.filename)
            unique_name = f"{uuid.uuid4().hex}_{safe_name}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            fichier.save(file_path)

            doc = Document(
                titre=request.form.get('titre', safe_name),
                description=request.form.get('description', ''),
                type_document=request.form.get('type_document', 'Cours'),
                matiere_id=int(request.form.get('matiere_id')),
                semestre_id=int(request.form.get('semestre_id')),
                filiere_id=int(request.form.get('filiere_id')),
                specialite_id=int(request.form.get('specialite_id')),
                filename=safe_name,
                fichier_path=file_path,
                taille_fichier=os.path.getsize(file_path)
            )
            db.add(doc)
            db.commit()
            flash('Document ajouté avec succès.', 'success')

    filieres = db.query(Filiere).all()
    specialites = db.query(Specialite).all()
    semestres = db.query(Semestre).order_by(Semestre.numero).all()
    matieres = db.query(Matiere).all()

    filieres_data = [(f.id, f.nom) for f in filieres]
    specialites_data = [(s.id, s.nom) for s in specialites]
    semestres_data = [(s.id, s.nom) for s in semestres]
    matieres_data = [(m.id, m.nom) for m in matieres]

    documents = db.query(Document).order_by(Document.date_upload.desc()).all()
    documents_data = [
        (d.id, d.titre, d.type_document, d.matiere.nom if d.matiere else 'N/A', d.date_upload.strftime('%d/%m/%Y'))
        for d in documents
    ]
    db.close()

    docs_html = ''.join([f"""
    <tr>
        <td>{titre}</td>
        <td><span class=\"badge bg-info\">{type_doc}</span></td>
        <td>{matiere}</td>
        <td>{date}</td>
        <td>
            <a href=\"/ressource/download/{doc_id}\" class=\"btn btn-sm btn-success\" style=\"background: linear-gradient(135deg, #10b981 0%, #059669 100%); border: none; color: white;\">
                <i class=\"fas fa-download\"></i>
            </a>
        </td>
    </tr>
    """ for doc_id, titre, type_doc, matiere, date in documents_data])

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang=\"fr\">
    <head>
        <meta charset=\"UTF-8\">
        <title>Cours et Archives</title>
        <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
        <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css\">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container-fluid {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 25px; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class=\"container-fluid\">
            <h1 class=\"title\"><i class=\"fas fa-folder-open\"></i> Cours et Archives</h1>

            <div class=\"card\">
                <div class=\"card-body\">
                    <h5 style=\"margin-bottom: 15px;\">Ajouter un document</h5>
                    <form method=\"POST\" enctype=\"multipart/form-data\">
                        <div class=\"row g-3\">
                            <div class=\"col-md-4\">
                                <label class=\"form-label\">Titre</label>
                                <input type=\"text\" name=\"titre\" class=\"form-control\" required>
                            </div>
                            <div class=\"col-md-4\">
                                <label class=\"form-label\">Type</label>
                                <select class=\"form-control\" name=\"type_document\" required>
                                    <option value=\"Cours\">Cours</option>
                                    <option value=\"TD\">TD</option>
                                    <option value=\"TP\">TP</option>
                                    <option value=\"Examen\">Examen</option>
                                    <option value=\"Archive\">Archive</option>
                                </select>
                            </div>
                            <div class=\"col-md-4\">
                                <label class=\"form-label\">Fichier</label>
                                <input type=\"file\" name=\"fichier\" class=\"form-control\" required>
                            </div>
                            <div class=\"col-md-4\">
                                <label class=\"form-label\">Filière</label>
                                <select class=\"form-control\" name=\"filiere_id\" required>
                                    {''.join([f'<option value="{fid}">{fname}</option>' for fid, fname in filieres_data])}
                                </select>
                            </div>
                            <div class=\"col-md-4\">
                                <label class=\"form-label\">Spécialité</label>
                                <select class=\"form-control\" name=\"specialite_id\" required>
                                    {''.join([f'<option value="{sid}">{snom}</option>' for sid, snom in specialites_data])}
                                </select>
                            </div>
                            <div class=\"col-md-4\">
                                <label class=\"form-label\">Semestre</label>
                                <select class=\"form-control\" name=\"semestre_id\" required>
                                    {''.join([f'<option value="{sid}">{snom}</option>' for sid, snom in semestres_data])}
                                </select>
                            </div>
                            <div class=\"col-md-6\">
                                <label class=\"form-label\">Matière</label>
                                <select class=\"form-control\" name=\"matiere_id\" required>
                                    {''.join([f'<option value="{mid}">{mnom}</option>' for mid, mnom in matieres_data])}
                                </select>
                            </div>
                            <div class=\"col-md-6\">
                                <label class=\"form-label\">Description</label>
                                <input type=\"text\" name=\"description\" class=\"form-control\">
                            </div>
                        </div>
                        <div style=\"margin-top: 15px;\">
                            <button class=\"btn btn-primary\" style=\"background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none;\">
                                <i class=\"fas fa-upload\"></i> Publier
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <div class=\"card\">
                <div class=\"card-body\">
                    <h5 style=\"margin-bottom: 15px;\">Documents publiés</h5>
                    <table class=\"table table-hover\">
                        <thead style=\"background-color: #f0f9ff;\">
                            <tr>
                                <th>Titre</th>
                                <th>Type</th>
                                <th>Matière</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {docs_html if docs_html else '<tr><td colspan="5" style="text-align: center; color: #6b7280;">Aucun document</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
        <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js\"></script>
    </body>
    </html>
    """, navbar=get_navbar('documents', True, username))

@app.route('/etudiant/ressources')
@login_required
def etudiant_ressources():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant

    if not etudiant:
        db.close()
        return redirect(url_for('student_dashboard'))

    documents = db.query(Document).filter(
        Document.semestre_id == etudiant.semestre_id,
        Document.filiere_id == etudiant.filiere_id,
        Document.specialite_id == etudiant.specialite_id
    ).order_by(Document.date_upload.desc()).all()

    docs_data = [
        (d.id, d.titre, d.type_document, d.matiere.nom if d.matiere else 'N/A', d.date_upload.strftime('%d/%m/%Y'))
        for d in documents
    ]

    matieres = db.query(Matiere).filter_by(semestre_id=etudiant.semestre_id).all()
    matieres_data = [(m.id, m.nom) for m in matieres]
    username = user.prenom
    db.close()

    docs_html = ''.join([f"""
    <tr>
        <td>{titre}</td>
        <td><span class=\"badge bg-info\">{type_doc}</span></td>
        <td>{matiere}</td>
        <td>{date}</td>
        <td>
            <a href=\"/ressource/download/{doc_id}\" class=\"btn btn-sm btn-success\" style=\"background: linear-gradient(135deg, #10b981 0%, #059669 100%); border: none; color: white;\">
                <i class=\"fas fa-download\"></i>
            </a>
        </td>
    </tr>
    """ for doc_id, titre, type_doc, matiere, date in docs_data])

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang=\"fr\">
    <head>
        <meta charset=\"UTF-8\">
        <title>Ressources</title>
        <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
        <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css\">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container-fluid {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 25px; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class=\"container-fluid\">
            <h1 class=\"title\"><i class=\"fas fa-archive\"></i> Ressources et Archives</h1>

            <div class=\"card\">
                <div class=\"card-body\">
                    <h5 style=\"margin-bottom: 15px;\">Partager un document</h5>
                    <form method=\"POST\" action=\"/etudiant/ressources/upload\" enctype=\"multipart/form-data\">
                        <div class=\"row g-3\">
                            <div class=\"col-md-4\">
                                <label class=\"form-label\">Titre</label>
                                <input type=\"text\" name=\"titre\" class=\"form-control\" required>
                            </div>
                            <div class=\"col-md-4\">
                                <label class=\"form-label\">Type</label>
                                <select class=\"form-control\" name=\"type_document\" required>
                                    <option value=\"Cours\">Cours</option>
                                    <option value=\"TD\">TD</option>
                                    <option value=\"TP\">TP</option>
                                    <option value=\"Examen\">Examen</option>
                                    <option value=\"Archive\">Archive</option>
                                </select>
                            </div>
                            <div class=\"col-md-4\">
                                <label class=\"form-label\">Fichier</label>
                                <input type=\"file\" name=\"fichier\" class=\"form-control\" required>
                            </div>
                            <div class=\"col-md-6\">
                                <label class=\"form-label\">Matière</label>
                                <select class=\"form-control\" name=\"matiere_id\" required>
                                    {''.join([f'<option value="{mid}">{mnom}</option>' for mid, mnom in matieres_data])}
                                </select>
                            </div>
                            <div class=\"col-md-6\">
                                <label class=\"form-label\">Description</label>
                                <input type=\"text\" name=\"description\" class=\"form-control\">
                            </div>
                        </div>
                        <div style=\"margin-top: 15px;\">
                            <button class=\"btn btn-primary\" style=\"background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none;\">
                                <i class=\"fas fa-upload\"></i> Partager
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <div class=\"card\">
                <div class=\"card-body\">
                    <h5 style=\"margin-bottom: 15px;\">Documents disponibles</h5>
                    <table class=\"table table-hover\">
                        <thead style=\"background-color: #f0f9ff;\">
                            <tr>
                                <th>Titre</th>
                                <th>Type</th>
                                <th>Matière</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {docs_html if docs_html else '<tr><td colspan="5" style="text-align: center; color: #6b7280;">Aucun document</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
        <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js\"></script>
    </body>
    </html>
    """, navbar=get_navbar('ressources', False, username))

@app.route('/etudiant/ressources/upload', methods=['POST'])
@login_required
def etudiant_ressources_upload():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant

    fichier = request.files.get('fichier')
    if not etudiant:
        db.close()
        return redirect(url_for('student_dashboard'))

    if not fichier or fichier.filename == '':
        flash('Veuillez choisir un fichier.', 'warning')
        db.close()
        return redirect(url_for('etudiant_ressources'))

    if not allowed_file(fichier.filename):
        flash('Type de fichier non autorisé.', 'danger')
        db.close()
        return redirect(url_for('etudiant_ressources'))

    safe_name = secure_filename(fichier.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    fichier.save(file_path)

    doc = Document(
        titre=request.form.get('titre', safe_name),
        description=request.form.get('description', ''),
        type_document=request.form.get('type_document', 'Cours'),
        matiere_id=int(request.form.get('matiere_id')),
        semestre_id=etudiant.semestre_id,
        filiere_id=etudiant.filiere_id,
        specialite_id=etudiant.specialite_id,
        filename=safe_name,
        fichier_path=file_path,
        taille_fichier=os.path.getsize(file_path)
    )
    db.add(doc)
    db.commit()
    db.close()

    flash('Document partagé.', 'success')
    return redirect(url_for('etudiant_ressources'))

@app.route('/etudiant/chat')
@login_required
def etudiant_chat():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant

    if not etudiant:
        db.close()
        return redirect(url_for('student_dashboard'))

    messages = db.query(Message).filter(
        Message.type_message == 'public',
        Message.semestre_id == etudiant.semestre_id
    ).order_by(Message.date_creation.desc()).limit(50).all()

    messages_data = [
        (
            m.expediteur.prenom if m.expediteur else 'Anonyme',
            m.contenu,
            m.date_creation.strftime('%d/%m/%Y %H:%M'),
            m.id,
            m.filename
        )
        for m in messages
    ]
    username = user.prenom
    db.close()

    messages_html = ''.join([f"""
    <div style=\"background: white; border-radius: 8px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);\">
        <p style=\"margin: 0; color: #1f2937;\"><strong>{expediteur}</strong> <span style=\"color: #9ca3af; font-size: 12px;\">{date}</span></p>
        <p style=\"margin: 8px 0 0 0; color: #4b5563;\">{contenu}</p>
        {f'<a href="/etudiant/chat/file/{message_id}" style="font-size: 12px;">📎 {filename}</a>' if filename else ''}
    </div>
    """ for expediteur, contenu, date, message_id, filename in messages_data])

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang=\"fr\">
    <head>
        <meta charset=\"UTF-8\">
        <title>Communication</title>
        <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
        <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css\">
        <style>
            body {{ background: #eef1f5; min-height: 100vh; }}
            .container-fluid {{ padding: 24px 20px; max-width: 1200px; }}
            .title {{ color: #3b4a5a; font-weight: 700; font-size: 26px; margin-bottom: 20px; }}
            .chat-box {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); min-height: 400px; display: flex; flex-direction: column; }}
            .messages-area {{ flex: 1; overflow-y: auto; margin-bottom: 20px; }}
            .form-area {{ border-top: 1px solid #e5e7eb; padding-top: 20px; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class=\"container-fluid\">
            <h1 class=\"title\"><i class=\"fas fa-comments\"></i> Communication du Semestre</h1>

            <div class=\"chat-box\">
                <div class=\"messages-area\">
                    {messages_html if messages_html else '<p style="color: #cbd5e1; text-align: center;">Aucun message pour le moment</p>'}
                </div>
                <div class=\"form-area\">
                    <form method=\"POST\" action=\"/etudiant/chat/send\" enctype=\"multipart/form-data\">
                        <div class=\"input-group\">
                            <input type=\"text\" class=\"form-control\" name=\"contenu\" placeholder=\"Écrivez votre message...\" required>
                            <button class=\"btn btn-primary\" type=\"submit\" style=\"background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none;\">
                                <i class=\"fas fa-paper-plane\"></i>
                            </button>
                        </div>
                        <div style=\"margin-top: 10px;\">
                            <input type=\"file\" class=\"form-control\" name=\"fichier\">
                        </div>
                    </form>
                </div>
            </div>
        </main>
        <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js\"></script>
    </body>
    </html>
    """, navbar=get_navbar('chat', False, username))

@app.route('/etudiant/chat/send', methods=['POST'])
@login_required
def etudiant_chat_send():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant

    if etudiant:
        contenu = request.form.get('contenu', '').strip()
        fichier = request.files.get('fichier')
        filename = None
        file_path = None

        if fichier and fichier.filename:
            if allowed_file(fichier.filename):
                safe_name = secure_filename(fichier.filename)
                unique_name = f"{uuid.uuid4().hex}_{safe_name}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                fichier.save(file_path)
                filename = safe_name
            else:
                flash('Type de fichier non autorisé.', 'danger')

        if contenu or filename:
            message = Message(
                contenu=contenu if contenu else 'Document partagé',
                type_message='public',
                semestre_id=etudiant.semestre_id,
                expediteur_id=user.id,
                fichier_path=file_path,
                filename=filename
            )
            db.add(message)
            db.commit()
            flash('Message envoyé.', 'success')

    db.close()
    return redirect(url_for('etudiant_chat'))

@app.route('/etudiant/chat/file/<int:message_id>')
@login_required
def etudiant_chat_file(message_id):
    db = Session()
    msg = db.query(Message).filter_by(id=message_id).first()
    file_path = msg.fichier_path if msg else None
    filename = msg.filename if msg else None
    db.close()

    if not file_path or not os.path.exists(file_path):
        flash('Fichier introuvable.', 'danger')
        return redirect(url_for('etudiant_chat'))

    return send_file(file_path, as_attachment=True, download_name=filename)

@app.route('/ressource/download/<int:doc_id>')
@login_required
def ressource_download(doc_id):
    db = Session()
    doc = db.query(Document).filter_by(id=doc_id).first()
    file_path = doc.fichier_path if doc else None
    filename = doc.filename if doc else None
    db.close()

    if not file_path or not os.path.exists(file_path):
        flash('Fichier introuvable.', 'danger')
        return redirect(url_for('etudiant_ressources'))

    return send_file(file_path, as_attachment=True, download_name=filename)

@app.route('/profile')
@login_required
def profile():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    # Extract data BEFORE closing session
    username = user.username
    email = user.email
    prenom = user.prenom
    nom = user.nom
    role = user.role
    db.close()
    
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Profil</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .btn-primary {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none; }}
            .btn-primary:hover {{ color: white; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <div class="container" style="max-width: 600px;">
            <h1 class="title"><i class="fas fa-user-circle"></i> Mon Profil</h1>
            <div class="card">
                <div class="card-body">
                    <div style="margin-bottom: 20px;">
                        <label style="color: #6b7280; font-weight: 600; font-size: 13px;">Username</label>
                        <p style="color: #1f2937; font-size: 15px;">{username}</p>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label style="color: #6b7280; font-weight: 600; font-size: 13px;">Email</label>
                        <p style="color: #1f2937; font-size: 15px;">{email}</p>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label style="color: #6b7280; font-weight: 600; font-size: 13px;">Nom Complet</label>
                        <p style="color: #1f2937; font-size: 15px;">{prenom} {nom}</p>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label style="color: #6b7280; font-weight: 600; font-size: 13px;">Rôle</label>
                        <p><span class="badge bg-primary">{role.capitalize()}</span></p>
                    </div>
                    <a href="/" class="btn btn-primary"><i class="fas fa-arrow-left"></i> Retour au Dashboard</a>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('profile', user.is_admin(), user.prenom))

@app.errorhandler(404)
def page_404(e):
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>404 - Page Non Trouvée</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .error-container { text-align: center; color: white; }
            .error-code { font-size: 120px; font-weight: 700; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .btn { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; padding: 12px 30px; border-radius: 8px; }
            .btn:hover { color: white; }
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-code">404</div>
            <h2 style="margin: 20px 0;">Page Non Trouvée</h2>
            <p style="color: #cbd5e1; margin-bottom: 30px;">La page que vous cherchez n'existe pas.</p>
            <a href="/" class="btn"><i class="fas fa-home"></i> Retour à l'Accueil</a>
        </div>
    </body>
    </html>
    """), 404

@app.errorhandler(500)
def page_500(e):
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>500 - Erreur Serveur</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .error-container { text-align: center; color: white; }
            .error-code { font-size: 120px; font-weight: 700; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .btn { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; padding: 12px 30px; border-radius: 8px; }
            .btn:hover { color: white; }
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-code">500</div>
            <h2 style="margin: 20px 0;">Erreur Serveur</h2>
            <p style="color: #cbd5e1; margin-bottom: 30px;">Une erreur est survenue sur le serveur.</p>
            <a href="/" class="btn"><i class="fas fa-home"></i> Retour à l'Accueil</a>
        </div>
    </body>
    </html>
    """), 500

def init_db():
    """Initialiser la base de données"""
    db = Session()
    
    if db.query(Filiere).count() > 0:
        print("✓ Base de données déjà initialisée")
        db.close()
        return
    
    print("🔧 Initialisation de la base de données...")
    
    # Filières
    filieres = [Filiere(nom='L1'), Filiere(nom='L2'), Filiere(nom='L3')]
    db.add_all(filieres)
    db.commit()
    
    # Spécialités
    specialites = []
    for f_id in [1, 2, 3]:
        for code, nom in [('DSI', 'Développement Système'), ('RSS', 'Réseau et Sécurité'), ('CNM', 'Multimédia')]:
            specialites.append(Specialite(nom=nom, code=code, filiere_id=f_id))
    db.add_all(specialites)
    db.commit()
    
    # Semestres
    semestres = [Semestre(nom=f'S{i}', numero=i) for i in range(1, 7)]
    db.add_all(semestres)
    db.commit()
    
    # Matières
    matieres = [
        Matiere(code='INFO101', nom='Programmation Python', coefficient=2.0, semestre_id=1, filiere_id=1, specialite_id=1),
        Matiere(code='INFO102', nom='Algorithmes', coefficient=2.0, semestre_id=1, filiere_id=1, specialite_id=1),
        Matiere(code='MATH101', nom='Mathématiques', coefficient=1.5, semestre_id=1, filiere_id=1, specialite_id=1),
        Matiere(code='WEB101', nom='Frontend', coefficient=2.0, semestre_id=1, filiere_id=1, specialite_id=2),
        Matiere(code='NET101', nom='Réseaux', coefficient=1.5, semestre_id=1, filiere_id=1, specialite_id=3),
    ]
    db.add_all(matieres)
    db.commit()
    
    # Admin
    admin = User(username='admin', email='admin@supnum.mr', prenom='Admin', nom='Supnum', role='admin', actif=True)
    admin.set_password('admin123')
    db.add(admin)
    db.commit()
    
    # Étudiants
    student = User(username='eddy', email='eddy@supnum.mr', prenom='Eddy', nom='Martin', role='etudiant', actif=True)
    student.set_password('eddy123')
    db.add(student)
    db.commit()
    
    etudiant = Etudiant(user_id=student.id, filiere_id=1, specialite_id=1, semestre_id=1, numero_inscription='2026-001')
    db.add(etudiant)
    db.commit()

    student2 = User(username='sara', email='sara@supnum.mr', prenom='Sara', nom='Dia', role='etudiant', actif=True)
    student2.set_password('1234')
    db.add(student2)
    db.commit()

    etudiant2 = Etudiant(user_id=student2.id, filiere_id=1, specialite_id=1, semestre_id=1, numero_inscription='2026-002')
    db.add(etudiant2)
    db.commit()

    student3 = User(username='omar', email='omar@supnum.mr', prenom='Omar', nom='Sow', role='etudiant', actif=True)
    student3.set_password('1234')
    db.add(student3)
    db.commit()

    etudiant3 = Etudiant(user_id=student3.id, filiere_id=1, specialite_id=1, semestre_id=1, numero_inscription='2026-003')
    db.add(etudiant3)
    db.commit()
    
    # Devoirs et Notes
    devoirs = [
        Devoir(nom='TP Python 1', date=date(2026, 2, 15), type_examen='TP', session='Normale', coefficient=1.0, matiere_id=1),
        Devoir(nom='Projet Algorithmes', date=date(2026, 2, 28), type_examen='Projet', session='Normale', coefficient=2.0, matiere_id=2),
        Devoir(nom='Examen Mathématiques', date=date(2026, 3, 15), type_examen='Écrit', session='Normale', coefficient=1.5, matiere_id=3),
    ]
    db.add_all(devoirs)
    db.commit()
    
    notes = [
        Note(valeur=15.5, etudiant_id=1, matiere_id=1, devoir_id=1),
        Note(valeur=12.0, etudiant_id=1, matiere_id=2, devoir_id=2),
        Note(valeur=13.5, etudiant_id=1, matiere_id=3, devoir_id=3),
    ]
    db.add_all(notes)
    db.commit()
    
    print("✓ Initialisé avec succès!")
    print("\n📝 Admin: admin / admin123")
    print("📝 Étudiant: eddy / eddy123")
    print("📝 Étudiant: sara / 1234")
    print("📝 Étudiant: omar / 1234")
    
    db.close()

if __name__ == '__main__':
    init_db()
    print("\n🚀 http://127.0.0.1:5000\n")
    app.run(host='127.0.0.1', port=5000, debug=True)
