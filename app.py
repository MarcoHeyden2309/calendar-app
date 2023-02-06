from flask import Flask, render_template, redirect, url_for, request, current_app, g, flash, session
import random
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date, timedelta
from flask_mysqldb import MySQL
from mysql.connector import connect


app = Flask(__name__)

# Configure the secret key and database URI for the Flask application
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://marco:@localhost/calendardb'

# Initialize the database connection for the Flask application
db = SQLAlchemy(app)

# Initialize the LoginManager for the Flask application
# This code sets up the LoginManager class from the Flask-Login library as a login_manager
# object and initializes it with the Flask application "app". The "login_view" attribute is then
# set to the string 'login', which specifies the endpoint for the login page. This setup allows for
# managing user authentication in the Flask application.
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define the User model for the database


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # User id
    username = db.Column(db.String(30), unique=True)  # User username
    email = db.Column(db.String(50), unique=True)  # User email
    password = db.Column(db.String(80))  # User password
    # User participation in appointments
    participation = db.relationship(
        'Participation', backref='user', lazy='dynamic')
    # User created appointments
    creation = db.relationship('Appointment', backref='user', lazy='dynamic')

# Define the Appointment model for the database


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Appointment id
    # Appointment start time
    time_start = db.Column(db.DateTime, nullable=False)
    time_end = db.Column(db.DateTime, nullable=False)  # Appointment end time
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

# This function is used to load the user information by the user id.
# It will be used by the Flask-Login extension to retrieve the user information
# and to keep the user logged in.


@login_manager.user_loader
def load_user(user_id):
    # This line of code returns a User object corresponding to the given user id,
    # retrieved from the database.
    return User.query.get(int(user_id))

# The LoginForm class is a form for handling user login information.
# It is a subclass of FlaskForm and it defines the fields for the login form.


class LoginForm(FlaskForm):
    # This line of code defines a 'username' field, with validations:
    # - InputRequired: the field is required and cannot be left empty.
    # - Length: the length of the input must be between 4 and 15 characters.
    username = StringField('username', validators=[
                           InputRequired(), Length(min=4, max=15)])
    # This line of code defines a 'password' field, with validations:
    # - InputRequired: the field is required and cannot be left empty.
    # - Length: the length of the input must be between 8 and 80 characters.
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=80)])
    # This line of code defines a 'remember me' checkbox field.
    remember = BooleanField('remember me')
    # This line of code defines a 'Submit' button for submitting the form.
    submit = SubmitField("Submit")

# The RegisterForm class is a form for handling user registration information.
# It is a subclass of FlaskForm and it defines the fields for the registration form.


class RegisterForm(FlaskForm):
    # This line of code defines an 'email' field, with validations:
    # - InputRequired: the field is required and cannot be left empty.
    # - Length: the length of the input must be between 0 and 50 characters.
    email = StringField('email', validators=[InputRequired(), Length(max=50)])
    # This line of code defines a 'username' field, with validations:
    # - InputRequired: the field is required and cannot be left empty.
    # - Length: the length of the input must be between 4 and 15 characters.
    username = StringField('username', validators=[
                           InputRequired(), Length(min=4, max=15)])
    # This line of code defines a 'password' field, with validations:
    # - InputRequired: the field is required and cannot be left empty.
    # - Length: the length of the input must be between 8 and 80 characters.
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=80)])
    # This line of code defines a 'Submit' button for submitting the form.
    submit = SubmitField("Submit")

# SearchForm
# A form for searching for a user


class SearchForm(FlaskForm):
    # A StringField for searching user
    InputString = StringField('Rechercher Utilisateur',
                              validators=[InputRequired()])
    # A SubmitField for submitting the form
    submit = SubmitField("Submit")


# AppointmentTitle
# A form for setting the title of an appointment


class AppointmentTitle(FlaskForm):
    # A StringField for setting the title of an appointment, with InputRequired() validation
    title = StringField('Title', validators=[InputRequired()])
    # A SubmitField for submitting the form
    submit = SubmitField("Submit")

# AppointmentConfirmation
# A form for confirming an appointment


class AppointmentConfirmation(FlaskForm):
    # A BooleanField for confirming the appointment
    confirmation = BooleanField("Do you want to confirm the appointment?")
    # A SubmitField for submitting the form
    submit = SubmitField("Submit")


# this function takes as input appId, confirm, current_user
# appId is the appointment id. confirm is the the confirmation status for an appointment given by the user.
# confirm is an integer that can take the following values: 0 -> neither confirmed nor refused, 1-> refused, 2 -> confirmed
def confirm_function(appId, confirm, current_user):
    # Query the Participation table to get the relevant record
    participation = Participation.query.filter(
        Participation.appointmentId == appId, Participation.userId == current_user).first()

    # Update the confirmation status of the appointment
    participation.confirmed = int(confirm)

    # Commit the changes to the database
    db.session.commit()


# This function allows to create a new appointment. The input parameters are the following:
# slot, which is the date and time of the start of the appointment.
# title, the title of the new appointment
# current_user, which is the User.id of the user that creates the appointment
# idArray, which is an Array containing the User.id of the other users invited in the appointment
def new_appointment(slot, title, current_user, idArray):

    # Create a new appointment object with the selected slot and title
    # time end is 30minutes after time start.
    time_end = (datetime.strptime(
        slot, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=30))

    new_appointment = Appointment(
        time_start=slot, time_end=time_end, title=title, creatorId=current_user)

    # Add the appointment to the database
    db.session.add(new_appointment)
    db.session.commit()

    # initialise the variable
    conf = 1

    # Loop through the selected users
    for id in idArray:
        # If the selected user is the current user, set the confirmation status to 2, which means that the user has confirmed it.
        # This is because when a user creates a new appointment, the application implicitely assumes that he will participate in it
        if id == current_user:
            conf = 2
        else:
            conf = 0

            # Create a new participation object with the user id, appointment id and confirmation status
        new_participation2 = Participation(
            userId=id, appointmentId=new_appointment.id, confirmed=conf)

        # Add the participation to the database
        db.session.add(new_participation2)
        if idArray[0] == idArray[1]:
            break

        # Commit the changes to the database
    db.session.commit()

# This function allows to create a new user


def signup_function(username, email, password):

    # Hash password using sha256
    hashed_password = generate_password_hash(
        password, method='sha256')
    # Create new user with given username, email and password
    new_user = User(username=username,
                    email=email, password=hashed_password)
    # Add the new user to database
    db.session.add(new_user)
    db.session.commit()

# This function allows to delete an appoinment and all participations related to it


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

# This function allows to automatically find the available time slots for a selected subset of persons starting from a selected date and time.
# It takes the following inputs:
# user_ids: this is an array which includes all the users among which common time slots should be found.
# current_time: this is the starting time and date from which the common slots should be searched
# number_time_slots: how many time slots the algorithm should search
# The output is an array with all the available time slots


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


# This function will check the status of a givent appointment.
# The input is appointmnetId, which is the id of the appointment, and current_user, which is the id of the current user
# The output is a dictionary  {appointment_id : [number_of_invited_participants, number_of_confirmed_participants, confirmation_status_current_user, name_of_the_appointment_creator]}

def check_confirmation(appointmentId, current_user):
    # A dictionary to store the result of the function
    result = {}

    # Iterate over each appointment in the appointmentId argument
    for id in appointmentId:
        # Get a list of all participations for the current appointment
        participations_number = Participation.query.filter(
            Participation.appointmentId == id).all()
        # Get a list of all accepted participations for the current appointment
        participations_accepted = Participation.query.filter(
            Participation.appointmentId == id, Participation.confirmed == 2).all()
        # Get a list of all declined participations for the current appointment
        participations_declined = Participation.query.filter(
            Participation.appointmentId == id, Participation.confirmed == 1).all()
        # Get the participation status of the current user
        participation_currentuser = Participation.query.filter(
            Participation.appointmentId == id, Participation.userId == current_user).first()
        # get the name of the appointment creator
        appointment = Appointment.query.filter(id == id).first()
        creator_name = User.query.filter(
            User.id == appointment.creatorId).first()
        # Check if all participations are accepted
        if len(participations_accepted) == len(participations_number):
            # Add the appointment to the result dictionary with status 2 (all accepted)
            result.update(
                {id: [2, len(participations_number), len(participations_accepted), participation_currentuser.confirmed, creator_name.username]})
        # Check if all participations but one are declined
        elif len(participations_declined) == (len(participations_number)-1):
            # Add the appointment to the result dictionary with status 1 (all declined)
            result.update(
                {id: [1, len(participations_number), len(participations_accepted), participation_currentuser.confirmed, creator_name.username]})
        # If neither condition is met, add the appointment to the result dictionary with status 0 (not confirmed)
        else:
            result.update(
                {id: [0, len(participations_number), len(participations_accepted), participation_currentuser.confirmed, creator_name.username]})

    # Return the result dictionary
    return result

# This function will take as input a date. It will output
# an array which contains the 7 next weekdays from the input date: [MOnday, Tuesday,...]


def getWeekdays(firstDay):
    weekdays = []
    for i in range(7):
        currentDay = firstDay + timedelta(days=(i))

        weekdays.append([currentDay.strftime('%A'), currentDay])
    return weekdays

# This function will output an array with the divided day.
# the output will be like this: [00:00, 00:30, 01:30, 02:00,...]
# THe intervall and start_time are the inputs


def get_times(start_time, intervalle):

    result = []
    addition = 1440/intervalle

    i = 0
    for i in range(int(addition)):
        result.append(start_time + timedelta(minutes=(i)*intervalle))

    return result

# This function will retriveve all user appointments to show them on the Dashboard page
# It takes the following input:
# SelectedDate, which is the date from which the appointments should be retrieved
# other_user_id, which is the USer.id of the other user. This function is optimised for visualising in
# one place the appointments of two users who want to set an appointment together.
# So the appointments of the other user have to be queried as well


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
        .filter(Appointment.time_start.between(SelectedDate, time_start_plus_7))\
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


@login_manager.user_loader
def load_user(user_id):
    # Retrieve the user object from the database using the user_id
    user = User.query.get(user_id)
    return user

# THis is the start route, which direcly redirects to the dashboard


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return redirect('/dashboard')


# Route definition for creating a new appointment
# Supports GET and POST requests
@app.route('/appointment/<date>/<time>/<other_user_id>', methods=['GET', 'POST'])
# Login is required to access this page
@login_required
def make_appointment(date, time, other_user_id):
    # Initialize the AppointmentTitle form
    titleForm = AppointmentTitle()
    # Convert the date string to a datetime object
    date_obj = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M:%S")
    date_obj = date_obj.strftime("%Y-%m-%d %H:%M:%S")
    # Get the name of the current user
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None

    # If the appointment title form has been submitted and is valid
    if titleForm.validate_on_submit():
        userArray = [current_user.id, int(other_user_id)]
        new_appointment(date_obj, titleForm.title.data,
                        current_user.id, userArray)
        print(str(userArray))
        # Redirect to the dashboard
        return redirect('/dashboard')

    # Render the confirmation page, passing in necessary information
    return render_template('confirmation.html', titleForm=titleForm, date=date, time=time, id=other_user_id, name=name)


# Route for the dashboard view of a logged in user
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required  # Ensures the user must be logged in to access this view
def dashboard():

    # Identifying the id of the other user to display appointments with
    otherUserId = 'otherUserId_' + str(current_user.id)

    # Store the id of the other user in the current app context
    setattr(current_app, otherUserId, current_user.id)

    # Initialize the date selection form

    # Initialize the appointment confirmation form
    confirm_appoinment = AppointmentConfirmation()

    # List to store found users matching the search criteria
    foundUsers = [current_user]

    # Check if the user is authenticated and get their username
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None

     # If the selected date is not yet stored in the current app context, set it to today's date
    selected_date = 'selected_date_'+name
    if not hasattr(current_app, selected_date):
        setattr(current_app, selected_date, datetime.now())
    # Check the request method and process the form data accordingly

    if request.method == 'POST':
        if request.form.get('searchUser_button'):
            # Search for the user with the entered username
            otherName = request.form['username']
            foundUsers = User.query.filter_by(username=otherName).all()
            # If a user is found, store their id in the current app context
            if foundUsers != []:
                setattr(current_app, otherUserId, foundUsers[0].id)

        elif request.form.get('searchDate_button'):
            # Store the selected date in the current app context
            date_string = request.form['date']
            date_object = datetime.strptime(date_string, '%Y-%m-%d')

            setattr(current_app, selected_date,
                    date_object.replace(hour=00, minute=00))
        elif request.form.get('declineApp_button'):
            appointment_id = request.form['declineApp']
            confirm_function(appointment_id, 1, current_user.id)
            print('decline '+appointment_id)
            print('ok')

        elif request.form.get('confirmApp_button'):
            appointment_id = request.form['confirmApp']
            confirm_function(appointment_id, 2, current_user.id)
            print('accept '+appointment_id)
            print('ok')

        elif request.form.get('rmApp_button'):
            appointment_id = request.form['remove_appointment']
            remove_appointment(appointment_id)
            print('remove '+appointment_id)
            print('ok')

    # Get the days of the week for the selected date
    weekdays = getWeekdays(getattr(current_app, selected_date))

    # Get the list of times with a 30 minute interval
    times = get_times(datetime(2020, 1, 1, 00, 00, 00), 30)

    # Get the appointments and confirmations for the selected user and date
    get_appointments = get_user_appointments(getattr(current_app, selected_date),
                                             int(getattr(current_app, otherUserId)), current_user.id)
    appointments = get_appointments[0]
    appointments_id = get_appointments[1]
    appID_usID_map = get_appointments[2]
    current_date = datetime.now()

    # Get the current time
    current_time = datetime.now().time()

    # Get the confirmation status for the appointments
    confirmations = check_confirmation(appointments_id, current_user.id)
    print('confirmations '+str(confirmations))
    # Return the rendered dashboard template with the required variables
    return render_template('dashboard.html', appointments=appointments, confirmations=confirmations, userId=current_user.id, weekdays=weekdays, times=times, confirm_appoinment=confirm_appoinment, name=name, appID_usID_map=appID_usID_map, current_date=current_date, current_time=current_time, otherUserId=getattr(current_app, otherUserId), foundUsers=foundUsers, SelectedDate=getattr(current_app, selected_date))


# This function is called when the '/matching' endpoint is hit with a GET or POST request.
# It requires the user to be logged in before it can be accessed, as it uses the current_user object from Flask-Login.
@app.route('/matching', methods=['GET', 'POST'])
@login_required
def match():
    # If the user is logged in, sets the 'name' variable to the username of the current user.
    # If the user is not logged in, sets the 'name' variable to None.
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None

    # Initializes an empty list 'foundUsers' to store the results of the user search.
    foundUsers = []
    # Initializes a flag 'noUserFound' to indicate whether a user was found during a search.
    noUserFound = True
    # Initializes a flag 'sameUser' to indicate whether the searched user is the same as the
    # currently logged in user.
    sameUser = False
    # Initializes a flag 'sameSelectedUser' to indicate whether the searched user is already in the list of selected users.
    sameSelectedUser = False
    # Creates a dynamic attribute on the current Flask application with a unique name for the current user,
    # storing the list of selected users for that user.
    selected_users = 'selected_users_'+name
    if not hasattr(current_app, selected_users):
        setattr(current_app, selected_users, {
                current_user.id: current_user.username})

    # If the request method is POST, checks which form button was pressed and takes appropriate action.
    if request.method == 'POST':
        # If the 'rmUser' button was pressed, removes the specified user from the list of selected users.
        if request.form.get('rmUser_button'):
            rmUser = request.form['rmUser']
            if rmUser != current_user.username:
                for key, value in getattr(current_app, selected_users, {}).items():
                    if value == rmUser:

                        # Deletes the key from the dictionary stored in the current_app context
                        del getattr(current_app, selected_users, {})[key]
                        break
# If the 'addUser_button' form value is present, attempt to find a user by the specified username
        elif request.form.get('addUser_button'):
            foundUsers = User.query.filter_by(
                username=request.form['username']).first()
            # If a user is found, set the 'noUserFound' flag to True and check if the found user is the same as the current user
            if foundUsers:
                noUserFound = True

                if foundUsers.id == current_user.id:
                    sameUser = True
                # Check if the found user is already in the selected users dictionary
                if getattr(current_app, selected_users, {}).get(str(foundUsers.id)) != None:
                    sameSelectedUser = True
            # If no user is found, set the 'noUserFound' flag to False
            else:
                noUserFound = False

        elif request.form.get('remove_all_selected_users_button'):
            if hasattr(current_app, selected_users):
                delattr(current_app, selected_users)
            if not hasattr(current_app, selected_users):
                setattr(current_app, selected_users, {
                    current_user.id: current_user.username})

    # Render the 'matching_algorithm.html' template, passing in the form, user information, and selected users dictionary
    return render_template('matching_algorithm.html', sameUser=sameUser, foundUsers=foundUsers, sameSelectedUser=sameSelectedUser, selectedUsers=getattr(current_app, selected_users, {}), name=name, noUserFound=noUserFound)


# Define the route for adding selected users
@app.route('/add_selected_user/<id>/<name>', methods=['GET', 'POST'])
# Require the user to be logged in to access this route
@login_required
def add_selected_user(id, name):
    # Define the key for the selected users based on the current user's username
    selected_users = 'selected_users_' + current_user.username
    # Add the selected user's ID and name to the dictionary in the current app's context
    getattr(current_app, selected_users, {})[int(id)] = name

    # Print the dictionary of selected users for debugging purposes
    print(str(getattr(current_app, selected_users, {})))
    # Redirect the user back to the matching page
    return redirect('/matching')


@ app.route('/matching/asked', methods=['GET', 'POST'])
@ login_required
def select_slot():
    # Check if user is authenticated and set the name to the username of the current user
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None

    # Get the current time

    # Create a key for the selected users of the current user
    selected_users = 'selected_users_'+current_user.username

    # Get the list of keys of the selected users of the current user
    idArray = list(getattr(current_app, selected_users, {}).keys())
    selected_date_time = datetime.now()
    time_slots = find_available_time_slots(idArray, selected_date_time, 5)

    # If a POST request is made
    if request.method == 'POST':
        if request.form.get('select_date'):
            selected_date_time = datetime.strptime(
                request.form['datetime'], "%Y-%m-%dT%H:%M")
            print('test: '+str(selected_date_time))
            # Get the available time slots of the selected users
            time_slots = find_available_time_slots(
                idArray, selected_date_time, 5)

        # Get the title of the appointment
        elif request.form.get('slot_button'):
            title = request.form['title']

            # Get the selected slot for the appointment
            slot = request.form['slot']

            new_appointment(slot, title, current_user.id, idArray)

            # Print the type of the slot
            print("slot-title "+str(type(slot)))

            # Display a flash message to indicate that the appointment has been created
            flash("You have successfully created an appointment")

            # remove the selected users

            if hasattr(current_app, selected_users):
                delattr(current_app, selected_users)

            if not hasattr(current_app, selected_users):
                setattr(current_app, selected_users, {
                    current_user.id: current_user.username})

        # Redirect to the dashboard

            return redirect('/dashboard')

    # Render the select_common_slot.html template with the found time slots and the name of the current user
    return render_template('select_common_slot.html', foundSlots=time_slots, name=name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Boolean flag to determine if the previous login attempt was unsuccessful
    failed_login = False
    # Create a LoginForm instance
    form = LoginForm()
    # Check if user is already logged in and assign their username to a variable if so, otherwise set it to None
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None

    # If the form has been submitted and passes validation
    if form.validate_on_submit():
        # Query the database for a user with the entered username
        user = User.query.filter_by(username=form.username.data).first()
        # If the user exists in the database
        if user:
            # Check if the entered password matches the hashed password in the database
            if check_password_hash(user.password, form.password.data):
                # Log in the user
                login_user(user, remember=form.remember.data)
                # Redirect the user to the dashboard
                return redirect('/dashboard')
            else:
                # If the password does not match, set the failed_login flag to True
                failed_login = True
        else:
            # if the username doesn't exist in the database, set the failed_login flag to True
            failed_login = True

    # Render the login template with the form and username, regardless of whether the form was submitted or not
    return render_template('login.html', form=form, name=name, failed_login=failed_login)


# User sign up route
@ app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Form for sign up
    form = RegisterForm()
    # Get username from current user
    if current_user.is_authenticated:
        name = current_user.username
    else:
        name = None
    # Validate sign up form on submit
    if form.validate_on_submit():
        signup_function(form.username.data,
                        form.email.data, form.password.data)

        flash("You have successfully signed up! Please login to continue.")
        # Redirect to login page
        return redirect('/login')

    # Render sign up template with form and username
    return render_template('signup.html', form=form, name=name)


@app.route('/logout')
@login_required  # Ensure the user is authenticated to access this page
def logout():
    # Get the current app's selected_users attribute by appending the current user's username
    selected_users = 'selected_users_' + current_user.username

    # Check if the current app has the selected_users attribute, and if so, delete it
    if hasattr(current_app, selected_users):
        delattr(current_app, selected_users)

    # Log out the current user
    logout_user()

    # Redirect the user back to the login page
    return redirect('/login')


# Main function to run the app
if __name__ == '__main__':
    app.run(debug=True)
