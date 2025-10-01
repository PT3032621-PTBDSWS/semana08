from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'troque-esta-chave-por-uma-segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role {self.name}>"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return f"<User {self.name} - {self.role.name if self.role else 'NoRole'}>"

# Create DB and initial roles
@app.before_first_request
def setup_db():
    db.create_all()
    default_roles = ['Administrator', 'Moderator', 'User']
    for r in default_roles:
        if not Role.query.filter_by(name=r).first():
            db.session.add(Role(name=r))
    db.session.commit()

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        role_id = request.form.get('role')
        if not name:
            flash('Por favor, informe o nome do usuário.', 'warning')
            return redirect(url_for('index'))

        role = Role.query.get(role_id) if role_id else None
        new_user = User(name=name, role=role)
        db.session.add(new_user)
        db.session.commit()

        # salva o nome na sessão para usar na saudação
        session['username'] = name

        flash(f'Usuário "{name}" cadastrado com sucesso.', 'success')
        return redirect(url_for('index'))

    roles = Role.query.order_by(Role.name).all()
    users = User.query.order_by(User.id).all()
    roles_with_users = []
    for r in roles:
        users_of_role = r.users.order_by(User.id).all()
        roles_with_users.append((r.name, users_of_role))

    return render_template('index.html',
                           roles=roles,
                           users=users,
                           roles_with_users=roles_with_users,
                           username=session.get('username'))

@app.route('/roles/add', methods=['POST'])
def add_role():
    name = request.form.get('role_name', '').strip()
    if not name:
        flash('Nome da função não pode ser vazio.', 'warning')
        return redirect(url_for('index'))
    if Role.query.filter_by(name=name).first():
        flash('Função já existe.', 'warning')
        return redirect(url_for('index'))
    db.session.add(Role(name=name))
    db.session.commit()
    flash(f'Função "{name}" criada.', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
