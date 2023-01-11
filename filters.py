from flask import Flask, render_template, redirect, url_for, request, current_app

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateTimeField, DateField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date, timedelta
from flask_mysqldb import MySQL
from mysql.connector import connect


app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myDB.db'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://marco:@localhost/calendardb'

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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('username', validators=[
                           InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Length(max=50)])
    username = StringField('username', validators=[
                           InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=80)])
    submit = SubmitField("Submit")


class SearchForm(FlaskForm):
    InputString = StringField('Rechercher Utilisateur',
                              validators=[InputRequired()])
    submit = SubmitField("Submit")


class DateSelection(FlaskForm):
    start_date = DateField('Start Date', validators=[InputRequired()])
    submit = SubmitField("Submit")


class AppointmentTitle(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    submit = SubmitField("Submit")

class AppointmentConfirmation(FlaskForm):
    confirmation = BooleanField("Do you want to confirm the appointment?")
    submit = SubmitField("Submit")



def check_confirmation(appoId):
    result = {}
    number = 0
    for appointment in appoId:
        participations = Participation.query.filter( Participation.appointmentId == appointment, Participation.confirmed !=2).all()
        #print(str(Participation.query.filter(Participation.confirmed != 2, Participation.appointmentId == appointment.id).statement))
        if len(participations) > 0:
            result.update({appointment: False})
        else:
            result.update({appointment: True})
    
    return result






def getWeekdays(firstDay):
    weekdays = []
    for i in range(7):
        currentDay = firstDay + timedelta(days=(i))
        print(currentDay.strftime('%A'), str(currentDay))
        weekdays.append([currentDay.strftime('%A'), currentDay])
    return weekdays


def get_times(debut, intervalle):

    result = []
    addition = 1440/intervalle
    print(int(addition))
    i = 0
    for i in range(int(addition)):
        result.append(debut + timedelta(minutes=(i)*intervalle))

    return result

@ app.route('/', methods=['GET', 'POST'])
def get_app():
    SelectedDate = datetime.today()
    time_start_plus_7 = SelectedDate + timedelta(days=7)
    appointments_id = [row.appointmentId for row in Participation.query.filter(Participation.userId==3).order_by(Participation.id).all()]
    

    
    appointments = Appointment.query.filter(
        Appointment.id.in_(appointments_id)).all()
    result = []
    result1 = []
    for appo in appointments_id:
        print(str(appo))
        result.append(appo)
    for appi in appointments:
        print(str(appi))
        result1.append(appi.id)
    print(result)
    print(result1)
    print(check_confirmation(appointments_id))
    return 'test successful'


if __name__ == '__main__':
    app.run(debug=True)
    print("Successful")



