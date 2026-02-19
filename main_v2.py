"""
SupNum Share - Plateforme Académique Moderne 2026
Version 2 - Interface Améliorée avec Communication
"""

from flask import Flask, render_template_string, redirect, url_for, session, flash, request, send_file
from functools import wraps
from datetime import date
import os
import io
from openpyxl import Workbook

from app import (
    engine, Session, Base, User, Filiere, Specialite, Semestre, 
    Matiere, Devoir, Etudiant, Note, Message, Document, UPLOAD_FOLDER
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supnum-share-secret-2026'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Base.metadata.create_all(engine)

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
    <li class="nav-item"><a class="nav-link" href="/admin/devoirs"><i class="fas fa-tasks"></i> Devoirs</a></li>
    """
    student_items = """
    <li class="nav-item"><a class="nav-link" href="/student/matieres"><i class="fas fa-book"></i> Mes Matières</a></li>
    <li class="nav-item"><a class="nav-link" href="/student/resultats"><i class="fas fa-award"></i> Mes Résultats</a></li>
    <li class="nav-item"><a class="nav-link" href="/etudiant/chat"><i class="fas fa-comments"></i> Communication</a></li>
    <li class="nav-item"><a class="nav-link" href="/etudiant/ressources"><i class="fas fa-download"></i> Ressources</a></li>
    """
    
    items = admin_items if is_admin else student_items
    
    return f"""
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
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
    """

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
        flash('Identifiants invalides', 'danger')
    
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Segoe UI', sans-serif;
            }
            .login-box {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 50px 40px;
                max-width: 420px;
                width: 100%;
            }
            .login-header i {
                font-size: 56px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
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
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .btn-login {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
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
                    <i class="fas fa-sign-in-alt"></i> Se connecter
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
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('login'))

# ========== ROUTES ADMIN ==========

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    
    # Extract data BEFORE closing session
    username = user.prenom
    etudiants = db.query(Etudiant).count()
    matieres = db.query(Matiere).count()
    admins = db.query(User).filter_by(role='admin').count()
    total = db.query(User).count()
    
    stats = {
        'etudiants': etudiants,
        'matieres': matieres,
        'admins': admins,
        'total': total
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
            }
            .stat-card:hover { transform: translateY(-5px); box-shadow: 0 12px 30px rgba(0,0,0,0.15); }
            .stat-number { font-size: 32px; font-weight: 700; color: #1f2937; }
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
            .footer { text-align: center; color: #94a3b8; padding: 30px; margin-top: 40px; }
        </style>
    </head>
    <body>
        {{ navbar }}
        <main class="container-fluid">
            <h1 class="title"><i class="fas fa-tachometer-alt"></i> Dashboard Admin</h1>
            <p class="subtitle">Gestion complète de la plateforme</p>

            <div class="row g-4">
                <div class="col-md-3">
                    <div class="stat-card">
                        <p class="stat-label">Étudiants</p>
                        <p class="stat-number">{{ stats['etudiants'] }}</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <p class="stat-label">Matières</p>
                        <p class="stat-number">{{ stats['matieres'] }}</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <p class="stat-label">Administrateurs</p>
                        <p class="stat-number">{{ stats['admins'] }}</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <p class="stat-label">Total Utilisateurs</p>
                        <p class="stat-number">{{ stats['total'] }}</p>
                    </div>
                </div>
            </div>

            <div class="action-card">
                <h5 style="color: #1f2937; font-weight: 700; margin-bottom: 20px;">Actions Rapides</h5>
                <a href="/admin/utilisateur/ajouter" class="btn btn-action" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);">
                    <i class="fas fa-user-plus"></i> Ajouter Utilisateur
                </a>
                <a href="/admin/utilisateurs" class="btn btn-action" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                    <i class="fas fa-list"></i> Gérer Utilisateurs
                </a>
                <a href="/admin/matieres" class="btn btn-action" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);">
                    <i class="fas fa-book-plus"></i> Gérer Matières
                </a>
            </div>
        </main>
        <div class="footer">
            <p>© 2026 SupNum Share</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('admin_dashboard', True, username), stats=stats)

@app.route('/admin/matieres')
@admin_required
def admin_matieres():
    db = Session()
    semestres = db.query(Semestre).order_by(Semestre.numero).all()
    semestre_data = {}
    
    for semestre in semestres:
        matieres = db.query(Matiere).filter_by(semestre_id=semestre.id).all()
        semestre_data[semestre.nom] = [(m.code, m.nom, m.coefficient, m.seuil_validation, m.id) for m in matieres]
    
    username = db.query(User).filter_by(id=session['user_id']).first().prenom
    db.close()
    
    # Générer le HTML pour chaque semestre
    matieres_html = ""
    for semestre in semestres:
        matieres_list = semestre_data[semestre.nom]
        if matieres_list:
            matieres_html += f"""
            <div class="semestre-section">
                <h5 style="color: white; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <i class="fas fa-calendar"></i> {semestre.nom} - {len(matieres_list)} matière(s)
                </h5>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead style="background-color: #f0f9ff;">
                            <tr>
                                <th>Code</th>
                                <th>Matière</th>
                                <th>Coefficient</th>
                                <th>Seuil</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            for code, nom, coeff, seuil, mid in matieres_list:
                matieres_html += f"""
                            <tr>
                                <td><span class="badge bg-light text-dark">{code}</span></td>
                                <td><strong>{nom}</strong></td>
                                <td><span class="badge bg-info">{coeff}</span></td>
                                <td>{seuil}</td>
                                <td>
                                    <a href="/admin/matiere/edit/{mid}" class="btn btn-sm btn-primary"><i class="fas fa-edit"></i></a>
                                    <a href="/admin/matiere/delete/{mid}" class="btn btn-sm btn-danger" onclick="return confirm('Supprimer?')"><i class="fas fa-trash"></i></a>
                                </td>
                            </tr>
                """
            matieres_html += """
                        </tbody>
                    </table>
                </div>
            </div>
            <div style="margin-bottom: 30px;"></div>
            """
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Gestion des Matières</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }
            .container-fluid { padding: 30px 20px; }
            .title { color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }
            .semestre-section { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 25px; }
            .table { margin-bottom: 0; }
            .btn-primary { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none; }
            .btn-danger { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); border: none; }
        </style>
    </head>
    <body>
        {{ navbar }}
        <main class="container-fluid">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                <h1 class="title"><i class="fas fa-book"></i> Gestion des Matières par Semestre</h1>
                <a href="/admin/matiere/ajouter" class="btn btn-success" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); border: none; color: white;">
                    <i class="fas fa-plus"></i> Ajouter Matière
                </a>
            </div>

            {{ matieres_html }}
        </main>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('matieres', True, username), matieres_html=matieres_html)

@app.route('/admin/utilisateurs')
@admin_required
def admin_utilisateurs():
    db = Session()
    users = db.query(User).all()
    users_data = [(u.username, u.email, u.prenom, u.nom, u.role, u.actif) for u in users]
    username = db.query(User).filter_by(id=session['user_id']).first().prenom
    db.close()
    
    users_html = ''.join([f"""
    <tr>
        <td><strong>{uname}</strong></td>
        <td>{email}</td>
        <td>{prenom} {nom}</td>
        <td><span class="badge bg-primary">{role.capitalize()}</span></td>
        <td><span class="badge {'bg-success' if actif else 'bg-secondary'}">{'Actif' if actif else 'Inactif'}</span></td>
    </tr>
    """ for uname, email, prenom, nom, role, actif in users_data])
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Gestion des Utilisateurs</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }
            .container-fluid { padding: 30px 20px; }
            .title { color: white; font-weight: 700; margin-bottom: 30px; }
            .card { background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        {{ navbar }}
        <main class="container-fluid">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                <h1 class="title"><i class="fas fa-users"></i> Gestion des Utilisateurs</h1>
                <a href="/admin/utilisateur/ajouter" class="btn btn-success" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); border: none; color: white;">
                    <i class="fas fa-user-plus"></i> Ajouter
                </a>
            </div>

            <div class="card">
                <div class="card-body">
                    <table class="table table-hover">
                        <thead style="background-color: #f0f9ff;">
                            <tr>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Nom Complet</th>
                                <th>Rôle</th>
                                <th>Statut</th>
                            </tr>
                        </thead>
                        <tbody>
                            {{ users_html }}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('utilisateurs', True, username), users_html=users_html)

# ========== ROUTES ÉTUDIANT ==========

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = db.query(Etudiant).filter_by(user_id=user.id).first()
    
    if not etudiant:
        db.close()
        flash('Profil étudiant non trouvé', 'danger')
        return redirect(url_for('index'))
    
    # Load data BEFORE closing session
    semestre_nom = etudiant.semestre.nom if etudiant.semestre else "N/A"
    filiere_nom = etudiant.filiere.nom if etudiant.filiere else "N/A"
    specialite_nom = etudiant.specialite.nom if etudiant.specialite else "N/A"
    
    matieres = db.query(Matiere).filter_by(semestre_id=etudiant.semestre_id).all()
    matieres_data = [(m.nom, m.code, m.coefficient) for m in matieres]
    
    notes = db.query(Note).filter_by(etudiant_id=etudiant.id).all()
    notes_data = [{'matiere_nom': n.matiere.nom, 'valeur': n.valeur, 'date': n.date_creation.strftime('%d/%m/%Y')} for n in notes]
    
    username = user.prenom
    db.close()
    
    matieres_html = ''.join([f"""
    <div class="matiere-card">
        <div class="matiere-header">
            <h5>{nom}</h5>
            <span class="badge bg-info">{code}</span>
        </div>
        <p class="matiere-coeff">Coefficient: <strong>{coeff}</strong></p>
    </div>
    """ for nom, code, coeff in matieres_data])
    
    notes_html = ''.join([f"""
    <tr>
        <td><strong>{n['matiere_nom']}</strong></td>
        <td>{n['valeur']}</td>
        <td>{n['date']}</td>
    </tr>
    """ for n in notes_data])
    
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Tableau de Bord Étudiant</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container-fluid {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 10px; }}
            .subtitle {{ color: #cbd5e1; margin-bottom: 30px; }}
            .info-box {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .matiere-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 15px; border-left: 5px solid #3b82f6; }}
            .matiere-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
            .matiere-header h5 {{ margin: 0; color: #1f2937; }}
            .matiere-coeff {{ color: #6b7280; font-size: 14px; margin: 0; }}
            .notes-table {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class="container-fluid">
            <h1 class="title"><i class="fas fa-user-graduate"></i> Tableau de Bord</h1>
            <p class="subtitle">{semestre_nom} • {filiere_nom} • {specialite_nom}</p>

            <div class="info-box">
                <h5>Mes Informations</h5>
                <p class="mb-0"><strong>Filière:</strong> {filiere_nom}</p>
                <p class="mb-0"><strong>Spécialité:</strong> {specialite_nom}</p>
                <p class="mb-0"><strong>Semestre:</strong> {semestre_nom}</p>
            </div>

            <h4 style="color: white; margin-top: 30px; margin-bottom: 20px;">
                <i class="fas fa-book"></i> Mes Matières
            </h4>
            {matieres_html if matieres_html else '<p style="color: #cbd5e1;">Aucune matière trouvée pour votre semestre.</p>'}

            <h4 style="color: white; margin-top: 30px; margin-bottom: 20px;">
                <i class="fas fa-chart-bar"></i> Mes Notes Récentes
            </h4>
            <div class="notes-table">
                <table class="table table-hover">
                    <thead style="background-color: #f0f9ff;">
                        <tr>
                            <th>Matière</th>
                            <th>Note</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {notes_html if notes_html else '<tr><td colspan="3" style="text-align: center; color: #6b7280;">Aucune note enregistrée</td></tr>'}
                    </tbody>
                </table>
            </div>
        </main>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('dashboard', False, username), matieres_html=matieres_html, notes_html=notes_html)

@app.route('/student/matieres')
@login_required
def student_matieres():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = db.query(Etudiant).filter_by(user_id=user.id).first()
    
    if not etudiant:
        db.close()
        return redirect(url_for('student_dashboard'))
    
    matieres = db.query(Matiere).filter_by(semestre_id=etudiant.semestre_id).all()
    matieres_data = [(m.id, m.nom, m.code, m.coefficient, m.seuil_validation) for m in matieres]
    username = user.prenom
    db.close()
    
    matieres_html = ''.join([f"""
    <tr>
        <td><strong>{nom}</strong></td>
        <td><span class="badge bg-light text-dark">{code}</span></td>
        <td><span class="badge bg-info">{coeff}</span></td>
        <td>{seuil}</td>
        <td>
            <a href="/etudiant/matiere/{mid}/ressources" class="btn btn-sm btn-primary">
                <i class="fas fa-download"></i> Ressources
            </a>
        </td>
    </tr>
    """ for mid, nom, code, coeff, seuil in matieres_data])
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Mes Matières</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }
            .container-fluid { padding: 30px 20px; }
            .title { color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }
            .card { background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        {{ navbar }}
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
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {{ matieres_html }}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('matieres', False, username), matieres_html=matieres_html)

@app.route('/student/resultats')
@login_required
def student_resultats():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = db.query(Etudiant).filter_by(user_id=user.id).first()
    
    if not etudiant:
        db.close()
        return redirect(url_for('student_dashboard'))
    
    notes = db.query(Note).filter_by(etudiant_id=etudiant.id).all()
    notes_data = [{'matiere_nom': n.matiere.nom, 'valeur': n.valeur, 'date': n.date_creation.strftime('%d/%m/%Y')} for n in notes]
    username = user.prenom
    db.close()
    
    notes_html = ''.join([f"""
    <tr>
        <td><strong>{n['matiere_nom']}</strong></td>
        <td>{n['valeur']}</td>
        <td>{n['date']}</td>
    </tr>
    """ for n in notes_data])
    
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Mes Resultats</title>
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
            <h1 class="title"><i class="fas fa-award"></i> Mes Résultats</h1>

            <div class="card">
                <div class="card-body">
                    <table class="table table-hover">
                        <thead style="background-color: #f0f9ff;">
                            <tr>
                                <th>Matière</th>
                                <th>Note</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {notes_html if notes_html else '<tr><td colspan="3" style="text-align: center;">Aucune note enregistrée</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('resultats', False, username))

@app.route('/etudiant/chat')
@login_required
def etudiant_chat():
    """Page de communication entre étudiants du même semestre"""
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = db.query(Etudiant).filter_by(user_id=user.id).first()
    
    if not etudiant:
        db.close()
        return redirect(url_for('student_dashboard'))
    
    # Get messages from same semester
    messages = db.query(Message).filter(
        Message.type_message == 'public',
        Message.semestre_id == etudiant.semestre_id
    ).order_by(Message.date_creation.desc()).limit(50).all()
    
    messages_data = []
    for m in messages:
        messages_data.append({
            'expediteur': m.expediteur.prenom,
            'contenu': m.contenu,
            'date': m.date_creation.strftime('%d/%m/%Y %H:%M'),
            'id': m.id
        })
    
    username = user.prenom
    db.close()
    
    messages_html = ''.join([f"""
    <div style="background: white; border-radius: 8px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <p style="margin: 0; color: #1f2937;"><strong>{m['expediteur']}</strong> <span style="color: #9ca3af; font-size: 12px;">{m['date']}</span></p>
        <p style="margin: 8px 0 0 0; color: #4b5563;">{m['contenu']}</p>
    </div>
    """ for m in messages_data])
    
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Communication</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container-fluid {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .chat-box {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); min-height: 400px; display: flex; flex-direction: column; }}
            .messages-area {{ flex: 1; overflow-y: auto; margin-bottom: 20px; }}
            .form-area {{ border-top: 1px solid #e5e7eb; padding-top: 20px; }}
        </style>
    </head>
    <body>
        {{{{ navbar }}}}
        <main class="container-fluid">
            <h1 class="title"><i class="fas fa-comments"></i> Communication avec le Semestre</h1>

            <div class="chat-box">
                <div class="messages-area">
                    {messages_html if messages_html else '<p style="color: #cbd5e1; text-align: center;">Aucun message pour le moment</p>'}
                </div>
                <div class="form-area">
                    <form method="POST" action="/etudiant/chat/send">
                        <div class="input-group">
                            <input type="text" class="form-control" name="contenu" placeholder="Écrivez votre message..." required>
                            <button class="btn btn-primary" type="submit" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none;">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </main>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('chat', False, username))

@app.route('/etudiant/chat/send', methods=['POST'])
@login_required
def etudiant_chat_send():
    """Envoyer un message dans le chat du semestre"""
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = db.query(Etudiant).filter_by(user_id=user.id).first()
    
    if etudiant:
        message = Message(
            contenu=request.form.get('contenu'),
            type_message='public',
            semestre_id=etudiant.semestre_id,
            expediteur_id=user.id
        )
        db.add(message)
        db.commit()
        flash('Message envoyé!', 'success')
    
    db.close()
    return redirect(url_for('etudiant_chat'))

@app.route('/etudiant/ressources')
@login_required
def etudiant_ressources():
    """Page pour télécharger les ressources et archives"""
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
    etudiant = db.query(Etudiant).filter_by(user_id=user.id).first()
    
    if not etudiant:
        db.close()
        return redirect(url_for('student_dashboard'))
    
    # Get documents for student's semester
    documents = db.query(Document).filter_by(semestre_id=etudiant.semestre_id).all()
    docs_data = [(d.id, d.titre, d.type_document, d.matiere.nom if d.matiere else 'N/A', d.date_upload.strftime('%d/%m/%Y')) for d in documents]
    
    username = user.prenom
    db.close()
    
    docs_html = ''.join([f"""
    <tr>
        <td>{titre}</td>
        <td><span class="badge bg-info">{type_doc}</span></td>
        <td>{matiere}</td>
        <td>{date}</td>
        <td>
            <a href="/ressource/download/{rid}" class="btn btn-sm btn-success" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); border: none; color: white;">
                <i class="fas fa-download"></i>
            </a>
        </td>
    </tr>
    """ for rid, titre, type_doc, matiere, date in docs_data])
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Ressources et Archives</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }
            .container-fluid { padding: 30px 20px; }
            .title { color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }
            .card { background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        {{ navbar }}
        <main class="container-fluid">
            <h1 class="title"><i class="fas fa-archive"></i> Ressources et Archives</h1>

            <div class="card">
                <div class="card-body">
                    <table class="table table-hover">
                        <thead style="background-color: #f0f9ff;">
                            <tr>
                                <th>Titre</th>
                                <th>Type</th>
                                <th>Matière</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {{ docs_html }}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('ressources', False, username), docs_html=docs_html)

@app.route('/profile')
@login_required
def profile():
    db = Session()
    user = db.query(User).filter_by(id=session['user_id']).first()
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
        <title>Mon Profil</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }}
            .container {{ padding: 30px 20px; }}
            .title {{ color: white; font-weight: 700; font-size: 28px; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
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
                    <a href="/" class="btn btn-primary" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border: none; color: white;">
                        <i class="fas fa-arrow-left"></i> Retour
                    </a>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, navbar=get_navbar('profile', False, prenom))

def init_db():
    """Initialise la base de données avec les données de départ"""
    db = Session()
    
    # Vérifier si les données existent déjà
    if db.query(User).count() > 0:
        print("✓ Base de données déjà initialisée")
        return
    
    try:
        # Créer les objets de base
        filieres = [
            Filiere(nom='L1', description='Première année'),
            Filiere(nom='L2', description='Deuxième année'),
            Filiere(nom='L3', description='Troisième année'),
        ]
        
        specialites = [
            Specialite(nom='Développement et Système Informatique', code='DSI', filiere_id=1),
            Specialite(nom='Réseaux et Sécurité Système', code='RSS', filiere_id=2),
            Specialite(nom='Conseil et Métiers du Numérique', code='CMN', filiere_id=3),
        ]
        
        semestres = [
            Semestre(nom='S1', numero=1),
            Semestre(nom='S2', numero=2),
            Semestre(nom='S3', numero=3),
            Semestre(nom='S4', numero=4),
            Semestre(nom='S5', numero=5),
            Semestre(nom='S6', numero=6),
        ]
        
        db.add_all(filieres)
        db.add_all(specialites)
        db.add_all(semestres)
        db.commit()
        
        # Créer les matières
        matieres = [
            Matiere(nom='Mathématiques', code='MAT101', coefficient=3.0, semestre_id=1, filiere_id=1, specialite_id=1),
            Matiere(nom='Programmation Python', code='INFO101', coefficient=4.0, semestre_id=1, filiere_id=1, specialite_id=1),
            Matiere(nom='Anglais', code='LAN101', coefficient=2.0, semestre_id=1, filiere_id=1, specialite_id=1),
        ]
        db.add_all(matieres)
        db.commit()
        
        # Créer les utilisateurs
        admin = User(username='admin', email='admin@supnum.mr', prenom='Admin', nom='Système', role='admin')
        admin.set_password('admin123')
        
        etudiant = User(username='eddy', email='eddy@supnum.mr', prenom='Eddy', nom='Martin', role='etudiant')
        etudiant.set_password('eddy123')
        
        db.add(admin)
        db.add(etudiant)
        db.commit()
        
        # Créer le profil étudiant
        etudiant_profile = Etudiant(
            user_id=etudiant.id,
            filiere_id=1,
            specialite_id=1,
            semestre_id=1,
            numero_inscription='E00001'
        )
        db.add(etudiant_profile)
        db.commit()
        
        print("✓ Base de données initialisée avec succès")
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de l'initialisation: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    init_db()
    print("\n🚀 http://127.0.0.1:5000\n")
    app.run(host='127.0.0.1', port=5000, debug=True)
