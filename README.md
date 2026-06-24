# Skanda_Major_Project_2026_SEN_PWA
## Requirements for downloading and running the app
To run this app, you will need to have flask, sqlite3 and bcrypt (if you do not have either of them, use pip install)
It also makes use of the random and datetime modules, which should not need downloading.

To host the website, you will need to download the whole file, then open app.py in an IDE (preferably Visual Studio Code), and run it.
Then, click the link it presents to go to the website.

Note that when setting up the code in VSC or whichever IDE is being used, there may be apparent errors present in the html documents, but rest assured, they do not cause any issues when the code is executed.

If you are using a Mac device, you will have to go to system settings and disable AirPlay Receiver, because this occupies the same port (5000) that the app runs on. Once you are finished with using the app, however, you may turn it back on.

When starting the app for the first time, it is recommended that you use the purge_db() function right before the init_db() by adding a line and nesting the function right below the if statement in the if __name__ == "__main__" statement. Then, for future uses, remove the function. This will ensure there is no other data existing in the database beforehand.

## How to use the app itself
Navigate within the IDE to app.py and press the run button. Click on the final URL by control-clicking (command for mac) on the http address links. As a new user with no account, you can take a demo test, and sign in. Signing in provides a more personalised experience for teachers and students. The latter of which can link their account to a teacher, allowing the teacher to see their students' scores on quizzes they may assign to the students.

## Note for teacher marking:
Considering this is a demo-grade version, there are 3 dummy users that are initialised into the database, each with different access levels. 'exampleuser1' is a teacher, 'exampleuser2' is a student and 'dummyhost' is a host. For now, the password to all 3 accounts are 'examplepassword123!'
