# calendar-app

In order to run this app on your machine, you need to do the following:

1. import the used libraries that are not yet on your computer
2. setup the database connection in the app.py file on line 19:
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://marco:@localhost/calendardb'
   modify this line according to the instance of your local database.
