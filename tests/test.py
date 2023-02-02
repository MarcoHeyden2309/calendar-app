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

app = Flask(__name__)
with app.app_context():
    # Configure the secret key and database URI for the Flask application
    app.config['SECRET_KEY'] = 'secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://marco:@localhost/calendardb'
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

    def get_user_appointments(SelectedDate, other_user_id, current_user):
        # Calculates the time 7 days ahead from the selected date
        time_start_plus_7 = SelectedDate + timedelta(days=7)

        # Gets a list of tuples of appointment IDs and user IDs of the current user
        # The appointments are selected by joining the `Appointment` and `Participation` tables
        # The user IDs are filtered to match the `current_user.id`
        # The time of the appointment is also filtered to be within the current time and 7 days from now
        appID_usID_current_user = db.session.query(Appointment.id, Participation.userId)\
            .join(Participation)\
            .filter(Participation.userId == current_user, Appointment.time_start.between(SelectedDate, time_start_plus_7))\
            .all()

        # Gets a list of tuples of appointment IDs and user IDs of the other user
        # The appointments are selected by joining the `Appointment` and `Participation` tables
        # The user IDs are filtered to match the `other_user_id`
        # The appointments that have the same ID as the appointments of the current user are excluded
        appID_usID_other_user = db.session.query(Appointment.id, Participation.userId)\
            .join(Participation)\
            .filter(Participation.userId == other_user_id)\
            .filter(~Appointment.id.in_([x[0] for x in appID_usID_current_user]))\
            .all()

        # Merges the two lists of appointments of the current and other users
        appID_usID = appID_usID_current_user + appID_usID_other_user
        # Creates a dictionary mapping appointment ID to user ID
        appID_usID_map = dict(appID_usID)

        # Gets a list of appointments with the same IDs as in the `appID_usID` list
        # The appointments are filtered to be within the next 7 days from the selected date
        appointments = Appointment.query\
            .filter(Appointment.id.in_([x[0] for x in appID_usID]), Appointment.time_start >= SelectedDate, Appointment.time_end < time_start_plus_7)\
            .all()

        # Returns a list containing the appointments, a list of appointment IDs, and a dictionary mapping appointment ID to user ID
        return [appointments, [x[0] for x in appID_usID], appID_usID_map]

    def get_user_appointments1(SelectedDate, other_user_id, current_user):
        time_start_plus_7 = SelectedDate + timedelta(days=7)
        # get list of tuples of appointment IDs and user IDs of current user
        appID_usID_current_user = [[row.appointmentId, row.userId] for row in Participation.query.filter(
            Participation.userId == current_user).order_by(Participation.id).all()]
        # get list of tuples of appointment IDs and user IDs of other user
        appID_usID_other_user = [[row.appointmentId, row.userId] for row in Participation.query.filter(
            Participation.userId == other_user_id).order_by(Participation.id).all()]

        # keep only appointments that current user does not have
        appID_usID_other_user = [x for x in appID_usID_other_user if x[0]
                                 not in [y[0] for y in appID_usID_current_user]]

        # merge lists of appointments of current user and other user
        appID_usID_current_user.extend(appID_usID_other_user)
        appID_usID = appID_usID_current_user
        # get appointment IDs from merged list of appointments
        appointments_id = [inner_list[0] for inner_list in appID_usID]

        # create dictionary mapping appointment ID to user ID
        appID_usID_map = dict(appID_usID)

        # get appointments in the next 7 days that are in the merged list
        appointments = Appointment.query.filter(
            Appointment.id.in_(appointments_id), Appointment.time_start >= SelectedDate, Appointment.time_end < time_start_plus_7).all()
        # get participations for the appointments
        participations = Participation.query.filter(Participation.appointmentId.in_(
            appointments_id)).order_by(Participation.id).all()

        # return appointments, appointment IDs, and appointment ID to user ID mapping
        return [appointments, appointments_id, appID_usID_map]

    if set(get_user_appointments(datetime.now(), 3, 2)[1]) == set(get_user_appointments1(datetime.now(), 3, 2)[1]):
        print("success")
