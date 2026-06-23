#imports
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import bcrypt
import datetime
import sqlite3
import random
import string
from git import Repo



#initialising Flask
app = Flask(__name__)
app.secret_key = 'sen_secret_key' #os.environ['SECRET_KEY']

DB_PATH = "users.db"
COURSE_SUBTOPICS = ["sd phases", "datatypes", "errors", "algorithmic thinking", "debugging"]


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
def column_exists(cursor, table, column):
    return column in [row[1] for row in cursor.execute(f'PRAGMA table_info({table})').fetchall()]
def add_column_if_missing(cursor, table, column, definition):
    if not column_exists(cursor, table, column):
        cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
def generate_unique_teacher_code(cursor):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "T-" + "".join(random.choice(alphabet) for _ in range(6))
        if not cursor.execute('SELECT id FROM User WHERE selfcode = ?', (code,)).fetchone():
            return code
def ensure_teacher_selfcodes(cursor):
    teachers_without_codes = cursor.execute(
        'SELECT id FROM User WHERE accesslevel = "teacher" AND (selfcode IS NULL OR selfcode = "")'
    ).fetchall()
    for teacher in teachers_without_codes:
        cursor.execute('UPDATE User SET selfcode = ? WHERE id = ?', (generate_unique_teacher_code(cursor), teacher[0]))

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
            teachercode TEXT,
            selfcode TEXT UNIQUE

        )
    ''')
    add_column_if_missing(cursor, 'User', 'teachercode', 'TEXT')
    add_column_if_missing(cursor, 'User', 'selfcode', 'TEXT')
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
            totalmarks INTEGER,
            subtopic TEXT
        )
    ''')
    add_column_if_missing(cursor, 'Marks', 'subtopic', 'TEXT')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Signs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signtitle TEXT NOT NULL UNIQUE,
            signimageurl TEXT,
            signtext TEXT NOT NULL
            
        )                          
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS AssignedCourses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subtopic TEXT NOT NULL,
            assigned_by INTEGER,
            assigned_at TEXT,
            UNIQUE(student_id, subtopic),
            FOREIGN KEY (student_id) REFERENCES User(id),
            FOREIGN KEY (assigned_by) REFERENCES User(id)
        )
    ''')
    #signtitles are unique


    if column_exists(cursor, 'User', 'teacherid'):
        rows_to_migrate = cursor.execute('''
            SELECT student.id, teacher.selfcode
            FROM User AS student
            JOIN User AS teacher ON student.teacherid = teacher.id
            WHERE student.teachercode IS NULL OR student.teachercode = ""
        ''').fetchall()
        for student_id, teacher_code in rows_to_migrate:
            if teacher_code:
                cursor.execute('UPDATE User SET teachercode = ? WHERE id = ?', (teacher_code, student_id))

    if column_exists(cursor, 'User', 'assignedcourses'):
        assigned_rows = cursor.execute('SELECT id, assignedcourses FROM User WHERE assignedcourses IS NOT NULL AND assignedcourses != ""').fetchall()
        for student_id, assignedcourses in assigned_rows:
            for course in assignedcourses.split(','):
                course = course.strip()
                if course:
                    cursor.execute('''
                        INSERT OR IGNORE INTO AssignedCourses (student_id, subtopic, assigned_at)
                        VALUES (?, ?, ?)
                    ''', (student_id, course, datetime.datetime.now(tz=utc_plus_10).isoformat()))

    ensure_teacher_selfcodes(cursor)

    conn.commit()
    conn.close()
def purge_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS User')
    cursor.execute('DROP TABLE IF EXISTS Question')
    cursor.execute('DROP TABLE IF EXISTS Marks')
    cursor.execute('DROP TABLE IF EXISTS Signs')
    cursor.execute('DROP TABLE IF EXISTS QuizResult')
    cursor.execute('DROP TABLE IF EXISTS AssignedCourses')
    conn.commit()
    conn.close()
def createDummyUser():
    conn = get_db()
    cursor = conn.cursor()
    dummy_password = bcrypt.hashpw("examplepassword123!".encode(), bcrypt.gensalt()).decode()
    teacher1code = generate_unique_teacher_code(cursor)
    data1 = ("exampleuser1", dummy_password, "example.user@det.nsw.edu.au", "teacher", teacher1code)
    data2 = ("exampleuser2", dummy_password, "example.user2@education.nsw.gov.au", "student", teacher1code)
    try:
        existingid = cursor.execute('SELECT id FROM User WHERE email = ?', (data1[2],)).fetchone()
        if existingid:
            ensure_teacher_selfcodes(cursor)
            print("Dummy user already exists, no need to create.")
            return
        else:
            cursor.execute('INSERT INTO User(username, password, email, accesslevel, selfcode) VALUES (?, ?, ?, ?, ?)', data1)
            cursor.execute('INSERT INTO User(username, password, email, accesslevel, teachercode) VALUES (?, ?, ?, ?, ?)', data2)
            return
    except sqlite3.Error as e:
        print(f"Database error {e}. Could not add dummy users.")
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
    global COURSE_SUBTOPICS, senPhases, eg_things_done_in_sen_phases, egstrings, glossaryTerms, examplesOfTerms


    #example integers and decimals are randomised using the random module
    if whatAreaWordIsWantedFrom == "subtopic":
        if specificIndex is not None and 0 <= specificIndex < len(COURSE_SUBTOPICS):
            return COURSE_SUBTOPICS[specificIndex]
        return random.choice(COURSE_SUBTOPICS)
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
        #the different subtopics for the sen thunder mantles (fundamentals) are as follows: "sd phases", "algorithmic thinking", "datatypes", "errors", "debugging"

        fourOptionsQuestions = [
            #phases but they are demo questions only.
            {
                "subtopic": "demo",
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
                "subtopic": "demo",
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
                "subtopic": "datatypes",
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
                "subtopic": "datatypes",
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
                "subtopic": "datatypes",
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
                "subtopic": "datatypes",
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

        additionalQuestions = [ #arranged by subtopic
            #sd phases
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which SDLC phase focuses on gathering user needs and documenting what the system must do?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "requirements",
                "item1": "requirements",
                "item2": "development",
                "item3": "installation",
                "item4": "maintenance",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which SDLC phase turns broad requirements into detailed measurable specifications?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "specifications",
                "item1": "specifications",
                "item2": "testing & debugging",
                "item3": "integration",
                "item4": "maintenance",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which SDLC phase involves creating algorithms, flowcharts and user interface plans before coding?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "design",
                "item1": "design",
                "item2": "installation",
                "item3": "requirements",
                "item4": "integration",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which SDLC phase is mainly concerned with writing the software code?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "development",
                "item1": "development",
                "item2": "requirements",
                "item3": "maintenance",
                "item4": "specifications",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which SDLC phase combines separately developed modules into a complete system?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "integration",
                "item1": "integration",
                "item2": "design",
                "item3": "installation",
                "item4": "requirements",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which SDLC phase checks the software against requirements and locates errors?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "testing & debugging",
                "item1": "testing & debugging",
                "item2": "development",
                "item3": "specifications",
                "item4": "installation",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which SDLC phase deploys the finished software into the user's working environment?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "installation",
                "item1": "installation",
                "item2": "requirements",
                "item3": "design",
                "item4": "testing & debugging",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "Which SDLC phase continues after deployment to fix issues and add improvements?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "maintenance",
                "item1": "maintenance",
                "item2": "requirements",
                "item3": "integration",
                "item4": "development",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "What is a functional requirement?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "A statement of what the system must do",
                "item1": "A statement of what the system must do",
                "item2": "A rule about the programming language syntax",
                "item3": "A description of the company budget only",
                "item4": "A list of unrelated test data",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "sd phases",
                "qinfotext": "",
                "qquestiontext": "What is a non-functional requirement?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "A quality or constraint such as speed, security or reliability",
                "item1": "A quality or constraint such as speed, security or reliability",
                "item2": "A line of source code that calls a function",
                "item3": "A random value selected during testing",
                "item4": "A diagram that only shows colours",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            
            #datatypes
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which data type stores whole numbers without a fractional component?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "integer",
                "item1": "integer",
                "item2": "real",
                "item3": "string",
                "item4": "boolean",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which data type stores text as a sequence of characters?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "string",
                "item1": "string",
                "item2": "integer",
                "item3": "boolean",
                "item4": "real",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which data type stores only true or false?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "boolean",
                "item1": "boolean",
                "item2": "char",
                "item3": "integer",
                "item4": "record",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which data type is best for a single letter such as 'A'?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "char",
                "item1": "char",
                "item2": "boolean",
                "item3": "array",
                "item4": "real",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which number system uses only the digits 0 and 1?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "binary",
                "item1": "binary",
                "item2": "decimal",
                "item3": "hexadecimal",
                "item4": "real",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which number system uses base 16?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "hexadecimal",
                "item1": "hexadecimal",
                "item2": "binary",
                "item3": "decimal",
                "item4": "boolean",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which data structure stores values in order and accesses them by index?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "array",
                "item1": "array",
                "item2": "boolean",
                "item3": "syntax error",
                "item4": "maintenance phase",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which data structure groups related fields that may have different data types?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "record",
                "item1": "record",
                "item2": "stack",
                "item3": "single precision floating point",
                "item4": "breakpoint",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which data structure follows Last In, First Out?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "stack",
                "item1": "stack",
                "item2": "queue",
                "item3": "record",
                "item4": "tree",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "datatypes",
                "qinfotext": "",
                "qquestiontext": "Which data structure stores data as key-value pairs?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "dictionary",
                "item1": "dictionary",
                "item2": "array",
                "item3": "sequential file",
                "item4": "boolean",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            
            #algorithmic thinking
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "",
                "qquestiontext": "Which control structure executes instructions one after another in order?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "sequence",
                "item1": "sequence",
                "item2": "selection",
                "item3": "iteration",
                "item4": "backtracking",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "",
                "qquestiontext": "Which control structure chooses between different paths based on a condition?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "selection",
                "item1": "selection",
                "item2": "sequence",
                "item3": "iteration",
                "item4": "abstraction",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "",
                "qquestiontext": "Which control structure repeats instructions while a condition is met?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "iteration",
                "item1": "iteration",
                "item2": "selection",
                "item3": "sequence",
                "item4": "logic paradigm",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "",
                "qquestiontext": "Which technique breaks a large problem into smaller subproblems?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "divide & conquer",
                "item1": "divide & conquer",
                "item2": "single line stepping",
                "item3": "installation",
                "item4": "syntax checking",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "",
                "qquestiontext": "Which technique explores possible solutions and reverses decisions when a path fails?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "backtracking",
                "item1": "backtracking",
                "item2": "iteration",
                "item3": "installation",
                "item4": "hosting",
                "qanswerspecialmethod": "",
                "difficulty": 4
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "",
                "qquestiontext": "What is pseudocode used for?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "Describing an algorithm in structured human-readable steps",
                "item1": "Describing an algorithm in structured human-readable steps",
                "item2": "Compiling a program directly into machine code",
                "item3": "Replacing all testing and debugging",
                "item4": "Storing encrypted passwords",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "",
                "qquestiontext": "What do flowcharts show?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "The sequence, decisions, inputs, outputs and flow of control in an algorithm",
                "item1": "The sequence, decisions, inputs, outputs and flow of control in an algorithm",
                "item2": "Only the colours used in a user interface",
                "item3": "Only the names of database tables",
                "item4": "The teacher assigned to a student",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "",
                "qquestiontext": "Which term means simplifying complexity by focusing on essential features?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "abstraction",
                "item1": "abstraction",
                "item2": "runtime error",
                "item3": "hexadecimal",
                "item4": "maintenance",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "FOR i FROM 1 TO 3\n    DISPLAY i\nNEXT i",
                "qquestiontext": "Which control structure is shown in this pseudocode?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "iteration",
                "item1": "iteration",
                "item2": "selection",
                "item3": "sequence only",
                "item4": "backtracking only",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "algorithmic thinking",
                "qinfotext": "IF mark >= 50 THEN\n    DISPLAY 'Pass'\nELSE\n    DISPLAY 'Try again'\nENDIF",
                "qquestiontext": "Which control structure is shown in this pseudocode?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "selection",
                "item1": "selection",
                "item2": "iteration",
                "item3": "divide & conquer",
                "item4": "sequence only",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            
            #errors
            {
                "subtopic": "errors",
                "qinfotext": "",
                "qquestiontext": "Which error is caused by code that breaks the grammar rules of a programming language?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "syntax error",
                "item1": "syntax error",
                "item2": "logic error",
                "item3": "runtime error",
                "item4": "maintenance error",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "errors",
                "qinfotext": "",
                "qquestiontext": "Which error occurs when a program runs but produces the wrong result?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "logic error",
                "item1": "logic error",
                "item2": "syntax error",
                "item3": "runtime error",
                "item4": "compile-time spelling",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "errors",
                "qinfotext": "",
                "qquestiontext": "Which error occurs while the program is executing and may stop it unexpectedly?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "runtime error",
                "item1": "runtime error",
                "item2": "logic error",
                "item3": "syntax error",
                "item4": "design phase",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "errors",
                "qinfotext": "total = 10 / 0",
                "qquestiontext": "What type of error is most likely caused by this line when it runs?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "runtime error",
                "item1": "runtime error",
                "item2": "syntax error",
                "item3": "requirements error",
                "item4": "no error",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "errors",
                "qinfotext": "IF score > 50 THEN DISPLAY 'Fail'",
                "qquestiontext": "If the program runs but uses the wrong comparison outcome, what kind of error is it?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "logic error",
                "item1": "logic error",
                "item2": "syntax error",
                "item3": "runtime error",
                "item4": "data type",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "errors",
                "qinfotext": "",
                "qquestiontext": "Which testing data checks values at the edge of an allowed range?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "boundary data",
                "item1": "boundary data",
                "item2": "random unrelated data",
                "item3": "only invalid data",
                "item4": "maintenance data",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "errors",
                "qinfotext": "",
                "qquestiontext": "Which testing data should be accepted by the program?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "valid data",
                "item1": "valid data",
                "item2": "invalid data",
                "item3": "out-of-range data",
                "item4": "syntax data",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "errors",
                "qinfotext": "",
                "qquestiontext": "Which testing data should be rejected by the program?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "invalid data",
                "item1": "invalid data",
                "item2": "valid data",
                "item3": "normal data",
                "item4": "expected data",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "errors",
                "qinfotext": "",
                "qquestiontext": "What does validation do?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "Checks that entered data follows required rules",
                "item1": "Checks that entered data follows required rules",
                "item2": "Proves that the data is true in the real world",
                "item3": "Automatically designs the user interface",
                "item4": "Deletes all incorrect code",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "errors",
                "qinfotext": "",
                "qquestiontext": "What does verification check?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "That data has been copied or entered accurately",
                "item1": "That data has been copied or entered accurately",
                "item2": "That an algorithm has no loops",
                "item3": "That a teacher code is always blank",
                "item4": "That every runtime error is impossible",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            
            #debugging
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "What is a breakpoint used for?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "Pausing execution so program state can be inspected",
                "item1": "Pausing execution so program state can be inspected",
                "item2": "Deleting variables from memory permanently",
                "item3": "Skipping the testing phase",
                "item4": "Changing decimal numbers to hexadecimal",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "What is single line stepping?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "Executing a program one statement at a time",
                "item1": "Executing a program one statement at a time",
                "item2": "Running all code without stopping",
                "item3": "Writing comments on every line",
                "item4": "Opening one file at a time",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "What is a watch used for in debugging?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "Monitoring the value of a variable or expression",
                "item1": "Monitoring the value of a variable or expression",
                "item2": "Timing how long a student takes on a quiz",
                "item3": "Replacing a database table",
                "item4": "Drawing a structure chart",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "What is a debugging output statement?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "A temporary statement used to display values or program flow",
                "item1": "A temporary statement used to display values or program flow",
                "item2": "A permanent password hashing method",
                "item3": "A diagram showing only teacher codes",
                "item4": "A rule for naming files",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "Which tool feature lets a developer inspect variables after stopping at a chosen line?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "breakpoint",
                "item1": "breakpoint",
                "item2": "hexadecimal",
                "item3": "record",
                "item4": "installation",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "What is the main purpose of debugging?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "Finding and correcting errors in a program",
                "item1": "Finding and correcting errors in a program",
                "item2": "Avoiding all testing",
                "item3": "Converting every string into an integer",
                "item4": "Assigning students to courses",
                "qanswerspecialmethod": "",
                "difficulty": 1
            },
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "Why might a developer trace through code manually?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "To follow variable changes and locate where behaviour becomes incorrect",
                "item1": "To follow variable changes and locate where behaviour becomes incorrect",
                "item2": "To make the program run without a computer",
                "item3": "To remove the need for algorithms",
                "item4": "To choose a random access level",
                "qanswerspecialmethod": "",
                "difficulty": 3
            },
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "What is an IDE?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "Software that provides tools such as an editor, compiler and debugger",
                "item1": "Software that provides tools such as an editor, compiler and debugger",
                "item2": "A type of runtime error",
                "item3": "A base-2 number system",
                "item4": "A student assignment table",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "Which practice helps locate a bug by printing variable values during execution?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "using debugging output statements",
                "item1": "using debugging output statements",
                "item2": "removing all selection statements",
                "item3": "changing every integer to a string",
                "item4": "skipping validation",
                "qanswerspecialmethod": "",
                "difficulty": 2
            },
            {
                "subtopic": "debugging",
                "qinfotext": "",
                "qquestiontext": "What should a developer do after finding the location of an error?",
                "qassociatedimage": "",
                "qquestiontype": 0,
                "qcorrectanswer": "Correct the code and retest the program",
                "item1": "Correct the code and retest the program",
                "item2": "Delete all test cases",
                "item3": "Ignore the error if it is intermittent",
                "item4": "Change the project subtopic",
                "qanswerspecialmethod": "",
                "difficulty": 2
            }
        ]

        fourOptionsQuestions.extend(additionalQuestions)

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
            ["SDLC Steps Part 3", "", "<h2>Installation:</h2><p> \n Deploying the finished software into the client's working environment (e.g. installing it on their servers or computers). This includes setting up databases and configuring networks. \n\n </p><h2>Maintenance:</h2><p> \n Ongoing activity after deployment to keep the system operational and relevant. Includes fixing bugs (corrective), adapting to new environments (adaptive), and adding new features (perfective).</p>"]
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
def solve_question(qsolvemethod, params):
    global senPhases, eg_things_done_in_sen_phases, egstrings, glossaryTerms, examplesOfTerms
    try:
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
    except IndexError as e:
        return "None of these"
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
    return makeTestOrder("demo", signtitles, template)


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
def is_logged_in():
    return session.get('user_id') is not None
def get_assigned_courses(student_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        return [
            row[0] for row in cursor.execute(
                'SELECT subtopic FROM AssignedCourses WHERE student_id = ? ORDER BY subtopic',
                (student_id,)
            ).fetchall()
        ]
    finally:
        conn.close()
def assign_course_to_student(student_id, subtopic, assigned_by=None):
    if subtopic not in COURSE_SUBTOPICS:
        return False
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO AssignedCourses (student_id, subtopic, assigned_by, assigned_at)
            VALUES (?, ?, ?, ?)
        ''', (student_id, subtopic, assigned_by, datetime.datetime.now(tz=utc_plus_10).isoformat()))
        conn.commit()
        return True
    finally:
        conn.close()
def remove_assigned_course(student_id, subtopic):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM AssignedCourses WHERE student_id = ? AND subtopic = ?', (student_id, subtopic))
        conn.commit()
    finally:
        conn.close()
def get_teacher_for_student(cursor, teachercode):
    if not teachercode:
        return None
    return cursor.execute(
        'SELECT id, username, selfcode FROM User WHERE selfcode = ? AND accesslevel = "teacher"',
        (teachercode,)
    ).fetchone()











#                   APP ROUTES!

# starts by loading index.html, the home page at the root url (that is what the bare '/' means)











@app.before_request
def session_timeout(): #setting up a limit so that session times out after 1 hour of inactivity
    session.permanent = True 
    app.permanent_session_lifetime = datetime.timedelta(hours=1)
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
            selfcode = generate_unique_teacher_code(cursor) if alevel == "teacher" else None
            cursor.execute(
                'INSERT INTO User (username, password, email, accesslevel, selfcode, teachercode) VALUES (?, ?, ?, ?, ?, ?)',
                (uname, hashed_password, uemail, alevel, selfcode, None)
            )
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
        user_id = session['user_id']
        conn = get_db()
        cursor = conn.cursor()
        user = cursor.execute('SELECT username, accesslevel FROM User WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if not user:
            return redirect(url_for('home'))
        assigned_courses = get_assigned_courses(user_id) if user[1] == 'student' else []
        return render_template(
            'loggedinhomepage.html',
            username=user[0],
            accesslevel=user[1],
            assigned_courses=assigned_courses,
            course_subtopics=COURSE_SUBTOPICS
        )
    except (KeyError, TypeError):    #when session expires or tries to access the homepage without having logged in
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
        if session.get('user_id'):
            subtopic = request.form['subtopic']
            if subtopic == "all":
                pass
        else:
            #it should return the demo quiz
            session['test_order'] = makeDemoTest()
            session['current_question_index'] = 0
    if subtopic == "":
        return render_template('preparation.html', loggedin = is_logged_in())
    else:
        return render_template('preparation.html', subtopic = subtopic, loggedin = is_logged_in())
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    try:
        user_id = session['user_id']
        user = cursor.execute('SELECT username, accesslevel, teachercode, selfcode FROM User WHERE id = ?', (user_id,)).fetchone()

        if not user:
            return redirect(url_for('login'))

        username, accesslevel, teachercode, selfcode = user

        if accesslevel == 'teacher':
            students = [
                {
                    "id": row[0],
                    "username": row[1],
                    "assigned_courses": get_assigned_courses(row[0])
                }
                for row in cursor.execute(
                    'SELECT id, username FROM User WHERE teachercode = ? AND accesslevel = "student" ORDER BY username',
                    (selfcode,)
                ).fetchall()
            ]
            student_count = len(students)
            return render_template(
                'dashboard.html',
                username=username,
                accesslevel=accesslevel,
                user_id=user_id,
                selfcode=selfcode,
                student_count=student_count,
                students=students,
                course_subtopics=COURSE_SUBTOPICS
            )

        elif accesslevel == 'student':
            teacher_row = get_teacher_for_student(cursor, teachercode)
            teacher = {"id": teacher_row[0], "username": teacher_row[1], "selfcode": teacher_row[2]} if teacher_row else None
            scores = [
                {"quiznumber": row[0], "score": row[1], "totalmarks": row[2], "subtopic": row[3]} for row in cursor.execute(
                    'SELECT quiznumber, score, totalmarks, subtopic FROM Marks WHERE testtakerid = ? ORDER BY id DESC LIMIT 20',
                    (user_id,)
                ).fetchall()
            ]
            assigned_courses = get_assigned_courses(user_id)

            return render_template(
                'dashboard.html',
                username=username,
                accesslevel=accesslevel,
                user_id=user_id,
                teacher=teacher,
                scores=scores,
                assigned_courses=assigned_courses,
                verified=request.args.get('verified'),
                course_subtopics=COURSE_SUBTOPICS
            )

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return redirect(url_for('home'))
    finally:
        conn.close()
@app.route('/adminzone', methods=['GET'])
def adminzone():
    try:
        if 'user_id' not in session:
            return redirect(url_for('login'))

        conn = get_db()
        cursor = conn.cursor()
        user = cursor.execute('SELECT accesslevel FROM User WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()

        if user and user[0] == 'host':
            return render_template('adminzone.html')
        else:
            return redirect(url_for('loggedinhomepage'))
    except Exception as e:
        print(f"Error in adminzone: {e}")
        return redirect(url_for('home'))

@app.route('/add_q_to_db', methods=['GET', 'POST'])
def add_q_to_db():
    if request.method == 'POST':
        subtopic = request.form.get('subtopic')
        info = request.form.get('info')
        question = request.form.get('question')
        image = request.form.get('image')
        robotType = request.form.get('robotType')
        answer = request.form.get('answer')
        i1 = request.form.get('i1')
        i2 = request.form.get('i2')
        i3 = request.form.get('i3')
        i4 = request.form.get('i4')
        answermethod = request.form.get('answermethod')
        difficulty = request.form.get('difficulty')
        adminconfirm = request.form.get('adminconfirm')

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Verify admin password
            admin = cursor.execute('SELECT password FROM User WHERE id = ?', (session['user_id'],)).fetchone()
            if admin and bcrypt.checkpw(adminconfirm.encode(), admin[0] if isinstance(admin[0], bytes) else admin[0].encode()):
                cursor.execute('''
                    INSERT INTO Question (qsubtopic, qinfotext, qquestiontext, qassociatedimage, qquestiontype, qcorrectanswer, item1, item2, item3, item4, qanswerspecialmethod, difficulty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (subtopic, info, question, image, robotType, answer, i1, i2, i3, i4, answermethod, difficulty))
                conn.commit()
                return jsonify({"status": "success", "message": "Question added successfully!"})
            else:
                return jsonify({"status": "error", "message": "Admin password incorrect!"})
        except Exception as e:
            print(f"Error adding question: {e}")
            return jsonify({"status": "error", "message": "An error occurred while adding the question."})
        finally:
            conn.close()
    return redirect(url_for('loggedinhomepage'))
@app.route('/add_s_to_db', methods=['GET', 'POST'])
def add_s_to_db():
    if request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')
        image = request.form.get('image')
        adminconfirm = request.form.get('adminconfirm')

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Verify admin password
            admin = cursor.execute('SELECT password FROM User WHERE id = ?', (session['user_id'],)).fetchone()
            if admin and bcrypt.checkpw(adminconfirm.encode(), admin[0] if isinstance(admin[0], bytes) else admin[0].encode()):
                cursor.execute('''
                    INSERT INTO Signs (signtitle, signtext, signimageurl)
                    VALUES (?, ?, ?)
                ''', (title, text, image))
                conn.commit()
                return jsonify({"status": "success", "message": "Sign added successfully!"})
            else:
                return jsonify({"status": "error", "message": "Admin password incorrect!"})
        except Exception as e:
            print(f"Error adding sign: {e}")
            return jsonify({"status": "error", "message": "An error occurred while adding the sign."})
        finally:
            conn.close()
    return redirect(url_for('loggedinhomepage'))

@app.route('/assign_teacher', methods=['POST'])
def assign_teacher():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    teacher_code = request.form.get('teacher_code', '').strip().upper()
    conn = get_db()
    cursor = conn.cursor()
    try:
        user = cursor.execute('SELECT accesslevel FROM User WHERE id = ?', (session['user_id'],)).fetchone()
        teacher = get_teacher_for_student(cursor, teacher_code)
        if user and user[0] == 'student' and teacher:
            cursor.execute('UPDATE User SET teachercode = ? WHERE id = ?', (teacher_code, session['user_id']))
            conn.commit()
            return redirect(url_for('dashboard', verified='true'))
        return redirect(url_for('dashboard', verified='false'))
    finally:
        conn.close()
@app.route('/assign_course', methods=['POST'])
def assign_course():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    student_id = request.form.get('student_id')
    subtopic = request.form.get('subtopic')
    conn = get_db()
    cursor = conn.cursor()
    try:
        teacher = cursor.execute('SELECT accesslevel, selfcode FROM User WHERE id = ?', (session['user_id'],)).fetchone()
        student = cursor.execute(
            'SELECT id FROM User WHERE id = ? AND accesslevel = "student" AND teachercode = ?',
            (student_id, teacher[1] if teacher else None)
        ).fetchone()
        if teacher and teacher[0] == 'teacher' and student and subtopic in COURSE_SUBTOPICS:
            cursor.execute('''
                INSERT OR IGNORE INTO AssignedCourses (student_id, subtopic, assigned_by, assigned_at)
                VALUES (?, ?, ?, ?)
            ''', (student_id, subtopic, session['user_id'], datetime.datetime.now(tz=utc_plus_10).isoformat()))
            conn.commit()
    finally:
        conn.close()
    return redirect(url_for('dashboard'))
@app.route('/get_student_scores')
def get_student_scores():
    if 'user_id' not in session:
        return jsonify({'scores': []})

    student_id = request.args.get('student_id')
    conn = get_db()
    cursor = conn.cursor()
    try:
        teacher = cursor.execute('SELECT accesslevel, selfcode FROM User WHERE id = ?', (session['user_id'],)).fetchone()
        if not teacher or teacher[0] != 'teacher':
            return jsonify({'scores': []})
        student = cursor.execute(
            'SELECT id FROM User WHERE id = ? AND accesslevel = "student" AND teachercode = ?',
            (student_id, teacher[1])
        ).fetchone()
        if not student:
            return jsonify({'scores': []})
        scores = [
            {'quiznumber': row[0], 'score': row[1], 'totalmarks': row[2], 'subtopic': row[3] or 'Unknown'}
            for row in cursor.execute(
                'SELECT quiznumber, score, totalmarks, subtopic FROM Marks WHERE testtakerid = ? ORDER BY id DESC LIMIT 20',
                (student_id,)
            ).fetchall()
        ]
        return jsonify({'scores': scores})
    finally:
        conn.close()

@app.route('/signpage')
def signpage():
    data = session.get('current_question_data')
    return render_template(
        'signpage.html',
        signtitle=data["title"],
        signimage=data["image"],
        signtext=data["text"],
        loggedin=is_logged_in()
    )
@app.route('/testpage')
def testpage():
    try:
        data = session.get('current_question_data')

        difficulty = data["difficulty"]
        time_limit = 30 if difficulty <= 4 else 45 if difficulty <= 7 else 60

        if session.get('qtimer_question_id') != data.get("id"):
            session['qtimerstart'] = datetime.datetime.now(tz=utc_plus_10)
            session['qtimer_question_id'] = data.get("id")

        elapsed = (datetime.datetime.now(tz=utc_plus_10) - session.get('qtimerstart')).total_seconds()
        remaining_seconds = max(0, round(time_limit - elapsed))

        if remaining_seconds <= 0:
            return redirect(url_for('checkanswer', timeout=1))
        
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
            timer=convert_seconds_to_format(remaining_seconds),
            timer_seconds=remaining_seconds,
            qindex = session.get('question_number_within_test', 1),
            loggedin=is_logged_in()
            )
    except Exception as e:
        print(f"Hey uh, this might be hard for you to hear but {e}")
        return redirect(url_for('home')) #when an exception like this is thrown,
        #it is assumed that it is because the user is timed out, which sends them back to the landing page.

@app.route('/checkanswer', methods=['GET', 'POST'])
def checkanswer():
    try:
        if request.args.get('timeout') == '1':
            answer = ""
        else:
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
                verdict=qverdict,
                correctAnswer=data['answer'],
                loggedin=is_logged_in()
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
        if subtopic not in COURSE_SUBTOPICS:
            subtopic = 'sd phases'
        session['quiz_subtopic'] = subtopic

        if not session.get('user_id'):
            session['test_order'] = makeDemoTest()
        else:
            session['test_order'] = makeTestOrder(subtopic, ["Welcome", "Demo Finish"])
            session['quiz_score'] = 0
            session['quiz_total'] = len([item for item in session['test_order'] if item.get("type") == "question_template"])

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
            selfid = session.get('user_id')
            user = cursor.execute('SELECT accesslevel, teachercode FROM User WHERE id=?', (selfid,)).fetchone()
            if user and user[0] == "student":
                teacher = get_teacher_for_student(cursor, user[1])
                teacher_id = teacher[0] if teacher else None
                cursor.execute('''
                    INSERT INTO Marks (testtakerid, teacherid, quiznumber, score, totalmarks, subtopic)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    selfid,
                    teacher_id,
                    1,
                    session.get('quiz_score', 0),
                    session.get('quiz_total', 0),
                    session.get('quiz_subtopic')
                ))
                if session.get('quiz_subtopic') in get_assigned_courses(selfid):
                    cursor.execute(
                        'DELETE FROM AssignedCourses WHERE student_id = ? AND subtopic = ?',
                        (selfid, session.get('quiz_subtopic'))
                    )
                conn.commit()
            conn.close()
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
                (item["robotType"],)
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
        session['qtimerstart'] = datetime.datetime.now(tz=utc_plus_10)
        #this is just here to ensure the timer always resets and does not automatically timeout or start at the wrong time.
        session['current_question_data'] = generate_question_by_id(qid[0])
        return redirect(url_for('testpage'))
@app.route('/qtimerexpired', methods=['POST'])
def qtimerexpired():
    data = session.get('current_question_data')
    return jsonify({
        "status": "timeout",
        "correct_answer": data["answer"]
    })



#if __name__ == '__main__':
#    with app.app_context():
#      purge_db()
#      init_db()
#      createDummyUser()
#      init_questions()
#      init_signs()
#      app.run(debug=True)
#this runs when testing/debugging

if __name__ == "__main__":
    init_db()
    createDummyUser()
    init_questions()
    init_signs()
    app.run(host="0.0.0.0", port=5000, debug=False)
# for mac users, you will have to go to System Settings and disable AirPlay Receiver, as this occupies port 5000
