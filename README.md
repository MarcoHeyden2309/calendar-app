# calendar-app

In order to run this app on your machine, you need to do the following:

1. import the used libraries that are not yet on your computer
2. setup the database connection in the app.py file on line 19:
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://marco:@localhost/calendardb'
   modify this line according to the instance of your local database.
3. if you want to run the tests, setup the database connection in the test_config.py file on line 3:
   SQLALCHEMY_DATABASE_URI = 'mysql://marco:@localhost/calendardb'
   modify this line according to the instance of your local database.
4. In the adHoc Database dump, there are 100 users. They have usernames like this: User1, User2,...,User100. The password is the same for all: 'password'
