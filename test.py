from flask import Flask, render_template, redirect, url_for, request, current_app

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateTimeField, DateField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date, timedelta



app = Flask(__name__)
app.app_context().push()
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    participation = db.relationship(
        'Participation', backref='user', lazy='dynamic')
    participation = db.relationship(
        'Participation', backref='user', lazy='dynamic')
    creation = db.relationship(
        'Appointment', backref='user', lazy='dynamic')


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_start = db.Column(db.DateTime, nullable=False)
    time_end = db.Column(db.DateTime, nullable=False)
    title = db.Column(db.String)

    creatorId = db.Column(db.Integer, db.ForeignKey('user.id'))


class Participation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'))
    appointmentId = db.Column(db.Integer, db.ForeignKey('appointment.id'))
    confirmed = db.Column(db.Integer)

db.create_all()