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

    def find_available_time_slots(user_ids, current_time, number_time_slots):
        # retrieve all appointments for the given users
        participations = Participation.query.filter(
            Participation.userId.in_(user_ids)).all()

        # create a list of busy time slots for each user
        busy_slots = {}
        for user_id in user_ids:
            busy_slots[user_id] = []

        # populate the busy slots for each user
        for participation in participations:
            for user_id in user_ids:
                # the following line checks if a user has declined a participation to an appointment. If the user was invited but
                # did neither accept nor decline, participation.confirmed will have the value 0. If it accepted, it will have the value
                # of 2. If he declined, the value will be 1
                if participation.userId == user_id and participation.confirmed != 1:
                    appointment = Appointment.query.filter_by(
                        id=participation.appointmentId).first()
                    busy_slots[user_id].append(
                        (appointment.time_start, appointment.time_end))

        # initialize the available time slots list
        available_slots = []

        # start checking time slots from the current time

        current_time = current_time.replace(microsecond=0, second=0)
        if current_time.minute > 0 and current_time.minute <= 30:
            current_time = current_time.replace(minute=30)
        elif current_time.minute > 30:
            current_time = current_time.replace(
                minute=0, hour=current_time.hour+1)
        while len(available_slots) < number_time_slots:
            # check if all users are available during the current time slot
            all_available = True
            for user_id in user_ids:
                for busy_slot in busy_slots[user_id]:
                    if current_time >= busy_slot[0] and current_time < busy_slot[1]:
                        all_available = False
                        break
                if not all_available:
                    break

            # if all users are available, add the current time slot to the list
            if all_available:
                available_slots.append(current_time)

            # increment the current time by 30 minutes
            current_time += timedelta(minutes=30)
            current_time = current_time.replace(microsecond=0, second=0)
            if current_time.minute > 0 and current_time.minute <= 30:
                current_time = current_time.replace(minute=30)
            elif current_time.minute > 30:
                current_time = current_time.replace(
                    minute=0, hour=current_time.hour+1)

        return available_slots

    def new_appointment(slot, title, current_user, idArray):

        # Create a new appointment object with the selected slot and title
        slot_str = slot.strftime("%Y-%m-%d %H:%M:%S")
        time_end = (datetime.strptime(
            slot_str, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=30))
        new_appointment = Appointment(
            time_start=slot, time_end=time_end, title=title, creatorId=current_user)

        # Add the appointment to the database
        db.session.add(new_appointment)
        db.session.commit()

        # initialise the variable
        conf = 1

        # Loop through the selected users
        for id in idArray:
            # If the selected user is the current user, set the confirmation status to 2
            if id == current_user:
                conf = 2
            else:
                conf = 0

                # Create a new participation object with the user id, appointment id and confirmation status
            new_participation2 = Participation(
                userId=id, appointmentId=new_appointment.id, confirmed=conf)

            # Add the participation to the database
            db.session.add(new_participation2)

            # Commit the changes to the database
        db.session.commit()

    userid = list(range(1, 101))
    curentTime = datetime.now()
    result = find_available_time_slots(userid, curentTime, 2880)
    random_timestamps = random.sample(result, 1000)
    print(str(random_timestamps))
    # add the appointments to the database:
    i = 0

    for slot in random_timestamps:
        title = 'title'+str(i)
        new_appointment(slot, title, random.sample(userid, 1)[0], userid,)
        i = i+1
