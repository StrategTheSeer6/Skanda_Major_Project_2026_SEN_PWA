#imports
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import bcrypt
import datetime
import sqlite3
import random
from git import Repo



#initialising Flask
app = Flask(__name__)
app.secret_key = 'sen_secret_key' #os.environ['SECRET_KEY']

DB_PATH = "users.db"


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
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            accesslevel TEXT NOT NULL DEFAULT 'student',
            teacherid INTEGER,
            assignedcourses TEXT,

            FOREIGN KEY (teacherid) REFERENCES User(id)

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

            qcorrectanswer TEXT,
            qanswerspecialmethod TEXT,
            item1 TEXT,
            item2 TEXT,
            item3 TEXT,
            item4 TEXT,
            item1r TEXT,
            item2r TEXT,
            item3r TEXT,
            item4r TEXT,
            difficulty INTEGER NOT NULL DEFAULT 3
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS QuizResult (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question_id INTEGER,
            quiz_index INTEGER,
            given_answer TEXT,
            correct_answer TEXT,
            is_correct INTEGER,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES User(id)
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
            signtitle TEXT NOT NULL UNIQUE,
            signimageurl TEXT,
            signtext TEXT NOT NULL
            
        )                          
    ''')
    #signtitles are unique



    conn.commit()
    conn.close()
def purge_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS User')
    cursor.execute('DROP TABLE IF EXISTS Question')
    cursor.execute('DROP TABLE IF EXISTS Marks')
    cursor.execute('DROP TABLE IF EXISTS Signs')
    conn.commit()
    conn.close()
def createDummyUser():
    conn = get_db()
    cursor = conn.cursor()
    dummy_password = bcrypt.hashpw("examplepassword123!".encode(), bcrypt.gensalt()).decode()
    data = ("exampleuser1", dummy_password, "example.user@det.nsw.edu.au", "teacher")
    try:
        existingid = cursor.execute('SELECT id FROM User WHERE email = ?', (data[2],)).fetchone()
        if existingid:
            print("Dummy user already exists, no need to create.")
            return
        else:
            cursor.execute('INSERT INTO User(username, password, email, accesslevel) VALUES (?, ?, ?, ?)', data)
            return
    except sqlite3.Error as e:
        print(f"Database error {e}")
        cursor.execute('INSERT INTO User(username, password, email, accesslevel) VALUES (?, ?, ?, ?)', data)
    finally:
        conn.commit()
        conn.close()
    return

def init_sessionData():
    if session.get('initialised') is None:
        session['initialised'] = True
        session['incorrectAttempts'] = 0
        session['lastFail'] = None

        session['current_question_index'] = 0
        session['test_order'] = []
        session['current_question_data'] = {}
        session['current_question_params'] = []
        session['question_number_within_test'] = 0

utc_plus_10 = datetime.timezone(datetime.timedelta(hours=10))

#global variables for question bank use
subtopics = ["sd phases", "datatypes", "errors", "algorithmic thinking", "debugging"]
senPhases = ["requirements", "specifications", "design", "development", "integration", "testing & debugging", "installation", "maintenance", "None"]
eg_things_done_in_sen_phases = {
    "requirements": ["gathering requirements", "creating user stories", "creating use case diagrams"],
    "specifications": ["creating software requirement specifications", "creating technical specifications"],
    "design": ["creating flowcharts", "creating pseudocode", "creating algorithms"],
    "development": ["writing code", "using version control", "debugging code"],
    "integration": ["integrating different modules of code together", "resolving merge conflicts in version control"],
    "testing & debugging": ["writing test cases", "using debugging tools", "performing manual testing"],
    "installation": ["deploying software to a server", "setting up a database"],
    "maintenance": ["fixing bugs in existing code", "adding new features to existing code"]}
egstrings = ["'1'", "'2'", "'3'", "'4'", "'5'", "'6'", "'7'", "'8'", "'9'", "'10'", "'11'", "'12'", "'hello'", "'bye'",
                "'a'", "'b'", "'c'", "'d'", "'e'", "'f'", "'g'", "'h'", "'i'", "'j'", "'k'", "'l'", "'m'", "'n'", "'o'", "'p'", "'q'", "'r'", "'s'", "'t'", "'u'", "'v'", "'w'", "'x'", "'y'", "'z'",
                "'school'", "'software engineering'", "'python'", "'flowchart'", "'pseudocode'", "'algorithm'", "'debugging'", "'start'", "'end'",
                "'if'", "'then'", "'else'", "'for'", "'while'", "'return'", "'pass'", "'break'", "'import'",
                ]
glossaryTerms = {
"version control": "A system that tracks changes to source code and other project files over time, allowing developers to manage revisions, compare versions, and restore previous states.",
"hosting & collaboration": "The use of online platforms to store software projects, share code, coordinate development, review contributions, and work with others on the same project.",
"agile project management": "An iterative project management approach that emphasises collaboration, flexibility, regular feedback, and delivering software in small, incremental updates.",
"sequence": "A control structure in which instructions are executed one after another in the order they appear.",
"selection": "A control structure that chooses between alternative paths of execution based on a condition being true or false.",
"iteration": "A control structure that repeatedly executes a set of instructions while a condition is met or for a specified number of times.",
"divide & conquer": "An algorithm design technique that solves a problem by breaking it into smaller subproblems, solving each independently, and combining the results.",
"backtracking": "An algorithmic technique that explores possible solutions and reverses previous decisions when a path does not lead to a valid solution.",
"flowcharts": "Diagrammatic representations of algorithms that use standard symbols to show the sequence, decisions, inputs, outputs, and flow of control.",
"pseudocode": "A language-independent way of describing algorithms using structured, human-readable statements that resemble programming code.",
"structure charts": "Diagrams that show the hierarchical organisation of modules or functions within a program and the relationships between them.",
"abstraction": "The process of simplifying complexity by focusing on essential features while hiding unnecessary implementation details.",
"imperative paradigm": "A programming paradigm where programs are written as sequences of commands that explicitly change a program's state.",
"object oriented programming paradigm": "A programming paradigm based on objects that combine data and behaviour, using concepts such as classes, inheritance, encapsulation, and polymorphism.",
"logic paradigm": "A programming paradigm where problems are expressed as facts and rules, and solutions are derived through logical inference.",
"functional paradigm": "A programming paradigm that treats computation as the evaluation of functions and emphasises immutability and avoiding side effects.",
"binary": "A base-2 number system that uses only the digits 0 and 1 and is the fundamental representation of data in computers.",
"decimal": "A base-10 number system that uses the digits 0 to 9 and is commonly used by humans for counting and calculations.",
"hexadecimal": "A base-16 number system that uses the digits 0–9 and letters A–F, often used as a compact representation of binary data.",
"integer": "A whole number data type that can represent positive, negative, or zero values without a fractional component.",
"real": "A numeric data type used to represent numbers that may contain decimal places or fractional values.",
"single precision floating point": "A 32-bit data type used to store approximate real numbers with a limited range and level of precision.",
"char": "A data type used to store a single character, such as a letter, digit, or symbol.",
"string": "A sequence of characters stored together and treated as a single piece of text.",
"boolean": "A data type that stores one of two possible values: true or false.",
"date & time": "A data type used to represent calendar dates, times, or both, often allowing calculations involving time intervals.",
"data dictionary": "A collection of metadata that defines and describes the data used in a system, including names, types, sizes, and rules.",
"data name": "The identifier used to refer to a data item, variable, field, or structure within a program or system.",
"data type": "A classification that specifies the kind of value a piece of data can store and the operations that can be performed on it.",
"data structure": "A method of organising and storing data so it can be accessed, managed, and modified efficiently.",
"size/length": "A specification of the amount of storage allocated to a data item or the number of elements or characters it contains.",
"validation rules": "Constraints applied to data to ensure that entered values are reasonable, complete, and in the correct format.",
"relationship": "A connection between data entities that describes how they are associated with one another.",
"arrays": "Data structures that store multiple values of the same data type in an ordered collection accessed by index.",
"records": "Data structures that group related fields of potentially different data types into a single unit.",
"trees": "Hierarchical data structures consisting of nodes connected by parent-child relationships.",
"sequential files": "Files in which records are stored and accessed in a specific order, typically one after another.",
"single array": "A one-dimensional array that stores elements in a single sequence and is accessed using one index.",
"multidimensional arrays": "Arrays with two or more dimensions, allowing data to be organised in rows, columns, or higher-dimensional structures.",
"lists": "Dynamic data structures that store ordered collections of items and can grow or shrink during program execution.",
"stacks": "Linear data structures that follow the Last In, First Out (LIFO) principle, where the most recently added item is removed first.",
"dictionaries": "Data structures that store data as key-value pairs, allowing values to be retrieved using unique keys.",
"functionality": "The extent to which software performs the required tasks and meets specified user requirements.",
"performance": "A measure of how efficiently software operates, including factors such as speed, responsiveness, and resource usage.",
"syntax error": "An error caused by code that violates the grammatical rules of a programming language, preventing compilation or execution.",
"logic error": "An error where a program runs but produces incorrect results because the algorithm or reasoning is flawed.",
"runtime error": "An error that occurs while a program is executing, often causing it to stop unexpectedly or behave incorrectly.",
"breakpoints": "Markers placed in code that pause program execution during debugging so program state can be inspected.",
"single line stepping": "A debugging technique that executes a program one statement at a time to observe its behaviour in detail.",
"watches": "Debugging tools that monitor the values of variables or expressions as a program executes.",
"interfaces between functions": "The parameters, return values, and communication mechanisms that allow functions to interact and exchange data.",
"debugging output statements": "Temporary statements added to code to display variable values, program flow, or other information to help identify errors.",
"Integrated Development Environments (IDE)": "Software applications that provide tools such as a code editor, compiler, debugger, and project management features to support software development."
}
examplesOfTerms = {
    "version control": ["git"],
    "hosting and collaboration": ["github", "gitlab", "bitbucket"]
}







def generate_question_parameter(whatAreaWordIsWantedFrom, wordWantedFromDictionary = None, specificIndex = None, wrongOption=False):
    #whatAreaWordIsWantedFrom refers to what is actually wanted
    #wordWantedFromDictionary only applies to the dictionaries where a specific key is needed.
    #specificIndex only applies to the lists where a specific index is needed. If it is not provided, a random item is returned.
    global subtopics, senPhases, eg_things_done_in_sen_phases, egstrings, glossaryTerms, examplesOfTerms


    #example integers and decimals are randomised using the random module
    if whatAreaWordIsWantedFrom == "subtopic":
        if specificIndex is not None and 0 <= specificIndex < len(subtopics):
            return subtopics[specificIndex]
        return random.choice(subtopics)
    elif whatAreaWordIsWantedFrom == "sen phase":
        if specificIndex is not None and 0 <= specificIndex < len(senPhases):
            return senPhases[specificIndex]
        senphase = "None"
        while senphase == "None":
            senphase = random.choice(senPhases)
        return senphase
    elif whatAreaWordIsWantedFrom == "eg string":
        while True:
            value = random.choice(egstrings)
            if not wrongOption or value != session['current_question_data']['answer']:
                return value
    elif whatAreaWordIsWantedFrom == "eg integer":
        while True:
            value = str(random.randint(1, 100))
            if not wrongOption or value != session['current_question_data']['answer']:
                return value
    elif whatAreaWordIsWantedFrom == "eg float":
        while True:
            value = str(round(random.uniform(1.0, 100.0), 2))
            if not wrongOption or value != session['current_question_data']['answer']:
                return value
    elif whatAreaWordIsWantedFrom == "eg boolean":
        while True:
            value = random.choice(["True", "False"])
            if not wrongOption or value != session['current_question_data']['answer']:
                return value
    elif whatAreaWordIsWantedFrom == "eg thing done in sen phase":
        if wordWantedFromDictionary in eg_things_done_in_sen_phases:
            return random.choice(eg_things_done_in_sen_phases[wordWantedFromDictionary])
        else:
            raise ValueError(f"Invalid SEN phase: {wordWantedFromDictionary}")
    else:
        raise ValueError(f"Invalid area requested: {whatAreaWordIsWantedFrom}")

    
# random.shuffle can be used to shuffle the data when posting the questions

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
        #mcq/arrange/select questions are in the format of (subtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, item1, item2, item3, item4, qanswerspecialmethod, difficulty)
        #if anything is not applicable, it will be represented by "".
        #if something requires a string within it, wherever that string goes will be represented by "\\randomstring\\", and that will be replaced by a random string from egstrings in generate_question_parameters.
        #if there is to be a new line, it will be represented by \n.
        #if the output needs to be remotely calculated, the qcorrectanswer and item1 fields will be left as None.
        #the different subtopics are as follows: "sd phases", "algorithmic thinking", "datatypes", "errors", "debugging"

        fourOptionsQuestions = [

            #phases
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which phase comes after the \\randomsenphase\\ phase?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "",
                "item1": "",
                "item2": "\\randomsenphase\\",
                "item3": "\\randomsenphase\\",
                "item4": "\\randomsenphase\\",
                "qanswerspecialmethod": "findnextphase",
                "difficulty": 2
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which phase comes before the \\randomsenphase\\ phase?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "",
                "item1": "",
                "item2": "\\randomsenphase\\",
                "item3": "\\randomsenphase\\",
                "item4": "\\randomsenphase\\",
                "qanswerspecialmethod": "findpreviousphase",
                "difficulty": 2
            },

            #datatypes
            {
                "subtopic": "understanding datatypes",
                "qinfotext": "",
                "qquestiontext": "What datatype is \\randomstring\\?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "string",
                "item1": "string",
                "item2": "integer",
                "item3": "float",
                "item4": "boolean",
                "qanswerspecialmethod": "datatype",
                "difficulty": 2
            },
            {
                "subtopic": "understanding datatypes",
                "qinfotext": "",
                "qquestiontext": "What datatype is \\randominteger\\?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "integer",
                "item1": "string",
                "item2": "integer",
                "item3": "float",
                "item4": "boolean",
                "qanswerspecialmethod": "datatype",
                "difficulty": 2
            },
            {
                "subtopic": "understanding datatypes",
                "qinfotext": "",
                "qquestiontext": "What datatype is \\randomfloat\\?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "float",
                "item1": "string",
                "item2": "integer",
                "item3": "float",
                "item4": "boolean",
                "qanswerspecialmethod": "datatype",
                "difficulty": 2
            },
            {
                "subtopic": "understanding datatypes",
                "qinfotext": "",
                "qquestiontext": "What datatype is \\randomboolean\\?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "boolean",
                "item1": "string",
                "item2": "integer",
                "item3": "float",
                "item4": "boolean",
                "qanswerspecialmethod": "datatype",
                "difficulty": 2
            },

            #addloop
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "x = \\randominteger\\ \n for i in range(\\randominteger\\): \n      x += \\randominteger\\ \n print(x)",
                "qquestiontext": "What will the output of this code be?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "",
                "item1": "",
                "item2": "\\randominteger\\",
                "item3": "\\randominteger\\",
                "item4": "\\randominteger\\",
                "qanswerspecialmethod": "addloop",
                "difficulty": 5
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "x = \\randominteger\\ \n for i in range(\\randominteger\\): \n      x += \\randominteger\\",
                "qquestiontext": "What will the output of this code be?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "No output",
                "item1": "No output",
                "item2": "\\randominteger\\",
                "item3": "\\randominteger\\",
                "item4": "\\randominteger\\",
                "qanswerspecialmethod": "addloop",
                "difficulty": 4
            },

            #add2
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "x = \\randominteger\\ \n y = \\randominteger\\ \n sum = 'x' + 'y' \n print(sum)",
                "qquestiontext": "What will the output of this code be?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "'xy'",
                "item1": "",
                "item2": "xy",
                "item3": "'sum'",
                "item4": "\\randominteger\\",
                "qanswerspecialmethod": "add2",
                "difficulty": 3
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "x = \\randominteger\\ \n y = \\randominteger\\ \n sum = x + y \n print('sum')",
                "qquestiontext": "What will the output of this code be?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "'sum'",
                "item1": "",
                "item2": "xy",
                "item3": "'sum'",
                "item4": "\\randominteger\\",
                "qanswerspecialmethod": "add2",
                "difficulty": 3
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "x = \\randominteger\\ \n y = \\randominteger\\ \n sum = x + y \n print(sum)",
                "qquestiontext": "What will the output of this code be?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "",
                "item1": "",
                "item2": "xy",
                "item3": "'sum'",
                "item4": "\\randominteger\\",
                "qanswerspecialmethod": "add2",
                "difficulty": 3
            },

        ]

        numberOrStringQuestions = [
            #these are integer answers in the format of (subtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, difficulty), with no options. qquestiontype here will always be 4.
            #if the answer is to be calculated on the spot, the qcorrectanswer will be None.


            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "x = \\randominteger\\ \n y = \\randominteger\\ \n sum = x + y \n print(sum)",
                "qquestiontext": "What will the output of this code be?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "",
                "qanswerspecialmethod": "add2",
                "difficulty": 3
            },

        ]

        #because it is going from list to dictionary, this will have to be changed

        for question in fourOptionsQuestions:
            qattributelist = []
            for attribute in question.values():
                qattributelist.append(attribute)
            cursor.execute('INSERT INTO Question (qsubtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, item1, item2, item3, item4, qanswerspecialmethod, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', qattributelist)

        for question in numberOrStringQuestions:
            qattributelist = []
            for attribute in question.values():
                qattributelist.append(attribute)
            cursor.execute('INSERT INTO Question (qsubtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, qanswerspecialmethod, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', qattributelist)

        conn.commit()
        conn.close()
        return
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
            ["Welcome", "", "<h2>Welcome to the Software Engineering Course!</h2><p> Here in SEN, there are many topics to explore, such as the phases of the SDLC, understanding datatypes, algorithmic thinking, errors and debugging. \n\n This is a sign, as I'm sure you're aware, and you'll see many of these in your time here. Signs are full of important information, so make sure to read them carefully! \n\n You will also encounter robots, each having their own way of defeating them. Solve their questions to deactivate them and progress through the course!</p>"],
            ["Demo Finish", "", "<h2>Congratulations!</h2><p> You finished the demo quiz on the Software Development Phases! If you want to try more quizzes, you will have to sign up or log in if you already have an account.</p>"],
            ["SDLC Steps Part 1", "", "<h2>Requirements Definition:</h2><p> \n The initial phase where the needs of the user/client are gathered and clearly documented. It defines what the system must do.\n\n </p><h2>Determining Specifications:</h2><p> \n Translating the broad requirements into detailed, measurable specifications. This involves documenting both functional (what it does) and non-functional (how well it does it, e.g. speed, security) requirements.\n\n </p><h2>Design:</h2><p> \n Planning the how. Creating blueprints for the software, including user interface (UI), data structures and algorithms. Involves top-down design (breaking down) and bottom-up design (building components).</p>"],
            ["SDLC Steps Part 2", "", "<h2>Development (Coding):</h2><p> \n The actual writing of the software code based on the design specifications. This is often the longest phase. \n\n </p><h2>Integration:</h2><p> \n Combining individual, tested modules (subprograms) into a complete, working software system. This step focuses on ensuring all parts communicate correctly. \n\n </p><h2>Testing and Debugging:</h2><p> \n Rigorously checking the integrated software against the specifications to find and fix errors. Testing finds the error; Debugging locates and corrects the error.</p>"],
            ["SDLC Steps Part 3", "", "<h2>Installation:</h2><p> \n Deploying the finidhed software into the client's working environment (e.g. installing it on their servers or computers). This includes setting up databases and configuring networks. \n\n </p><h2>Maintenance:</h2><p> \n Ongoing activity after deployment to keep the system operational and relevant. Includes fixing bugs (corrective), adapting to new environments (adaptive), and adding new features (perfective).</p>"]
        ]

        for sign in signs:
            cursor.execute('INSERT INTO Signs (signtitle, signimageurl, signtext) VALUES (?, ?, ?)', sign)

        conn.commit()
        conn.close()
        return

def check_var_for_indicator(variable, addToSessionData = True):
    #the variable (a string) is checked for the indicators
    params = []
    while "\\randominteger\\" in variable:
        value = generate_question_parameter("eg integer")
        params.append(value)
        variable = variable.replace("\\randominteger\\", value, 1)
    while "\\randomstring\\" in variable:
        value = generate_question_parameter("eg string")
        params.append(value)
        variable = variable.replace("\\randomstring\\", value, 1)
    while "\\randomboolean\\" in variable:
        value = generate_question_parameter("eg boolean")
        params.append(value)
        variable = variable.replace("\\randomboolean\\", value, 1)
    while "\\randomfloat\\" in variable:
        value = generate_question_parameter("eg float")
        params.append(value)
        variable = variable.replace("\\randomfloat\\", value, 1)
    while "\\randomsenphase\\" in variable:
        value = generate_question_parameter("sen phase")
        params.append(value)
        variable = variable.replace("\\randomsenphase\\", value, 1)
    while "\\randomthingdoneinsenphase\\" in variable:
        value = generate_question_parameter("eg thing done in sen phase", wordWantedFromDictionary=generate_question_parameter("sen phase"))
        params.append(value)
        variable = variable.replace("\\randomthingdoneinsenphase\\", value, 1)
    while "\\randomsubtopic\\" in variable:
        value = generate_question_parameter("subtopic")
        params.append(value)
        variable = variable.replace("\\randomsubtopic\\", value, 1)
    if addToSessionData:
        for param in params:
            if session.get('current_question_params'):
                session['current_question_params'].append(param)
            else:
                session['current_question_params'] = [param]
    return variable

#get_question may be deleted because it shall no longer be used.
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
        total_questions = cursor.execute('SELECT COUNT(*) FROM Question WHERE qquestiontype = ? AND qsubtopic = ?', (robotType, subtopic,)).fetchone()[0]
    except sqlite3.Error as e:
        print(f"Look out! There was a database error: {e}")
        return [None, None, None, None]
    else:
        if total_questions > 0:
            random_index = random.randint(0, total_questions - 1)
            question_data = cursor.execute('SELECT id, qinfotext, qassociatedimage, qquestiontext, qcorrectanswer, qanswerspecialmethod, difficulty FROM Question WHERE qquestiontype = ? AND qsubtopic = ? LIMIT 1 OFFSET ?', (robotType, subtopic, random_index,)).fetchone()
            if question_data:
                qid = question_data[0]
                qdiff = question_data[-1]
                qdict = {
                        "robotType": robotType,
                        "infotext": question_data[1],
                        "qimage": question_data[2],
                        "questiontext": question_data[3],
                        "answer": question_data[4],
                        "qansmethod": question_data[5],
                        "qdiff": question_data[6]
                    }

                if robotType in [0, 1, 2, 3]: #questions with at least 4 options
                    options = cursor.execute('SELECT item1, item2, item3, item4 FROM Question WHERE id = ?', (qid,)).fetchone()
                    for option in options:
                        option = check_var_for_indicator(option)

                    if item4 is not None: #the fourth option will always have a value in 4 option questions.
                        if robotType == 1: #for match questions
                            item1r, item2r, item3r, item4r = cursor.execute('SELECT item1r, item2r, item3r, item4r FROM Question WHERE id = ?', (qid)).fetchone()
                            item1r = check_var_for_indicator(item1r)
                            item2r = check_var_for_indicator(item2r)
                            item3r = check_var_for_indicator(item3r)
                            item4r = check_var_for_indicator(item4r)
                            return [robotType, question_content, question_image_url, question_question, correct_num_or_string, item1, item2, item3, item4, item1r, item2r, item3r, item4r, qdiff]
                        return [robotType, question_content, question_image_url, question_question, correct_num_or_string, item1, item2, item3, item4, qdiff]
                    return [robotType, question_content, question_image_url, question_question, correct_num_or_string, qdiff]
                else:
                    
                    return [robotType, question_content, question_image_url, question_question, correct_num_or_string, qdiff]

        else:
            return [0, None, None, None, None]
    finally:
        conn.close()
def get_sign(signtitle):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        
        row = cursor.execute(
            'SELECT signimageurl, signtext FROM Signs WHERE signtitle=?',
            (signtitle,)
        ).fetchone()
        conn.close()

        if row:
            return {"robotType": 9, "title": signtitle, "image": row[0], "text": row[1]}

        return {"robotType": 9, "title": signtitle, "image": None, "text": None}
    except sqlite3.Error as e:
        print(f"Look out! There was a database error: {e}")
        return {"robotType": 9, "title": signtitle, "image": None, "text": None}

def solve_question(qsolvemethod, params): #params shall always be a list
    global subtopics, senPhases, eg_things_done_in_sen_phases, egstrings, glossaryTerms, examplesOfTerms

    if params:
        if qsolvemethod == "datatype":
            #here, it assumes params is a single value
            intList = []
            for i in range(101):
                intList.append(str(i))

            if params in intList:
                return "integer"
            elif params in ["True", "False"]:
                return "boolean"
            elif "." in params:
                return "float"
            else:
                return "string"
        
        elif qsolvemethod == "add2":
            #takes 2 values
            return int(params[0]) + int(params[1])
        elif qsolvemethod == "addloop":
            #takes 3 values
            return int(params[0] + (int(params[1]) * int(params[2])))
        
        elif qsolvemethod == "findnextphase":
            #the previous phase is given in params
            if params == "maintenance":
                return "None"
            else:
                phaseindex = senPhases.index(params)
                return senPhases[phaseindex + 1]
        elif qsolvemethod == "findpreviousphase":
            #the phase is given in params
            if params == "requirements":
                return "None"
            else:
                phaseindex = senPhases.index(params)
                return senPhases[phaseindex - 1]

        else: #should not be called.
            return ""
    else: #should not be called.
        return ""



def generate_question_by_id(qid):
    conn = get_db()
    cursor = conn.cursor()

    q = cursor.execute('''
        SELECT id, qinfotext, qquestiontext, qassociatedimage,
               qquestiontype, qcorrectanswer, qanswerspecialmethod,
               item1, item2, item3, item4, difficulty
        FROM Question WHERE id=?
    ''', (qid,)).fetchone()

    conn.close()

    if not q:
        return None

    question_to_send =  {
        "type": "question",
        "id": q[0],
        "info": check_var_for_indicator(q[1]),
        "text": check_var_for_indicator(q[2]),
        "image": q[3],
        "robotType": q[4],
        "answer": q[5],
        "method": q[6],
        "options": [check_var_for_indicator(q[7], False),check_var_for_indicator(q[8], False),check_var_for_indicator(q[9], False),check_var_for_indicator(q[10], False)],
        "difficulty": q[11]
    }

    #here it assumes the first option is always the correct one.

    if question_to_send['answer'] == "":
        question_to_send['answer'] = solve_question(question_to_send['method'], session['current_question_params'].pop(0))
        question_to_send['options'][0] = question_to_send['answer']

    
    while question_to_send['options'][0] == question_to_send['options'][1]:
        question_to_send['options'][1] = check_var_for_indicator(q[8], False)
        while question_to_send['options'][1] == question_to_send['options'][2] or question_to_send['options'][0] == question_to_send['options'][2]:
            question_to_send['options'][2] = check_var_for_indicator(q[9], False)
            while question_to_send['options'][0] == question_to_send['options'][3] or question_to_send['options'][1] == question_to_send['options'][3] or question_to_send['options'][2] == question_to_send['options'][3]:
                question_to_send['options'][3] = check_var_for_indicator(q[10], False)

    random.shuffle(question_to_send['options'])

    return question_to_send
def makeTestOrder(subtopic, signtitles, examTemplate=None):
    if examTemplate is None:
        examTemplate = [0] * 12

    testOrder = []

    for robotType in examTemplate:
        if robotType == 9:
            if signtitles:
                testOrder.append({"type": "sign", "title": signtitles.pop(0)})
            continue

        # store template only (NOT full question yet)
        testOrder.append({
            "type": "question_template",
            "robotType": robotType,
            "subtopic": subtopic
        })

    return testOrder
def makeDemoTest():
    template = [9, 9, 9, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9]
    signtitles = ["Welcome", "SDLC Steps Part 1", "SDLC Steps Part 2", "SDLC Steps Part 3", "Demo Finish"]
    return makeTestOrder("sd phases", signtitles, template)


def get_username_from_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        username = cursor.execute('SELECT username FROM User WHERE id = ?', (user_id,)).fetchone()[0]
        return username
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()
def convert_seconds_to_format(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"











#                   APP ROUTES!

# starts by loading index.html, the home page at the root url (that is what the bare '/' means)











@app.before_request
def session_timeout(): #setting up a limit so that session times out after 2 hours of inactivity
    session.permanent = True 
    app.permanent_session_lifetime = datetime.timedelta(hours=2)
    session.modified = True

@app.route('/')
def home():
    init_sessionData()
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

        if uemail.endswith("@det.nsw.edu.au"):
            alevel = "teacher"
        elif uemail.endswith("@education.nsw.gov.au"):
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
                session['incorrectAttempts'] = 0
                return redirect(url_for('loggedinhomepage', loggedIn = True))
            else:
                try:
                    session['incorrectAttempts'] += 1
                    if session['incorrectAttempts'] >= 5:
                        timePenalty = (session['incorrectAttempts'] - 4) * 30
                        session['lastFail'] = datetime.datetime.now(tz=utc_plus_10)
                        if (datetime.datetime.now(tz=utc_plus_10) - session.get('lastFail')).total_seconds() < timePenalty:
                            return render_template('login.html', loginTimeout = (datetime.datetime.now(tz=utc_plus_10) - session['lastFail']).total_seconds())
                        else:
                            return render_template('login.html', error=f"Invalid username or password! Note that both fields are case-sensitive. {session['incorrectAttempts']}/5 incorrect attempts.")
                    else:
                        return render_template('login.html', error=f"Invalid username or password! Note that both fields are case-sensitive. {session['incorrectAttempts']}/5 incorrect attempts.")
                except Exception as e:
                    session['incorrectAttempts'] = 1
                    return render_template('login.html', error=f"Invalid username or password! Note that both fields are case-sensitive. {session['incorrectAttempts']}/5 incorrect attempts.")
        except sqlite3.Error as e:
            return render_template('login.html', error="An error occurred. Please try again.")
        finally:
            conn.close()
    if session.get('lastFail') and session.get('incorrectAttempts'):
        if session['incorrectAttempts'] >= 5:
            timePenalty = (session['incorrectAttempts'] - 4) * 30
            if (datetime.datetime.now(tz=utc_plus_10) - session.get('lastFail')).total_seconds() < timePenalty:
                return render_template('login.html', loginTimeout = round(timePenalty - (datetime.datetime.now(tz=utc_plus_10) - session['lastFail']).total_seconds()))
            else:
                return render_template('login.html')
    return render_template('login.html')
@app.route('/logout')
def logout():
        session.clear()
        init_sessionData()
        return redirect(url_for('login'))
@app.route('/loggedinhomepage')
def loggedinhomepage():
    try:
        return render_template('loggedinhomepage.html', username = get_username_from_id(session['user_id']))
    except KeyError:    #when session expires or tries to access the homepage without having logged in
        return redirect(url_for('home'))


@app.route('/check_inactivity', methods=['GET'])
def check_inactivity():
    if 'user_id' in session:
        return jsonify({'status': 'active'})
    else:
        return jsonify({'status': 'inactive'})


@app.route('/preparation', methods=['GET', 'POST'])
def preparation():
    subtopic = ""
    if request.method == 'POST':
        if session['user_id']:
            subtopic = request.form['subtopic']
            if subtopic == "all":
                pass
        else:
            #it should return the demo quiz
            session['test_order'] = makeDemoTest()
            session['current_question_index'] = 0
    if subtopic == "":
        return render_template('preparation.html')
    else:
        return render_template('preparation.html', subtopic = subtopic)

@app.route('/dashboard')
def dashboard():
    pass


@app.route('/signpage')
def signpage():
    data = session.get('current_question_data')
    return render_template(
        'signpage.html',
        signtitle=data["title"],
        signimage=data["image"],
        signtext=data["text"]
    )

@app.route('/testpage')
def testpage():
    try:
        data = session.get('current_question_data')

        difficulty = data["difficulty"]
        time_limit = 30 if difficulty <= 4 else 45 if difficulty <= 7 else 60

        session['qtimerstart'] = datetime.datetime.now(tz=utc_plus_10)

        if session.get('qtimerstart') and session.get('difficulty'):
            difficulty = data["difficulty"]
            time_limit = 30 if difficulty <= 4 else 45 if difficulty <= 7 else 60
            if (datetime.datetime.now(tz=utc_plus_10) - session.get('qtimerstart')).total_seconds() < time_limit:
                random.shuffle(data["options"])
                return render_template(
                    'testpage.html',
                    robotType=data["robotType"],
                    questionText=data["text"],
                    questionInfo=data["info"],
                    questionImage=data["image"],
                    i1=data["options"][0],
                    i2=data["options"][1],
                    i3=data["options"][2],
                    i4=data["options"][3],
                    timer=convert_seconds_to_format(round(time_limit - (datetime.datetime.now(tz=utc_plus_10) - session['qtimerstart']).total_seconds())),
                    qindex = session.get('question_number_within_test', 1)
                    )
            else:
                return redirect(url_for('checkanswer'))
        
        return render_template(
            'testpage.html',
            robotType=data["robotType"],
            questionText=data["text"],
            questionInfo=data["info"],
            questionImage=data["image"],
            i1=data["options"][0],
            i2=data["options"][1],
            i3=data["options"][2],
            i4=data["options"][3],
            timer=convert_seconds_to_format(round(time_limit - (datetime.datetime.now(tz=utc_plus_10) - session['qtimerstart']).total_seconds())),
            qindex = session.get('question_number_within_test', 1)
            )
    except Exception as e:
        return redirect(url_for('home')) #when an exception like this is thrown,
        #it is assumed that it is because the user is timed out, which sends them back to the landing page.

@app.route('/checkanswer', methods=['GET', 'POST'])
def checkanswer():
    try:
        try:
            answer = request.form["answer"]
        except Exception as e:
            #print("I am the source of all your problems!")
            return redirect(url_for('next_question'))

        data = session.get('current_question_data')
        if not data:
            return redirect(url_for('loggedinhomepage'))

        correct = str(data["answer"]).strip().lower()
        given = str(answer).strip().lower()

        is_correct = int(given == correct)

        question_data = session['current_question_data']
        qnum = session['question_number_within_test']

        if question_data.get("type") == "question":
            #user can also be logged out doing the demo quiz.

            if session.get('user_id'):
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO QuizResult (
                        user_id, question_id, quiz_index,
                        given_answer, correct_answer,
                        is_correct, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session['user_id'],
                    question_data.get("id"),
                    qnum,
                    answer,
                    data["answer"],
                    is_correct,
                    datetime.datetime.now(tz=utc_plus_10).isoformat()
                ))

                conn.commit()
                conn.close()

            qverdict = "×"
            if is_correct:
                session['quiz_score'] = session.get('quiz_score', 0) + 1
                qverdict = "✓"

            session['current_question_params'] = []

            return render_template(
                'testpage.html',
                feedback=(
                    "Congrats! You deactivated the robot!"
                    if is_correct
                    else f"The robot escaped... The answer was {data['answer']}"
                ),
                robotType=question_data['robotType'],
                i1=question_data['options'][0],
                i2=question_data['options'][1],
                i3=question_data['options'][2],
                i4=question_data['options'][3],
                questionText=question_data['text'],
                questionImage=question_data['image'],
                questionInfo=question_data['info'],
                qindex=qnum,
                timedout=True,
                verdict=qverdict
            )
        else:
            #print(f"It's nothing personal, it's just business... {question_data.get('type')}")
            return redirect(url_for('home'))
                
    except Exception as e:
        #print(f"You feeling exceptional yet? here is {e}")
        return redirect(url_for('home'))

@app.route('/start_test', methods=['GET', 'POST'])
def start_test():
    try:
        subtopic = request.form.get('subtopic', 'sd phases')

        if not session.get('user_id'):
            session['test_order'] = makeDemoTest()
        else:
            session['test_order'] = makeTestOrder(subtopic, ["Welcome", "Demo Finish"])
            session['quiz_score'] = 0
            session['quiz_total'] = len(session['test_order'])

        session['current_question_index'] = 0
        session['question_number_within_test'] = 0
        return redirect(url_for('next_question'))
    except Exception as e:
        #print(f"Error starting test: {e}")
        return redirect(url_for('login'))

@app.route('/next_question', methods = ['GET', 'POST'])
def next_question():
    order = session.get('test_order', [])
    i = session.get('current_question_index', 0)
    #print(f"There are {len(order)} items in test_order. We are on {i}. The question number should also say {session.get('question_number_within_test', -1) + 1}.")

    if i >= len(order):
        if session.get('user_id'):
            conn = get_db()
            cursor = conn.cursor()
            teacher = cursor.execute('SELECT teacherid from User WHERE id=?', session.get('user_id'))

            cursor.execute('''
                INSERT INTO Marks (testtakerid, teacherid, quiznumber, score, totalmarks)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session['user_id'],
                teacher,
                1,
                session.get('quiz_score', 0),
                session.get('quiz_total', 0)
            ))
            print("Logged Test")
            conn.commit()
            conn.close()
        print("Completed test. Going home now...")
        return redirect(url_for('loggedinhomepage'))

    item = order[i]
    session['current_question_index'] += 1
    #print(f"session question index incremented by 1 from {session.get('current_question_index') - 1} to {session.get('current_question_index')}")

    if item["type"] == "sign":
        session['current_question_data'] = get_sign(item["title"])
        return redirect(url_for('signpage'))

    if item["type"] == "question_template":
        conn = get_db()
        cursor = conn.cursor()
        session['question_number_within_test'] = 1 + session.get('question_number_within_test')
        #print(f"session question number within test incremented by 1 from {session.get('question_number_within_test') - 1} to {session.get('question_number_within_test')}")

        if item["subtopic"] == "all":
            qid = cursor.execute(
                "SELECT id FROM Question WHERE qquestiontype=? ORDER BY RANDOM() LIMIT 1",
                (item["robotType"])
              ).fetchone()
        else:
            qid = cursor.execute(
                "SELECT id FROM Question WHERE qquestiontype=? AND qsubtopic=? ORDER BY RANDOM() LIMIT 1",
                (item["robotType"], item["subtopic"])
              ).fetchone()

        conn.close()

        if not qid:
            print("Error: There was some trouble finding questions for you...")
            return redirect(url_for('next_question'))

        session['current_question_data'] = generate_question_by_id(qid[0])
        return redirect(url_for('testpage'))

@app.route('/qtimerexpired', methods=['POST'])
def qtimerexpired():
    data = session.get('current_question_data')
    return jsonify({
        "status": "timeout",
        "correct_answer": data["answer"]
    })



if __name__ == '__main__':
    with app.app_context():
      purge_db()
      init_db()
      createDummyUser()
      init_questions()
      init_signs()
      #auto_github_commit('./', 'Testing automatic update from app.py')
      app.run(debug=True)
#this runs when testing/debugging

#if __name__ == "__main__":
#    init_db()
#    createDummyUser()
#    init_questions()
#    init_signs()
#    app.run(host="0.0.0.0", port=5000, debug=False)
#hopefully this is what will run when the webiste is hosted for real.
