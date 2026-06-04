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
            qitem4r TEXT,
            difficulty INTEGER NOT NULL DEFAULT 3
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            testtakerid INTEGER,
            teacherid INTEGER,
            quiznumber INTEGER,
            score INTEGER,
            totalmarks INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Signs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signtitle TEXT NOT NULL,
            signimageurl TEXT,
            signtext TEXT NOT NULL
            
        )                          
    ''')
    #signtitles are unique



    conn.commit()
    conn.close()

def createDummyUser():
        conn = get_db()
        cursor = conn.cursor()
        dummy_password = bcrypt.hashpw("examplepassword".encode(), bcrypt.gensalt()).decode()
        data = ("exampleuser1", dummy_password, "example.user@det.nsw.edu.au", "teacher")
        cursor.execute('INSERT INTO User(username, password, email, accesslevel) VALUES (?, ?, ?, ?)', data)
        conn.commit()
        conn.close()

def generate_question_parameter(whatAreaWordIsWantedFrom, wordWantedFromDictionary = None, specificIndex = None):
    #whatAreaWordIsWantedFrom refers to what is actually wanted
    #wordWantedFromDictionary only applies to the dictionaries where a specific key is needed.
    #specificIndex only applies to the lists where a specific index is needed. If it is not provided, a random item is returned.
    
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
    egstrings = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "hello", "bye",
                 "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
                 "school", "software engineering", "python", "flowchart", "pseudocode", "algorithm", "debugging", "start", "end",
                 "if", "then", "else", "for", "while", "return", "pass", "break", "import",
                 ]
    #example integers and decimals are randomised using the random module
    if whatAreaWordIsWantedFrom == "subtopic":
        if specificIndex is not None and 0 <= specificIndex < len(subtopics):
            return subtopics[specificIndex]
        return random.choice(subtopics)
    elif whatAreaWordIsWantedFrom == "sen phase":
        if specificIndex is not None and 0 <= specificIndex < len(senPhases):
            return senPhases[specificIndex]
        return random.choice(senPhases)
    elif whatAreaWordIsWantedFrom == "eg thing done in sen phase":
        if wordWantedFromDictionary in eg_things_done_in_sen_phases:
            return random.choice(eg_things_done_in_sen_phases[wordWantedFromDictionary])
        else:
            raise ValueError(f"Invalid SEN phase: {wordWantedFromDictionary}")
    elif whatAreaWordIsWantedFrom == "eg string":
        return random.choice(egstrings)
    elif whatAreaWordIsWantedFrom == "eg integer":
        return random.randint(1, 100)
    elif whatAreaWordIsWantedFrom == "eg float":
        return round(random.uniform(1.0, 100.0), 2)
    elif whatAreaWordIsWantedFrom == "eg boolean":
        return random.choice([True, False])
    else:
        raise ValueError(f"Invalid area requested: {whatAreaWordIsWantedFrom}")
    
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
            ["algorithmic thinking", "x = \\randominteger\\ \n for i in range(\\randominteger\\): \n      x += \\randominteger\\ \n print(x)", "What will the output of this text be?", "", 0, "", "", "\\randominteger\\", "\\randominteger\\", "\\randominteger\\", 4],
            ["algorithmic thinking", "x = \\randominteger\\ \n for i in range(\\randominteger\\): \n      x += \\randominteger\\", "What will the output of this text be?", "", 0, "", "", "No output", "\\randominteger\\", "\\randominteger\\", 4],



        ]

        numberOrStringQuestions = [
            #these are integer answers in the format of (subtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, difficulty), with no options. qquestiontype here will always be 4.
            #if the answer is to be calculated on the spot, the qcorrectanswer will be None.

            ("algorithmic thinking", "x = \\randominteger\\ \n for i in range(\\randominteger\\): \n      x += \\randominteger\\ \n print(x)", "What will the output of this text be?", "", 4, None, 4)


        ]


        for question in fourOptionsQuestions:
            cursor.execute('INSERT INTO Question (qsubtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, item1, item2, item3, item4, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', question)

        for question in numberOrStringQuestions:
            cursor.execute('INSERT INTO Question (qsubtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?)', question)

        conn.commit()

        conn.close()

def init_signs():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM Signs')
    signCount = cursor.fetchone()[0]
    if signCount > 0:
        conn.close()
        print("No need to seed, questions already present.")
        return
    else:
        signs = [
            #these are in the format of title, imageurl (if there is no image, it will be ""), and the body text. All strings.
            ["", "", ""]
        ]

        for sign in signs:
            cursor.execute('INSERT INTO Signs (signtitle, signimageurl, signtext) VALUES (?, ?, ?)', sign)






def check_var_for_indicator(variable):
    #the variable (a string) is checked for the indicators
    while "\\randomstring\\" in variable:
        variable.replace("\\randomstring\\", generate_question_parameter("eg string"))
    while "\\randominteger\\" in variable:
        variable.replace("\\randominteger\\", generate_question_parameter("eg integer"))
    while "\\randomfloat\\" in variable:
        variable.replace("\\randomfloat\\", generate_question_parameter("eg float"))
    while "\\randomboolean\\" in variable:
        variable.replace("\\randomboolean\\", generate_question_parameter("eg boolean"))
    while "\\randomsenphase\\" in variable:
        variable.replace("\\randomsenphase\\", generate_question_parameter("sen phase"))
    while "\\randomthingdoneinsenphase\\" in variable:
        variable.replace("\\randomthingdoneinsenphase\\", generate_question_parameter("eg thing done in sen phase", wordWantedFromDictionary=generate_question_parameter("sen_phase")))
    while "\\randomsubtopic\\" in variable:
        variable.replace("\\randomsubtopic\\", generate_question_parameter("subtopic"))
    return variable

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
        total_questions = cursor.execute('SELECT COUNT(*) FROM Question WHERE qquestiontype = ?', (robotType)).fetchone()[0]
    except sqlite3.Error as e:
        print(f"Look out! There was a database error: {e}")
        return [None, None, None, None]

    if total_questions > 0:
        random_index = random.randint(0, total_questions - 1)
        question_data = cursor.execute('SELECT id, qinfotext, qassociatedimage, qquestiontext, qcorrectanswer FROM Question WHERE qsubtopic = ? LIMIT 1 OFFSET ?', (subtopic, random_index,)).fetchone()
        if question_data:
            qid, question_content, question_image_url, question_question, correct_num_or_string = question_data

            if robotType in [0, 1, 2, 3]: #questions with at least 4 options
                item1, item2, item3, item4 = cursor.execute('SELECT item1, item2, item3, item4 FROM Question WHERE id = ?', (qid,)).fetchone()
                if item4 is not None: #the fourth option will always have a value in 4 option questions.
                    if robotType == 1: #for match questions
                        item1r, item2r, item3r, item4r = cursor.execute('SELECT item1r, item2r, item3r, item4r FROM Question WHERE id = ?', (qid)).fetchone()
                        
                        return [question_content, question_image_url, question_question, correct_num_or_string, item1, item2, item3, item4, item1r, item2r, item3r, item4r]
                    return [question_content, question_image_url, question_question, correct_num_or_string, item1, item2, item3, item4]
                return [question_content, question_image_url, question_question, correct_num_or_string]
            else:
                return [question_content, question_image_url, question_question, correct_num_or_string]
    else:
        return [None, None, None, None]


def get_sign(signtitle):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        sign_data = cursor.execute('SELECT signimageurl, signtext FROM Signs WHERE signtitle = ?', (signtitle,)).fetchone()
        if sign_data:
            sign_image_url, sign_text = sign_data
            return [sign_image_url, sign_text]
        else:
            print(f"No sign found with title: {signtitle}")
            return [None, None]
    except sqlite3.Error as e:
        print(f"Look out! There was a database error: {e}")
        return [None, None]


def makeTestOrder(subtopic, examTemplate, signtitles):
    #an exam template can look like this: [0, 0, 2, 2, 9, 4, 4, 5, 5, 5, 5, 9]
    # in this one there are 2 mcqs, 2 arranges, 1 sign, 2 integers, 4 strings and 1 more sign.
    
    testOrder = []

    for robotType in examTemplate:
        if robotType in [0, 1, 2, 3, 4, 5]:
            testOrder.append(get_question(subtopic, robotType))
        elif robotType == 9:
            #9 means there is a sign
            try:
                signTitle = signtitles.pop(0) # the first title in the list is taken and removed from the list
                testOrder.append(get_sign(signTitle))
            except IndexError as e:
                print(f"Bad template writing. You have a skill issue mr developer and here is your error: {e}")
                testOrder.append([None, None])
        else:
            print(f"Invalid robot type in exam template: {robotType}")
            return signtitles[0] #just there for bug fixing purposes
    
    return testOrder

def makeDemoTest():
    template = [9, 0, 0, 0, 0, 9, 0, 0, 0, 0, 9, 0, 0, 9]
    signtitles = []















#starts by loading index.html, the home page at the root url (that is what the bare '/' means)


@app.route('/')
def home():
    
    return render_template('index.html')

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
            return redirect(url_for('loggedinhomepage'))
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
            if user and bcrypt.checkpw(pword.encode(), user[1] if isinstance(user[1], bytes) else user[1].encode()):
                session['user_id'] = user[0]
                return redirect(url_for('loggedinhomepage', loggedIn = True))
            else:
                #incorrectAttempts += 1
                return render_template('login.html', error=f"Invalid username or password! Note that both fields are case-sensitive.")
        except sqlite3.Error as e:
            return render_template('login.html', error="An error occurred. Please try again.")
        finally:
            conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
        session.pop('user_id', None)
        return redirect(url_for('login'))

@app.route('/preparation')
def preparation():
    return render_template('preparation.html')

@app.route('/signpage')
def signpage():
    return render_template('signpage.html')

@app.route('/realtest')
def realtest():
    print("this place is not real")
    return render_template('testpage.html', isTestReal = True)

@app.route('/practicetest')
def practicetest():

    return render_template('testpage.html', isTestReal = False)

@app.route('/testanswer', methods=['GET', 'POST'])
def testanswer():
    if request.method == 'POST':
        answer = request.form['answer']
        return render_template('login.html', error = answer)
    return render_template('login.html', error = answer)

@app.route('/loggedinhomepage')
def loggedinhomepage():
    return render_template('loggedinhomepage.html')


if __name__ == '__main__':
    with app.app_context():
      init_db()
      createDummyUser()
      #init_questions()
      #init_signs()
      #auto_github_commit('./', 'Testing automatic update from app.py')


      incorrectAttempts = 0
      app.run(debug=True)
