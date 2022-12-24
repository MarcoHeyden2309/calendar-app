from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db'
app.config['SECRET_KEY'] = 'test'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user


@app.route('/')
def index():
    user = User.query.filter_by(username='Marco').first()
    login_user(user)
    return 'you are now logged in '+str(user.id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return 'you are now logged out'


@app.route('/home')
@login_required
def home():
    return 'the current user is ' + current_user.username


if __name__ == '__main__':
    app.run(debug=True)
