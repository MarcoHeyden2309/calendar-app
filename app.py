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


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = SearchForm()
    foundUsers = []
    if form.validate_on_submit():
        foundUsers = User.query.filter_by(username=form.InputString.data).all()
        if foundUsers == []:
            return render_template('index.html', form=form, foundUsers=foundUsers, noUser=True)

    return render_template('index.html', form=form, foundUsers=foundUsers)


@app.route('/user/<id>', methods=['GET', 'POST'])
@ login_required
def get_user_calender(id):
    dateform = DateSelection()

    if dateform.validate_on_submit():
        ###SelectedDate = dateform.start_date.data
        SelectedDate = datetime(
            dateform.start_date.data.year, dateform.start_date.data.month, dateform.start_date.data.day, 2, 2, 00)
        print("selected date "+str(SelectedDate))
    else:
        SelectedDate = datetime.today()
        print("selected date "+str(SelectedDate))
    weekdays = getWeekdays(SelectedDate)
    print(weekdays)
    times = get_times(datetime(2020, 1, 1, 00, 00, 00), 30)
    time_start_plus_7 = SelectedDate + timedelta(days=7)
    appointments = Appointment.query.filter(
        Appointment.creatorId == id, Appointment.time_start >= SelectedDate, Appointment.time_end < time_start_plus_7).all()
    print(appointments)

    return render_template('calendar.html', appointments=appointments, dateform=dateform, userId=id, weekdays=weekdays, times=times)


@ app.route('/appointment/<date>/<time>/<id>', methods=['GET', 'POST'])
@ login_required
def make_appointment(date, time, id):
    titleForm = AppointmentTitle()
    date_obj = datetime.strptime(date+" "+time, "%Y-%m-%d %H:%M:%S")
    print(date_obj)
    if titleForm.validate_on_submit():
        new_appointment = Appointment(time_start=date_obj, time_end=(
            date_obj+timedelta(minutes=30)), title=titleForm.title.data, creatorId=current_user.id)
        db.session.add(new_appointment)
        db.session.commit()
        new_participation1 = Participation(
            userId=current_user.id, appointmentId=new_appointment.id, confirmed=2)
        new_participation2 = Participation(
            userId=id, appointmentId=new_appointment.id, confirmed=0)
        db.session.add(new_participation1)
        db.session.add(new_participation2)
        db.session.commit()
        #flash("Votre rendez-vous a été pris avec succès! Il faut maintenant attendre la confirmation de l'autre participant.")
        return redirect('/user/'+id)
        # =datetime(year=date.year(), month=date.month(), day=date.day(), hour=time.hour(), minute=time.minute())

    return render_template('confirmation.html', titleForm=titleForm, date=date, time=time, id=id)


@ app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect('/')
            else:
                 return 'user '+ form.password.data

    return render_template('login.html', form=form)


@ app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(
            form.password.data, method='sha256')
        new_user = User(username=form.username.data,
                        email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created!</h1>'
        # return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form)


@ app.route('/logout')
@ login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)


