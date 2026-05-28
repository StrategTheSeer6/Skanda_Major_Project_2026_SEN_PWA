#imports
from flask import Flask, render_template, request, redirect, url_for, session
import bcrypt
import datetime
import sqlite3
import random
from git import Repo



#initialising Flask
app = Flask(__name__)
app.secret_key = 'sen_secret_key'

DB_PATH = "users.db"


#other assorted aspects to initialise when the app starts up
incorrectAttempts = 0



def auto_github_commit(repo_path, commit_message):
    try:
        repo = Repo(repo_path)
        # Stage all changes
        repo.git.add(update=True) 
        # Create the commit
        repo.index.commit(commit_message)
        # Push to the remote 'origin'
        origin = repo.remote(name='origin')
        origin.push()
        print("Successfully committed and pushed to GitHub.")
    except Exception as e:
        print(f"Error occurred: {e}")
# auto_github_commit('./', 'Automatic update from app.py')
# the above line of code can be used to commit and push changes to github.

#makes the database
def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            accesslevel TEXT NOT NULL DEFAULT 'student'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Question (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qsubtopic TEXT NOT NULL,
            qinfotext TEXT,
            qquestiontext TEXT NOT NULL,
            qassociatedimage TEXT,
            qquestiontype INTEGER NOT NULL,

            qcorrectanswer TEXT NOT NULL,
            qitem1 TEXT,
            qitem2 TEXT
            qitem3 TEXT,
            qitem4 TEXT,
            qitem1r TEXT,
            qitem2r TEXT
            qitem3r TEXT,
            qitem4r TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            testtakerid INTEGER,
            teacherid INTEGER,
            quiznumber INTEGER,
            score INTEGER
        )
    ''')





    conn.commit()
    conn.close()


def createDummyUser():
        conn = get_db()
        cursor = conn.cursor()
        dummy_password = bcrypt.hashpw("examplepassword123!".encode(), bcrypt.gensalt()).decode()
        data = ("exampleuser1", dummy_password, "example.user@det.nsw.edu.au", "teacher")
        cursor.execute('INSERT INTO User(username, password, email, accesslevel) VALUES (?, ?, ?, ?)', data)
        conn.commit()
        conn.close()


def generate_question_parameters(whatAreaWordIsWantedFrom, wordWantedFromDictionary = None, specificIndex = None):
    subtopics = ["sd phases", "datatypes", "errors", "algorithmic thinking", "debugging"]
    senPhases = ["requirements", "specifications", "design", "development", "integration", "testing & debugging", "installation", "maintenance"]
    eg_things_done_in_sen_phases = {
        "requirements": ["gathering requirements", "creating user stories", "creating use case diagrams"],
        "specifications": ["creating software requirement specifications", "creating technical specifications"],
        "design": ["creating flowcharts", "creating pseudocode", "creating algorithms"],
        "development": ["writing code", "using version control", "debugging code"],
        "integration": ["integrating different modules of code together", "resolving merge conflicts in version control"],
        "testing & debugging": ["writing test cases", "using debugging tools", "performing manual testing"],
        "installation": ["deploying software to a server", "setting up a database"],
        "maintenance": ["fixing bugs in existing code", "adding new features to existing code"]}
    egstrings = ["hello", "bye", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                 "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
                 "school", "software engineering", "python", "flowchart", "pseudocode", "algorithm", "debugging", "start", "end",
                 "if", "then", "else", "for", "while", "return", "pass", "break", "import",
                 ]
    #example integers and decimals are randomised using the random module
    


    pass

#this probably will not be needed because random.shuffle can be used in posting onto the front end.
def shuffle_options(item1, item2, item3, item4):
    options = [item1, item2, item3, item4]
    random.shuffle(options)
    return options[0], options[1], options[2], options[3]


def init_questions():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM Question')
    questionCount = cursor.fetchone()[0]

    if questionCount > 0:
        conn.close()
        print("No need to seed, questions already present.")
        return
    else:
        #mcq/arrange/select questions are in the format of (subtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, item1, item2, item3, item4, difficulty)
        #if anything is not applicable, it will be represented by "".
        #if something requires a string within it, wherever that string goes will be represented by "\\randomstring\\", and that will be replaced by a random string from egstrings in generate_question_parameters.
        #if there is to be a new line, it will be represented by \\n\\.
        #if the output needs to be remotely calculated, the qcorrectanswer and item1 fields will be left as None.


        fourOptionsQuestions = [

            #mcq
            ["understanding datatypes", "", "What datatype is \\randomstring\\?", "", 0, "string", "string", "integer", "float", "boolean", 2],
            ["understanding datatypes", "", "What datatype is \\randominteger\\?", "", 0, "integer", "string", "integer", "float", "boolean", 2],
            ["understanding datatypes", "", "What datatype is \\randomfloat\\?", "", 0, "float", "string", "integer", "float", "boolean", 2],
            ["understanding datatypes", "", "What datatype is \\randomboolean\\?", "", 0, "boolean", "string", "integer", "float", "boolean", 2],
            ["algorithmic thinking", "x = \\randominteger\\ \\n\\ for i in range(\\randominteger\\): \\n\\      x += \\randominteger\\ \\n\\ print(x)", "What will the output of this text be?", "", 0, None, None, "\\randominteger\\", "\\randominteger\\", "\\randominteger\\", 4],
            ["algorithmic thinking", "x = \\randominteger\\ \\n\\ for i in range(\\randominteger\\): \\n\\      x += \\randominteger\\", "What will the output of this text be?", "", 0, None, None, "No output", "\\randominteger\\", "\\randominteger\\", 4],



        ]

        numberQuestions = [
            #these are integer answers in the format of (subtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, difficulty), with no options. qquestiontype here will always be 4.
            #if the answer is to be calculated on the spot, the qcorrectanswer will be None.

            ("algorithmic thinking", "x = \\randominteger\\ \\n\\ for i in range(\\randominteger\\): \\n\\      x += \\randominteger\\ \\n\\ print(x)", "What will the output of this text be?", "", 4, None, 4)


        ]

        conn = get_db()
        cursor = conn.cursor()
        conn.close()



def get_question(subtopic, robotType):
    question_content, question_image_url, question_question, correct_num_or_string = None, None, None, None #present in all questions
    item1, item2, item3, item4 = None, None, None, None #multiple choice, arrange, select and match
    item1r, item2r, item3r, item4r = None, None, None, None #right items, only for match
    #for string, it is self-explanatory.
    #for integer (the integer answer will be written and matched as a string)
    #for mcq, it is the text of the correct answer as a string
    #for match, it is in the format of “L1R?L2R?L3R?L4R?”, with the question marks being replaced by the number of the right item that matches the left one.
    #for arrange, it is a string of the items in correct order in the format "1234"
    #for select, it is a string of the correct items in ascending order of when they appear.



    #robot types:
    #0 = multiple choice
    #1 = match
    #2 = arrange
    #3 = select all that apply
    #4 = integer
    #5 = string


    conn = get_db()
    cursor = conn.cursor()

    try:
        total_questions = cursor.execute('SELECT COUNT(*) FROM Question').fetchone()[0]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None, None, None

    if total_questions > 0:
        random_index = random.randint(0, total_questions - 1)
        question_data = cursor.execute('SELECT qinfotext, qassociatedimage, qquestiontext FROM Question WHERE qsubtopic = ? LIMIT 1 OFFSET ?', (subtopic, random_index,)).fetchone()
        if question_data:
            question_content, question_image_url, question_question, correct_num_or_string = question_data
        
        
        return question_content, question_image_url, question_question, correct_num_or_string
    else:
        
        return None, None, None



#starts by loading index.html, the home page at the root url (that is what the bare '/' means)



@app.route('/')
def home():
    
    return render_template('index.html', dummyUserIsIn = True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        uncpword = request.form['password']
        uncconfirmpword = request.form['confirm_password']
        uemail = request.form['email']

        if uncpword != uncconfirmpword:
            return render_template('register.html', error="Passwords do not match!")

        if "@det.nsw.edu.au" in uemail:
            alevel = "teacher"
        elif "@education.nsw.gov.au" in uemail:
            alevel = "student"
        else:
            return render_template('register.html', error="Email must be a valid school email address!")

        conn = get_db()
        cursor = conn.cursor()
        try:
            existing_user = cursor.execute('SELECT * FROM User WHERE email = ?', (uemail,)).fetchone()
            if existing_user:
                return render_template('register.html', error="This email is already registered!")
            
            hashed_password = bcrypt.hashpw(uncpword.encode(), bcrypt.gensalt()).decode()
            cursor.execute('INSERT INTO User (username, password, email, accesslevel) VALUES (?, ?, ?, ?)', (uname, hashed_password, uemail, alevel))
            conn.commit()
            user_id = cursor.execute('SELECT id FROM User WHERE username = ?', (uname,)).fetchone()[0]
            session['user_id'] = user_id
            return redirect(url_for('home', loggedIn=True))
        except sqlite3.Error as e:
            return render_template('register.html', error="An error occurred. Please try again.")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pword = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        try:
            user = cursor.execute('SELECT id, password FROM User WHERE username = ?', (uname,)).fetchone()
            if user and bcrypt.checkpw(pword.encode(), user[1].encode()):
                session['user_id'] = user[0]
                return redirect(url_for('home', loggedIn=True))
            return render_template('login.html', error="Invalid username or password!")
        except sqlite3.Error as e:
            return render_template('login.html', error="An error occurred. Please try again.")
        finally:
            conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
        session.pop('user_id', None)
        return redirect(url_for('home'))

@app.route('/preparation')
def preparation():
    return render_template('preparation.html')

@app.route('/signpage')
def signpage():
    return render_template('signpage.html')

@app.route('/realtest')
def realtest():

    return render_template('testpage.html', isTestReal = True)

@app.route('/practicetest')
def practicetest():

    return render_template('testpage.html', isTestReal = False)

@app.route('/testAnswer')
def testAnswer():
    if request.method == 'POST':
        answer = request.form['answer']


if __name__ == '__main__':
    with app.app_context():
      init_db()
      createDummyUser()
      #auto_github_commit('./', 'Testing automatic update from app.py')

      incorrectAttempts = 0
      app.run(debug=True)



#what command do i use to commit everything to a git repository? I know it's git commit -m "message"
#the git i need to connect it to is called 'StrategTheSeer6/Skanda_Major_Project_2026_SEN_PWA'
#how do i connect it to the repository in the first place? is it git init, then git remote add origin <repository_url>? and then git push -u origin main? (assuming the branch is called main)



#when i try git push -u origin main, it asks for my username and password, but i cannot type in the password at all. it does not accept any characters i type.
#it says remote: Invalid username or token. Password authentication is not supported for Git operations.
#to fix this, 
#when creating a personal access token, what are the minimum permissions needed?
# the permissions that should be added are:
#