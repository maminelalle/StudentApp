"""
SupNum Share - Plateforme Académique Professionnelle
Design Moderne 2026 avec Interface Responsive
"""

from flask import Flask, render_template_string, redirect, url_for, session, flash, request, jsonify
from functools import wraps
from datetime import date, datetime
import os
import json

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
    UPLOAD_FOLDER,
)

# Créer l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supnum-share-secret-key-2026'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


def get_navbar_html(active_page='', is_admin=False, username=''):
    """Génère la barre de navigation"""
    admin_menu = """
    <li class="nav-item"><a class="nav-link" href="/admin/utilisateurs"><i class="fas fa-users"></i> Utilisateurs</a></li>
    <li class="nav-item"><a class="nav-link" href="/admin/matieres"><i class="fas fa-book"></i> Matières</a></li>
    <li class="nav-item"><a class="nav-link" href="/admin/notes"><i class="fas fa-chart-bar"></i> Notes</a></li>
    """
    
    student_menu = """
    <li class="nav-item"><a class="nav-link" href="/student/resultats"><i class="fas fa-award"></i> Résultats</a></li>
    <li class="nav-item"><a class="nav-link" href="/documents"><i class="fas fa-file"></i> Documents</a></li>
    """
    
    menu = admin_menu if is_admin else student_menu
    
    return f"""
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
        <div class="container-fluid">
            <a class="navbar-brand fw-bold" href="/" style="font-size: 22px; cursor: pointer;">
                <i class="fas fa-graduation-cap" style="color: #3b82f6;"></i> <span style="color: #fff;">SupNum</span><span style="color: #3b82f6;">Share</span>
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    {menu}
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user-circle"></i> {username}
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="/profile"><i class="fas fa-cog"></i> Paramètres</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt"></i> Déconnexion</a></li>
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    """


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion moderne"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db_session = Session()
        user = db_session.query(User).filter_by(username=username).first()
        
        if user and user.check_password(password) and user.actif:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            db_session.close()
            flash(f'Bienvenue {user.prenom} !', 'success')
            return redirect(url_for('index'))
        
        db_session.close()
        flash('Identifiants invalides ou compte inactif.', 'danger')
    
    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Connexion - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                animation: gradient 15s ease infinite;
                background-size: 400% 400%;
            }
            @keyframes gradient {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            .login-container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 50px 40px;
                max-width: 420px;
                width: 100%;
                animation: slideUp 0.6s ease;
            }
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .login-header {
                text-align: center;
                margin-bottom: 35px;
            }
            .login-header i {
                font-size: 56px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 15px;
                display: block;
            }
            .login-header h1 {
                color: #1F2937;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            .login-header p {
                color: #6B7280;
                font-size: 14px;
            }
            .form-control {
                border: 2px solid #E5E7EB;
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 14px;
                transition: all 0.3s;
            }
            .form-control:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .form-label {
                color: #374151;
                font-weight: 600;
                margin-bottom: 8px;
            }
            .btn-login {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
                transition: all 0.3s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            .btn-login:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
                color: white;
            }
            .demo-info {
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                border-left: 4px solid #0ea5e9;
                padding: 18px;
                border-radius: 8px;
                margin-bottom: 25px;
                font-size: 13px;
            }
            .demo-info strong {
                color: #0284c7;
                display: block;
                margin-bottom: 8px;
            }
            .demo-account {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                color: #0369a1;
            }
            .alert {
                border-radius: 8px;
                border: none;
                padding: 12px 16px;
            }
            .form-group {
                margin-bottom: 18px;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <i class="fas fa-graduation-cap"></i>
                <h1>SupNum<span style="color: #667eea;">Share</span></h1>
                <p>Plateforme Académique Nouvelle Génération</p>
            </div>

            <div class="demo-info">
                <strong><i class="fas fa-info-circle"></i> Comptes de Test</strong>
                <div class="demo-account">
                    <span>👨‍💼 Admin:</span>
                    <span><strong>admin</strong> / <strong>admin123</strong></span>
                </div>
                <div class="demo-account">
                    <span>👨‍🎓 Étudiant:</span>
                    <span><strong>eddy</strong> / <strong>eddy123</strong></span>
                </div>
            </div>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                        <i class="fas fa-{{ 'exclamation-circle' if category == 'danger' else 'check-circle' }}"></i> {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="POST" action="{{ url_for('login') }}">
                <div class="form-group">
                    <label for="username" class="form-label"><i class="fas fa-user"></i> Nom d'utilisateur</label>
                    <input type="text" class="form-control" id="username" name="username" required autofocus placeholder="Entrez votre username">
                </div>

                <div class="form-group">
                    <label for="password" class="form-label"><i class="fas fa-lock"></i> Mot de passe</label>
                    <input type="password" class="form-control" id="password" name="password" required placeholder="Entrez votre mot de passe">
                </div>

                <div class="form-check mb-3">
                    <input class="form-check-input" type="checkbox" id="remember" name="remember">
                    <label class="form-check-label" for="remember">Se souvenir de moi</label>
                </div>

                <button type="submit" class="btn btn-login w-100 text-white">
                    <i class="fas fa-sign-in-alt"></i> Connexion
                </button>
            </form>

            <hr style="margin: 25px 0; color: #E5E7EB;">
            <p class="text-center text-muted small mt-3" style="font-size: 12px;">
                © 2026 SupNum Share - Institut Supérieur du Numérique<br>
                <small>Plateforme sécurisée | Données protégées</small>
            </p>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return render_template_string(html)


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
    """Dashboard administrateur moderne"""
    db_session = Session()
    
    total_etudiants = db_session.query(User).filter_by(role='etudiant', actif=True).count()
    total_matieres = db_session.query(Matiere).count()
    total_admins = db_session.query(User).filter_by(role='admin', actif=True).count()
    total_utilisateurs = db_session.query(User).count()
    
    db_session.close()
    
    user = Session().query(User).filter_by(id=session['user_id']).first()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Admin - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .navbar {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
            .navbar-brand {{ cursor: pointer; transition: all 0.3s; }}
            .navbar-brand:hover {{ transform: scale(1.05); color: #3b82f6 !important; }}
            .container-fluid {{ padding: 30px 20px; }}
            .stat-card {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-left: 5px solid #3b82f6;
                transition: all 0.3s;
                animation: slideInUp 0.6s ease;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 12px 30px rgba(0,0,0,0.15);
            }}
            @keyframes slideInUp {{
                from {{ opacity: 0; transform: translateY(30px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .stat-icon {{
                font-size: 40px;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 10px;
                color: white;
            }}
            .stat-icon.blue {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }}
            .stat-icon.green {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); }}
            .stat-icon.purple {{ background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); }}
            .stat-icon.orange {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }}
            .stat-number {{ font-size: 32px; font-weight: 700; color: #1f2937; margin-top: 10px; }}
            .stat-label {{ font-size: 14px; color: #6b7280; margin-top: 5px; }}
            .action-card {{
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin-top: 30px;
            }}
            .btn-action {{
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 600;
                transition: all 0.3s;
                border: none;
                margin-right: 10px;
                margin-bottom: 10px;
            }}
            .btn-primary-grad {{
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
            }}
            .btn-primary-grad:hover {{
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
                color: white;
            }}
            .btn-success-grad {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
            }}
            .btn-success-grad:hover {{
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
                color: white;
            }}
            .dashboard-title {{
                color: white;
                font-weight: 700;
                font-size: 28px;
                margin-bottom: 10px;
            }}
            .dashboard-subtitle {{
                color: #cbd5e1;
                font-size: 14px;
            }}
            .footer {{
                text-align: center;
                color: #94a3b8;
                padding: 30px;
                border-top: 1px solid #334155;
                margin-top: 40px;
            }}
        </style>
    </head>
    <body>
        {get_navbar_html('dashboard', is_admin=True, username=user.prenom)}

        <main class="container-fluid">
            <div class="row mb-40">
                <div class="col-md-12">
                    <h1 class="dashboard-title"><i class="fas fa-tachometer-alt"></i> Dashboard Administrateur</h1>
                    <p class="dashboard-subtitle">Bienvenue {user.prenom}, gestion complète de la plateforme</p>
                </div>
            </div>

            <div class="row g-4">
                <div class="col-md-3 col-sm-6">
                    <div class="stat-card">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <div class="stat-label">Étudiants Actifs</div>
                                <div class="stat-number">{total_etudiants}</div>
                            </div>
                            <div class="stat-icon blue"><i class="fas fa-users"></i></div>
                        </div>
                    </div>
                </div>

                <div class="col-md-3 col-sm-6">
                    <div class="stat-card">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <div class="stat-label">Matières</div>
                                <div class="stat-number">{total_matieres}</div>
                            </div>
                            <div class="stat-icon green"><i class="fas fa-book"></i></div>
                        </div>
                    </div>
                </div>

                <div class="col-md-3 col-sm-6">
                    <div class="stat-card">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <div class="stat-label">Administrateurs</div>
                                <div class="stat-number">{total_admins}</div>
                            </div>
                            <div class="stat-icon purple"><i class="fas fa-user-shield"></i></div>
                        </div>
                    </div>
                </div>

                <div class="col-md-3 col-sm-6">
                    <div class="stat-card">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <div class="stat-label">Total Utilisateurs</div>
                                <div class="stat-number">{total_utilisateurs}</div>
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
                <a href="/admin/matieres" class="btn btn-action btn-success-grad">
                    <i class="fas fa-book-plus"></i> Gérer Matières
                </a>
                <a href="/admin/utilisateurs" class="btn btn-action" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white;">
                    <i class="fas fa-list"></i> Tous les Utilisateurs
                </a>
                <a href="/admin/notes" class="btn btn-action" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white;">
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
    """
    return render_template_string(html)


@app.route('/student/dashboard')
@login_required
def student_dashboard():
    """Dashboard étudiant moderne"""
    db_session = Session()
    
    user = db_session.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant if user else None
    
    if not etudiant:
        db_session.close()
        flash('Profil étudiant non trouvé.', 'danger')
        return redirect(url_for('logout'))
    
    matieres = db_session.query(Matiere).filter_by(semestre_id=etudiant.semestre_id).all()
    notes = db_session.query(Note).filter_by(etudiant_id=etudiant.id).all()
    
    db_session.close()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Étudiant - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .navbar {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
            .navbar-brand {{ cursor: pointer; transition: all 0.3s; }}
            .container-fluid {{ padding: 30px 20px; }}
            .profile-card {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin-bottom: 25px;
                border-top: 5px solid #3b82f6;
            }}
            .profile-info {{
                display: flex;
                align-items: center;
                gap: 20px;
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
            .matiere-card {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                border-left: 4px solid #3b82f6;
                transition: all 0.3s;
            }}
            .matiere-card:hover {{
                transform: translateX(5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.12);
            }}
            .matiere-name {{
                font-weight: 700;
                color: #1f2937;
                font-size: 16px;
            }}
            .matiere-code {{
                color: #6b7280;
                font-size: 12px;
                margin-top: 5px;
            }}
            .matiere-coef {{
                background: #f0f9ff;
                color: #0369a1;
                padding: 2px 8px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
            }}
            .dashboard-title {{
                color: white;
                font-weight: 700;
                font-size: 28px;
                margin-bottom: 10px;
            }}
            .dashboard-subtitle {{
                color: #cbd5e1;
                font-size: 14px;
            }}
            .footer {{
                text-align: center;
                color: #94a3b8;
                padding: 30px;
                border-top: 1px solid #334155;
                margin-top: 40px;
            }}
        </style>
    </head>
    <body>
        {get_navbar_html('student_dashboard', is_admin=False, username=user.prenom)}

        <main class="container-fluid">
            <div class="row mb-40">
                <div class="col-md-12">
                    <h1 class="dashboard-title"><i class="fas fa-home"></i> Tableau de Bord</h1>
                    <p class="dashboard-subtitle">Bienvenue {user.prenom}, consultez vos cours et résultats</p>
                </div>
            </div>

            <div class="row g-4">
                <div class="col-md-12">
                    <div class="profile-card">
                        <div class="profile-info">
                            <div class="profile-avatar">
                                <i class="fas fa-user"></i>
                            </div>
                            <div>
                                <h5 style="color: #1f2937; font-weight: 700; margin-bottom: 5px;">
                                    {user.prenom} {user.nom}
                                </h5>
                                <p style="color: #6b7280; margin-bottom: 8px;">
                                    <i class="fas fa-id-badge"></i> #{etudiant.numero_inscription}
                                </p>
                                <p style="color: #6b7280; margin-bottom: 0;">
                                    <strong>{etudiant.filiere.nom}</strong> • 
                                    <strong>{etudiant.specialite.code}</strong> • 
                                    <strong>{etudiant.semestre.nom}</strong>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col-md-8">
                    <h6 style="color: white; font-weight: 700; margin-bottom: 15px;">
                        <i class="fas fa-book"></i> Mes Matières ({len(matieres)})
                    </h6>
                    {''.join([f'''
                    <div class="matiere-card">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <div class="matiere-name">{m.nom}</div>
                                <div class="matiere-code">Code: {m.code}</div>
                            </div>
                            <span class="matiere-coef">Coef: {m.coefficient}</span>
                        </div>
                    </div>
                    ''' for m in matieres])}
                </div>

                <div class="col-md-4">
                    <h6 style="color: white; font-weight: 700; margin-bottom: 15px;">
                        <i class="fas fa-chart-line"></i> Statistiques
                    </h6>
                    <div style="background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
                        <div style="text-align: center; padding: 15px 0; border-bottom: 1px solid #e5e7eb;">
                            <div style="font-size: 32px; font-weight: 700; color: #3b82f6;">{len(notes)}</div>
                            <div style="color: #6b7280; font-size: 14px;">Notes Enregistrées</div>
                        </div>
                        <div style="text-align: center; padding: 15px 0;">
                            <div style="font-size: 28px; font-weight: 700; color: #10b981; margin-bottom: 5px;">
                                {round(sum(n.valeur for n in notes) / len(notes), 2) if notes else '—'}
                            </div>
                            <div style="color: #6b7280; font-size: 14px;">Moyenne Générale</div>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <div class="footer">
            <p>© 2026 SupNum Share - Institut Supérieur du Numérique</p>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return render_template_string(html)


# ======================== GESTION DES UTILISATEURS (ADMIN) ========================

@app.route('/admin/utilisateurs')
@admin_required
def admin_utilisateurs():
    """Liste des utilisateurs"""
    db_session = Session()
    utilisateurs = db_session.query(User).all()
    db_session.close()
    
    users_html = "".join([f"""
    <tr>
        <td class="fw-bold">{u.username}</td>
        <td>{u.email}</td>
        <td>{u.prenom} {u.nom}</td>
        <td><span class="badge bg-primary">{u.role}</span></td>
        <td><span class="badge bg-success">✓ Actif</span> if u.actif else <span class="badge bg-secondary">Inactif</span></td>
    </tr>
    """ for u in utilisateurs])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Utilisateurs - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background-color: #f8f9fa; }}
            .navbar {{ background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%); }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
            <div class="container-fluid">
                <a class="navbar-brand fw-bold" href="{{ url_for('admin_dashboard') }}">
                    <i class="fas fa-graduation-cap"></i> SupNum Share
                </a>
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('admin_utilisateurs') }}"><i class="fas fa-users"></i> Utilisateurs</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('admin_matieres') }}"><i class="fas fa-book"></i> Matières</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Déconnexion</a></li>
                </ul>
            </div>
        </nav>

        <main class="py-4">
            <div class="container-fluid">
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h1><i class="fas fa-users"></i> Gestion des Utilisateurs</h1>
                    </div>
                    <div class="col-md-6 text-end">
                        <a href="{{ url_for('admin_ajouter_utilisateur') }}" class="btn btn-primary">
                            <i class="fas fa-user-plus"></i> Ajouter Utilisateur
                        </a>
                    </div>
                </div>

                <div class="card shadow-sm">
                    <div class="card-body">
                        <table class="table table-hover">
                            <thead style="background-color: #f0f9ff;">
                                <tr>
                                    <th>Nom d'utilisateur</th>
                                    <th>Email</th>
                                    <th>Nom Complet</th>
                                    <th>Rôle</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </main>

        <footer class="bg-dark text-white text-center py-3 mt-5">
            <p class="mb-0">© 2026 SupNum Share</p>
        </footer>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return html


@app.route('/admin/utilisateur/ajouter', methods=['GET', 'POST'])
@admin_required
def admin_ajouter_utilisateur():
    """Ajouter un nouvel utilisateur"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        prenom = request.form.get('prenom')
        nom = request.form.get('nom')
        password = request.form.get('password')
        role = request.form.get('role', 'etudiant')
        
        db_session = Session()
        
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
        
        # Si étudiant, créer le profil
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
    
    db_session = Session()
    filieres = db_session.query(Filiere).all()
    specialites = db_session.query(Specialite).all()
    semestres = db_session.query(Semestre).all()
    db_session.close()
    
    filieres_html = "".join([f'<option value="{f.id}">{f.nom}</option>' for f in filieres])
    specialites_html = "".join([f'<option value="{s.id}">{s.nom}</option>' for s in specialites])
    semestres_html = "".join([f'<option value="{s.id}">{s.nom}</option>' for s in semestres])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Ajouter Utilisateur - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background-color: #f8f9fa; }}
            .navbar {{ background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%); }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
            <div class="container-fluid">
                <a class="navbar-brand fw-bold" href="{{ url_for('admin_dashboard') }}">
                    <i class="fas fa-graduation-cap"></i> SupNum Share
                </a>
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Déconnexion</a></li>
                </ul>
            </div>
        </nav>

        <main class="py-4">
            <div class="container" style="max-width: 500px;">
                <h1 class="mb-4"><i class="fas fa-user-plus"></i> Ajouter Utilisateur</h1>

                <div class="card shadow-sm">
                    <div class="card-body">
                        <form method="POST">
                            <div class="mb-3">
                                <label for="username" class="form-label">Nom d'utilisateur</label>
                                <input type="text" class="form-control" id="username" name="username" required>
                            </div>

                            <div class="mb-3">
                                <label for="email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" name="email" required>
                            </div>

                            <div class="mb-3">
                                <label for="prenom" class="form-label">Prénom</label>
                                <input type="text" class="form-control" id="prenom" name="prenom" required>
                            </div>

                            <div class="mb-3">
                                <label for="nom" class="form-label">Nom</label>
                                <input type="text" class="form-control" id="nom" name="nom" required>
                            </div>

                            <div class="mb-3">
                                <label for="password" class="form-label">Mot de passe</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>

                            <div class="mb-3">
                                <label for="role" class="form-label">Rôle</label>
                                <select class="form-control" id="role" name="role" required onchange="toggleStudentFields()">
                                    <option value="etudiant">Étudiant</option>
                                    <option value="admin">Administrateur</option>
                                </select>
                            </div>

                            <div id="studentFields">
                                <div class="mb-3">
                                    <label for="filiere_id" class="form-label">Filière</label>
                                    <select class="form-control" id="filiere_id" name="filiere_id">
                                        {filieres_html}
                                    </select>
                                </div>

                                <div class="mb-3">
                                    <label for="specialite_id" class="form-label">Spécialité</label>
                                    <select class="form-control" id="specialite_id" name="specialite_id">
                                        {specialites_html}
                                    </select>
                                </div>

                                <div class="mb-3">
                                    <label for="semestre_id" class="form-label">Semestre</label>
                                    <select class="form-control" id="semestre_id" name="semestre_id">
                                        {semestres_html}
                                    </select>
                                </div>

                                <div class="mb-3">
                                    <label for="numero_inscription" class="form-label">Numéro d'inscription</label>
                                    <input type="text" class="form-control" id="numero_inscription" name="numero_inscription">
                                </div>
                            </div>

                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-save"></i> Créer Utilisateur
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </main>

        <script>
            function toggleStudentFields() {{
                const role = document.getElementById('role').value;
                document.getElementById('studentFields').style.display = role === 'etudiant' ? 'block' : 'none';
            }}
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return html


@app.route('/admin/matieres')
@admin_required
def admin_matieres():
    """Liste des matières"""
    db_session = Session()
    matieres = db_session.query(Matiere).all()
    db_session.close()
    
    matieres_html = "".join([f"""
    <tr>
        <td class="fw-bold">{m.nom}</td>
        <td><span class="badge bg-light text-dark">{m.code}</span></td>
        <td>{m.semestre.nom}</td>
        <td>{m.coefficient}</td>
        <td>{m.seuil_validation}</td>
    </tr>
    """ for m in matieres])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Matières - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background-color: #f8f9fa; }}
            .navbar {{ background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%); }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
            <div class="container-fluid">
                <a class="navbar-brand fw-bold" href="{{ url_for('admin_dashboard') }}">
                    <i class="fas fa-graduation-cap"></i> SupNum Share
                </a>
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('admin_matieres') }}"><i class="fas fa-book"></i> Matières</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Déconnexion</a></li>
                </ul>
            </div>
        </nav>

        <main class="py-4">
            <div class="container-fluid">
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h1><i class="fas fa-book"></i> Gestion des Matières</h1>
                    </div>
                    <div class="col-md-6 text-end">
                        <a href="{{ url_for('admin_ajouter_matiere') }}" class="btn btn-success">
                            <i class="fas fa-plus"></i> Ajouter Matière
                        </a>
                    </div>
                </div>

                <div class="card shadow-sm">
                    <div class="card-body">
                        <table class="table table-hover">
                            <thead style="background-color: #f0f9ff;">
                                <tr>
                                    <th>Matière</th>
                                    <th>Code</th>
                                    <th>Semestre</th>
                                    <th>Coefficient</th>
                                    <th>Seuil</th>
                                </tr>
                            </thead>
                            <tbody>
                                {matieres_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </main>

        <footer class="bg-dark text-white text-center py-3 mt-5">
            <p class="mb-0">© 2026 SupNum Share</p>
        </footer>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return html


@app.route('/admin/matiere/ajouter', methods=['GET', 'POST'])
@admin_required
def admin_ajouter_matiere():
    """Ajouter une nouvelle matière"""
    if request.method == 'POST':
        code = request.form.get('code')
        nom = request.form.get('nom')
        coefficient = float(request.form.get('coefficient', 1.0))
        semestre_id = request.form.get('semestre_id')
        filiere_id = request.form.get('filiere_id')
        specialite_id = request.form.get('specialite_id')
        seuil_validation = float(request.form.get('seuil_validation', 10.0))
        
        db_session = Session()
        matiere = Matiere(
            code=code,
            nom=nom,
            coefficient=coefficient,
            semestre_id=semestre_id,
            filiere_id=filiere_id,
            specialite_id=specialite_id,
            seuil_validation=seuil_validation
        )
        db_session.add(matiere)
        db_session.commit()
        db_session.close()
        
        flash('Matière ajoutée avec succès.', 'success')
        return redirect(url_for('admin_matieres'))
    
    db_session = Session()
    semestres = db_session.query(Semestre).all()
    filieres = db_session.query(Filiere).all()
    specialites = db_session.query(Specialite).all()
    db_session.close()
    
    semestres_html = "".join([f'<option value="{s.id}">{s.nom}</option>' for s in semestres])
    filieres_html = "".join([f'<option value="{f.id}">{f.nom}</option>' for f in filieres])
    specialites_html = "".join([f'<option value="{s.id}">{s.nom}</option>' for s in specialites])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Ajouter Matière - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background-color: #f8f9fa; }}
            .navbar {{ background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%); }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
            <div class="container-fluid">
                <a class="navbar-brand fw-bold" href="{{ url_for('admin_dashboard') }}">
                    <i class="fas fa-graduation-cap"></i> SupNum Share
                </a>
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Déconnexion</a></li>
                </ul>
            </div>
        </nav>

        <main class="py-4">
            <div class="container" style="max-width: 600px;">
                <h1 class="mb-4"><i class="fas fa-plus"></i> Ajouter Matière</h1>

                <div class="card shadow-sm">
                    <div class="card-body">
                        <form method="POST">
                            <div class="mb-3">
                                <label for="code" class="form-label">Code Matière</label>
                                <input type="text" class="form-control" id="code" name="code" required placeholder="Ex: INFO101">
                            </div>

                            <div class="mb-3">
                                <label for="nom" class="form-label">Nom Matière</label>
                                <input type="text" class="form-control" id="nom" name="nom" required placeholder="Ex: Programmation Python">
                            </div>

                            <div class="mb-3">
                                <label for="coefficient" class="form-label">Coefficient</label>
                                <input type="number" class="form-control" id="coefficient" name="coefficient" step="0.5" value="1.0" required>
                            </div>

                            <div class="mb-3">
                                <label for="semestre_id" class="form-label">Semestre</label>
                                <select class="form-control" id="semestre_id" name="semestre_id" required>
                                    {semestres_html}
                                </select>
                            </div>

                            <div class="mb-3">
                                <label for="filiere_id" class="form-label">Filière</label>
                                <select class="form-control" id="filiere_id" name="filiere_id" required>
                                    {filieres_html}
                                </select>
                            </div>

                            <div class="mb-3">
                                <label for="specialite_id" class="form-label">Spécialité</label>
                                <select class="form-control" id="specialite_id" name="specialite_id" required>
                                    {specialites_html}
                                </select>
                            </div>

                            <div class="mb-3">
                                <label for="seuil_validation" class="form-label">Seuil de Validation</label>
                                <input type="number" class="form-control" id="seuil_validation" name="seuil_validation" step="0.5" value="10.0" required>
                            </div>

                            <button type="submit" class="btn btn-success w-100">
                                <i class="fas fa-save"></i> Créer Matière
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </main>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return html


@app.route('/admin/notes')
@admin_required
def admin_notes():
    """Gestion des notes"""
    db_session = Session()
    notes = db_session.query(Note).all()
    db_session.close()
    
    return f"<h1>Notes: {len(notes)}</h1>"


@app.route('/student/resultats')
@login_required
def student_resultats():
    """Résultats académiques de l'étudiant"""
    db_session = Session()
    
    user = db_session.query(User).filter_by(id=session['user_id']).first()
    etudiant = user.etudiant if user else None
    
    if not etudiant:
        db_session.close()
        return redirect(url_for('logout'))
    
    notes = db_session.query(Note).filter_by(etudiant_id=etudiant.id).all()
    
    # Calculer les moyennes par matière
    moyennes_matieres = {}
    for note in notes:
        if note.matiere_id not in moyennes_matieres:
            moyennes_matieres[note.matiere_id] = []
        moyennes_matieres[note.matiere_id].append(note.valeur)
    
    db_session.close()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Résultats - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .navbar {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
            .container-fluid {{ padding: 30px 20px; }}
            .dashboard-title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 10px; }}
            .dashboard-subtitle {{ color: #cbd5e1; font-size: 14px; }}
            .note-card {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-left: 4px solid #3b82f6;
            }}
            .note-info h6 {{ color: #1f2937; font-weight: 700; margin-bottom: 5px; }}
            .note-info p {{ color: #6b7280; font-size: 13px; margin-bottom: 0; }}
            .note-value {{
                font-size: 28px;
                font-weight: 700;
                color: #10b981;
                text-align: center;
            }}
            .note-status {{
                font-size: 12px;
                font-weight: 600;
                padding: 4px 12px;
                border-radius: 20px;
                text-transform: uppercase;
            }}
            .status-validee {{ background: #d1fae5; color: #065f46; }}
            .status-rattrapage {{ background: #fef3c7; color: #92400e; }}
            .status-non-validee {{ background: #fee2e2; color: #991b1b; }}
            .footer {{ text-align: center; color: #94a3b8; padding: 30px; border-top: 1px solid #334155; margin-top: 40px; }}
        </style>
    </head>
    <body>
        {get_navbar_html('resultats', is_admin=False, username=user.prenom)}

        <main class="container-fluid">
            <div class="row mb-40">
                <div class="col-md-12">
                    <h1 class="dashboard-title"><i class="fas fa-award"></i> Mes Résultats</h1>
                    <p class="dashboard-subtitle">Consultez vos notes et résultats académiques</p>
                </div>
            </div>

            <div class="row">
                <div class="col-md-12">
                    {''.join([f'''
                    <div class="note-card">
                        <div class="note-info">
                            <h6>{n.matiere.nom}</h6>
                            <p><i class="fas fa-calendar"></i> {n.devoir.date if n.devoir else "—"} | Code: {n.matiere.code}</p>
                        </div>
                        <div style="text-align: center;">
                            <div class="note-value">{n.valeur}</div>
                            <div class="note-status {'status-validee' if n.valeur >= 10 else 'status-non-validee'}">
                                {'✓ Validée' if n.valeur >= 10 else '✗ Non validée'}
                            </div>
                        </div>
                    </div>
                    ''' for n in notes])}
                    
                    {'<p style="color: #cbd5e1; text-align: center; padding: 40px;">Aucune note enregistrée pour le moment.</p>' if not notes else ''}
                </div>
            </div>
        </main>

        <div class="footer">
            <p>© 2026 SupNum Share - Institut Supérieur du Numérique</p>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/documents')
@login_required
def documents_list():
    """Liste des documents partagés"""
    db_session = Session()
    # Placeholder pour la liste des documents
    db_session.close()
    
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Documents - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .navbar {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
            .container-fluid {{ padding: 30px 20px; }}
            .dashboard-title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 10px; }}
            .empty-state {{ text-align: center; padding: 80px 20px; color: #cbd5e1; }}
            .empty-state i {{ font-size: 80px; color: #475569; margin-bottom: 20px; opacity: 0.5; }}
            .footer {{ text-align: center; color: #94a3b8; padding: 30px; border-top: 1px solid #334155; margin-top: 40px; }}
        </style>
    </head>
    <body>
        {get_navbar_html('documents', is_admin=False, username=session.get('username', ''))}
        
        <main class="container-fluid">
            <h1 class="dashboard-title"><i class="fas fa-file"></i> Documents</h1>
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h5>Aucun document disponible</h5>
                <p>Les documents partagés par les administrateurs apparaîtront ici.</p>
            </div>
        </main>

        <div class="footer">
            <p>© 2026 SupNum Share</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """


@app.route('/profile')
@login_required
def profile():
    """Page de profil utilisateur"""
    user = Session().query(User).filter_by(id=session['user_id']).first()
    
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Profil - SupNum Share</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .navbar {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
            .container {{ padding: 30px 20px; }}
            .profile-header {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .profile-card {{ background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .profile-field {{ margin-bottom: 20px; }}
            .profile-field label {{ color: #6b7280; font-weight: 600; font-size: 13px; margin-bottom: 5px; display: block; }}
            .profile-field p {{ color: #1f2937; font-size: 15px; margin-bottom: 0; }}
            .footer {{ text-align: center; color: #94a3b8; padding: 30px; border-top: 1px solid #334155; margin-top: 40px; }}
        </style>
    </head>
    <body>
        {get_navbar_html('profile', is_admin=user.is_admin() if user else False, username=user.prenom if user else '')}
        
        <div class="container" style="max-width: 600px;">
            <h1 class="profile-header"><i class="fas fa-cog"></i> Profil Utilisateur</h1>
            
            <div class="profile-card">
                <div class="profile-field">
                    <label>Nom d'utilisateur</label>
                    <p>{user.username}</p>
                </div>
                
                <div class="profile-field">
                    <label>Prénom</label>
                    <p>{user.prenom}</p>
                </div>
                
                <div class="profile-field">
                    <label>Nom</label>
                    <p>{user.nom}</p>
                </div>
                
                <div class="profile-field">
                    <label>Email</label>
                    <p>{user.email}</p>
                </div>
                
                <div class="profile-field">
                    <label>Rôle</label>
                    <p><span class="badge bg-primary">{user.role.capitalize()}</span></p>
                </div>
                
                <hr>
                
                <a href="/" class="btn btn-primary" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none;">
                    <i class="fas fa-arrow-left"></i> Retour au Dashboard
                </a>
            </div>
        </div>

        <div class="footer">
            <p>© 2026 SupNum Share</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """


# ======================== INITIALISER LA BASE DE DONNÉES ========================

def init_db():
    """Initialiser la base de données avec des données par défaut"""
    db_session = Session()
    
    # Vérifier si les données existent déjà
    if db_session.query(Filiere).count() > 0:
        print("✓ Base de données déjà initialisée")
        db_session.close()
        return
    
    print("🔧 Initialisation de la base de données...")
    
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
    
    # Créer les matières
    matieres = [
        Matiere(code='INFO101', nom='Programmation Python', coefficient=2.0, semestre_id=1, filiere_id=1, specialite_id=1),
        Matiere(code='INFO102', nom='Algorithmes et Structures de Données', coefficient=2.0, semestre_id=1, filiere_id=1, specialite_id=1),
        Matiere(code='MATH101', nom='Mathématiques Discrètes', coefficient=1.5, semestre_id=1, filiere_id=1, specialite_id=1),
        Matiere(code='WEB101', nom='Développement Web Frontend', coefficient=2.0, semestre_id=1, filiere_id=1, specialite_id=2),
        Matiere(code='NET101', nom='Introduction aux Réseaux', coefficient=1.5, semestre_id=1, filiere_id=1, specialite_id=3),
    ]
    db_session.add_all(matieres)
    db_session.commit()
    
    # Créer un utilisateur admin
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
    
    # Créer un utilisateur étudiant
    student_user = User(
        username='eddy',
        email='eddy@supnum.mr',
        prenom='Eddy',
        nom='Martin',
        role='etudiant',
        actif=True
    )
    student_user.set_password('eddy123')
    db_session.add(student_user)
    db_session.commit()
    
    # Créer le profil étudiant
    etudiant = Etudiant(
        user_id=student_user.id,
        filiere_id=1,
        specialite_id=1,
        semestre_id=1,
        numero_inscription='2026-001'
    )
    db_session.add(etudiant)
    db_session.commit()
    
    # Créer des devoirs
    devoirs = [
        Devoir(nom='TP Python 1', description='Premiers pas en Python', date=date(2026, 2, 15), type_examen='TP', session='Normale', coefficient=1.0, matiere_id=1),
        Devoir(nom='Projet Algorithmes', description='Implémentez un algoritme de tri', date=date(2026, 2, 28), type_examen='Projet', session='Normale', coefficient=2.0, matiere_id=2),
        Devoir(nom='Examen Mathématiques', description='Examen de mathématiques', date=date(2026, 3, 15), type_examen='Écrit', session='Normale', coefficient=1.5, matiere_id=3),
    ]
    db_session.add_all(devoirs)
    db_session.commit()
    
    # Créer des notes
    notes = [
        Note(valeur=15.5, etudiant_id=1, matiere_id=1, devoir_id=1),
        Note(valeur=12.0, etudiant_id=1, matiere_id=2, devoir_id=2),
        Note(valeur=13.5, etudiant_id=1, matiere_id=3, devoir_id=3),
    ]
    db_session.add_all(notes)
    db_session.commit()
    
    print("✓ Base de données initialisée avec succès!")
    print("\n📝 Comptes de test créés:")
    print("   Admin: admin / admin123")
    print("   Étudiant: eddy / eddy123")
    
    db_session.close()


# ======================== PROGRAMME PRINCIPAL ========================

if __name__ == '__main__':
    init_db()
    print("\n🚀 Lancement de SupNum Share...")
    print("📍 Accessible à: http://127.0.0.1:5000\n")
    app.run(host='127.0.0.1', port=5000, debug=True)
