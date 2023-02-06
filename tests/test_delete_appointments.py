from flask import Flask, render_template, redirect, url_for, request, current_app, g, flash, session
import random
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateTimeField, DateField, HiddenField
from wtforms.validators import InputRequired, Email, Length, DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date, timedelta
from flask_mysqldb import MySQL
from mysql.connector import connect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from test_config import Config

app = Flask(__name__)
with app.app_context():
    # Configure the secret key and database URI for the Flask application
    app.config.from_object(Config)
    db = SQLAlchemy(app)

    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)  # User id
        username = db.Column(db.String(30), unique=True)  # User username
        email = db.Column(db.String(50), unique=True)  # User email
        password = db.Column(db.String(80))  # User password
        # User participation in appointments
        participation = db.relationship(
            'Participation', backref='user', lazy='dynamic')
        # User created appointments
        creation = db.relationship(
            'Appointment', backref='user', lazy='dynamic')

    # Define the Appointment model for the database

    class Appointment(db.Model):
        id = db.Column(db.Integer, primary_key=True)  # Appointment id
        # Appointment start time
        time_start = db.Column(db.DateTime, nullable=False)
        # Appointment end time
        time_end = db.Column(db.DateTime, nullable=False)
        title = db.Column(db.String)  # Appointment title
        creatorId = db.Column(db.Integer, db.ForeignKey(
            'user.id'))  # Appointment creator id

    # Define the Participation model for the database

    class Participation(db.Model):
        id = db.Column(db.Integer, primary_key=True)  # Participation id
        userId = db.Column(db.Integer, db.ForeignKey('user.id')
                           )  # User id for the participation
        appointmentId = db.Column(db.Integer, db.ForeignKey(
            'appointment.id'))  # Appointment id for the participation
        # Confirmation status of the participation
        confirmed = db.Column(db.Integer)

    def remove_appointment(appointment_id):
        # Get all participation for the appointment
        participations = Participation.query.filter_by(
            appointmentId=appointment_id).all()

        # Delete all participations for the appointment
        for participation in participations:
            db.session.delete(participation)

        # Get the appointment with the given ID
        appointment = Appointment.query.get(appointment_id)

        # Delete the appointment
        db.session.delete(appointment)

        # Commit the changes to the database
        db.session.commit()

    def remove_test(id):
        appointments = db.session.query(Appointment).join(
            Participation).filter(Participation.userId == id).all()
        for app in appointments:
            remove_appointment(str(app.id))

    remove_test(2)
