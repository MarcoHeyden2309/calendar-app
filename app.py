from flask import Flask, render_template, redirect, url_for, request, current_app, g

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateTimeField, DateField, HiddenField
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

class AppointmentForm(FlaskForm):
    date = HiddenField()
    time = HiddenField()
    userId = HiddenField()
    submit = SubmitField("Prendre rendez-vous")


class MatchingAlgorithm(FlaskForm):

    submit = SubmitField(label='Find common time slots')




def find_available_time_slots(user_ids, current_time):
    # retrieve all appointments for the given users
    participations = Participation.query.filter(Participation.userId.in_(user_ids)).all()

    # create a list of busy time slots for each user
    busy_slots = {}
    for user_id in user_ids:
        busy_slots[user_id] = []

    # populate the busy slots for each user
    for participation in participations:
        for user_id in user_ids:
            if participation.userId == user_id and participation.confirmed==1:
                appointment=Appointment.query.filter_by(id=participation.appointmentId).first()
                busy_slots[user_id].append((appointment.time_start, appointment.time_end))

    # initialize the available time slots list
    available_slots = []

    # start checking time slots from the current time
    
    current_time = current_time.replace(microsecond=0, second=0)
    if current_time.minute > 0 and current_time.minute <=30:
        current_time = current_time.replace(minute=30)
    elif current_time.minute > 30:
        current_time = current_time.replace(minute=0, hour=current_time.hour+1)
    while len(available_slots) < 5:
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
        if current_time.minute > 0 and current_time.minute <=30:
            current_time = current_time.replace(minute=30)
        elif current_time.minute > 30:
            current_time = current_time.replace(minute=0, hour=current_time.hour+1)

    return available_slots



def check_confirmation(appoId):
    result = {}
    
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
        
        weekdays.append([currentDay.strftime('%A'), currentDay])
    return weekdays


def get_times(debut, intervalle):

    result = []
    addition = 1440/intervalle
    
    i = 0
    for i in range(int(addition)):
        result.append(debut + timedelta(minutes=(i)*intervalle))

    return result

@login_manager.user_loader
def load_user(user_id):
    # Retrieve the user object from the database using the user_id
    user = User.query.get(user_id)
    return user

@app.before_request
def before_request():
    g.current_user = current_user
    #g.selected_users = []





@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None    
    form = SearchForm()
    foundUsers = []
    noUser = False
    currentuserId = current_user.id
    if form.validate_on_submit():
        foundUsers = User.query.filter_by(username=form.InputString.data).all()
        if len(foundUsers) == 0: 
            noUser = True
        else:
            noUser = False

    return render_template('index.html', form=form, foundUsers=foundUsers, noUser=noUser, currentuserId = currentuserId, name = name)


@app.route('/userorg/<id>', methods=['GET', 'POST'])
@ login_required
def get_user_calender2(id):
    dateform = DateSelection()
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None      
    if dateform.validate_on_submit():
        ###SelectedDate = dateform.start_date.data
        SelectedDate = datetime(
            dateform.start_date.data.year, dateform.start_date.data.month, dateform.start_date.data.day, 2, 2, 00)
        
    else:
        SelectedDate = datetime.today()
        
    weekdays = getWeekdays(SelectedDate)
    


    times = get_times(datetime(2020, 1, 1, 00, 00, 00), 30)
    time_start_plus_7 = SelectedDate + timedelta(days=7)
    appointments = Appointment.query.filter(
        Appointment.creatorId == id, Appointment.time_start >= SelectedDate, Appointment.time_end < time_start_plus_7).all()
    

    return render_template('dashboard2.html', appointments=appointments, dateform=dateform, userId=id, weekdays=weekdays, times=times, name = name)


@app.route('/user/<id>', methods=['GET', 'POST'])
@ login_required
def get_user_calender(id):
    print("userid:"+id)
    dateform = DateSelection()
    confirm_appoinment = AppointmentConfirmation()
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None  
    if dateform.validate_on_submit():
        ###SelectedDate = dateform.start_date.data
        SelectedDate = datetime(
            dateform.start_date.data.year, dateform.start_date.data.month, dateform.start_date.data.day, 2, 2, 00)
        
    else:
        SelectedDate = datetime.today()
        
    weekdays = getWeekdays(SelectedDate)

    current_date = datetime.now()
    current_time = datetime.now().time()
    times = get_times(datetime(2020, 1, 1, 00, 00, 00), 30)
    time_start_plus_7 = SelectedDate + timedelta(days=7)
    appointments_id = [row.appointmentId for row in Participation.query.filter(Participation.userId==current_user.id).order_by(Participation.id).all()]
    

    
    appointments = Appointment.query.filter(
        Appointment.id.in_(appointments_id), Appointment.time_start >= SelectedDate, Appointment.time_end < time_start_plus_7).all()
    
    participations = Participation.query.filter( Participation.appointmentId.in_(appointments_id)).order_by(Participation.id).all()
    for part in participations:
        print(str(part.confirmed))        
    
    confirmations = check_confirmation(appointments_id)
    print("Confirmations: "+str(confirmations))
    print("appointments: "+str(appointments))


    return render_template('dashboard_other_user.html', appointments=appointments,confirmations = confirmations, dateform=dateform, otherUserId=id, weekdays=weekdays, times=times, confirm_appoinment = confirm_appoinment, current_date=current_date, current_time=current_time, name = name)



@ app.route('/appointment/<date>/<time>/<id>', methods=['GET', 'POST'])
@ login_required
def make_appointment(date, time, id):
    titleForm = AppointmentTitle()
    date_obj = datetime.strptime(date+" "+time, "%Y-%m-%d %H:%M:%S")
    
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None  

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

    return render_template('confirmation.html', titleForm=titleForm, date=date, time=time, id=id, name = name)




@ app.route('/dashboard', methods=['GET', 'POST'])
@ login_required
def dashboard():
    dateform = DateSelection()
    confirm_appoinment = AppointmentConfirmation()
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None  
    if dateform.validate_on_submit():
        ###SelectedDate = dateform.start_date.data
        SelectedDate = datetime(
            dateform.start_date.data.year, dateform.start_date.data.month, dateform.start_date.data.day, 2, 2, 00)
        
    else:
        SelectedDate = datetime.today()
        
    weekdays = getWeekdays(SelectedDate)


    times = get_times(datetime(2020, 1, 1, 00, 00, 00), 30)
    time_start_plus_7 = SelectedDate + timedelta(days=7)
    appointments_id = [row.appointmentId for row in Participation.query.filter(Participation.userId==current_user.id).order_by(Participation.id).all()]
    

    
    appointments = Appointment.query.filter(
        Appointment.id.in_(appointments_id), Appointment.time_start >= SelectedDate, Appointment.time_end < time_start_plus_7).all()
    
    participations = Participation.query.filter( Participation.appointmentId.in_(appointments_id)).order_by(Participation.id).all()
    for part in participations:
        print(str(part.confirmed))        
    
    confirmations = check_confirmation(appointments_id)
    print("Confirmations: "+str(confirmations))
    print("appointments: "+str(appointments))


    return render_template('dashboard.html', appointments=appointments,confirmations = confirmations, dateform=dateform, userId=current_user.id, weekdays=weekdays, times=times, confirm_appoinment = confirm_appoinment, name = name)



@ app.route('/confirm/<appId>/<confirm>', methods=['GET'])
@ login_required
def confirm(appId, confirm):
    participation = Participation.query.filter(Participation.appointmentId==appId, Participation.userId==current_user.id).first()
    participation.confirmed = int(confirm)
    db.session.commit()

    return redirect('/dashboard')


@ app.route('/matching', methods=['GET', 'POST'])
@ login_required
def match():
    #slots = find_available_time_slots()
    form = SearchForm()
    
    foundUsers = []
    sameUser = False
    sameSelectedUser = False
    if not hasattr(current_app, 'selected_users'):
        current_app.selected_users = {}

    
    
    if form.validate_on_submit():
        foundUsers = User.query.filter_by(username=form.InputString.data).first()
        
        if foundUsers:
            if foundUsers.id == current_user.id:
                sameUser = True
            if current_app.selected_users.get(str(foundUsers.id)) != None:
                sameSelectedUser = True

    

  
    return render_template('matching_algorithm.html', form = form, sameUser = sameUser, foundUsers = foundUsers, sameSelectedUser = sameSelectedUser, selectedUsers = current_app.selected_users)


@ app.route('/add_selected_user/<id>/<name>', methods=['GET', 'POST'])
@ login_required
def add_selected_user(id, name):
    current_app.selected_users[int(id)] = name

    print(str(current_app.selected_users))
    return redirect('/matching')



@ app.route('/matching/asked', methods=['GET', 'POST'])
@ login_required
def ask():
    
    cureentTime = datetime.now()
    idArray = list(current_app.selected_users.keys())
    time_slots = find_available_time_slots(idArray, cureentTime)
    print(str(time_slots))
    return time_slots


@ app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None  
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                
                
                return redirect('/')
            else:
                 return 'user '+ form.password.data

    return render_template('login.html', form=form, name = name)


@ app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None  
    if form.validate_on_submit():
        hashed_password = generate_password_hash(
            form.password.data, method='sha256')
        new_user = User(username=form.username.data,
                        email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created!</h1>'
        # return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form, name = name)


@ app.route('/logout')
@ login_required
def logout():
    logout_user()
   
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)


