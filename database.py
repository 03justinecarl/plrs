import os
import sqlite3
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'plrs.db')


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (program_id) REFERENCES programs(id)
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            program_id INTEGER,
            role TEXT NOT NULL DEFAULT "student",
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_active DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (program_id) REFERENCES programs(id)
        );
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            difficulty TEXT DEFAULT "medium",
            time_limit INTEGER DEFAULT 300,
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        );
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            choice_a TEXT NOT NULL,
            choice_b TEXT NOT NULL,
            choice_c TEXT NOT NULL,
            choice_d TEXT NOT NULL,
            correct TEXT NOT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        );
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quiz_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        );
        CREATE TABLE IF NOT EXISTS weak_areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            avg_score REAL NOT NULL,
            UNIQUE(user_id, subject_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        );
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            url TEXT,
            description TEXT,
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resource_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (resource_id) REFERENCES resources(id)
        );
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_name TEXT NOT NULL,
            badge_icon TEXT NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS progress_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            week_label TEXT NOT NULL,
            avg_score REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM programs")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    # Programs
    c.executemany("INSERT INTO programs (code, name) VALUES (?, ?)", [
        ('BSIT', 'BS Information Technology'),
        ('BSOA', 'BS Office Administration'),
        ('BSHM', 'BS Hospitality Management'),
        ('BSCPE', 'BS Computer Engineering'),
    ])

    # Subjects
    c.executemany("INSERT INTO subjects (program_id, name) VALUES (?, ?)", [
        (1, 'Web Development'), (1, 'Database Systems'), (1, 'Data Structures'),
        (1, 'Networking'), (1, 'Programming Logic'),
        (2, 'Business Communication'), (2, 'Office Management'), (2, 'Typing Skills'),
        (2, 'Records Management'), (2, 'Spreadsheet Applications'),
        (3, 'Hospitality Management'), (3, 'Food & Beverage Service'),
        (3, 'Tourism Management'), (3, 'Customer Relations'), (3, 'Event Planning'),
        (4, 'Electronics Fundamentals'), (4, 'Digital Logic'),
        (4, 'Computer Hardware'), (4, 'Embedded Systems'), (4, 'Circuit Analysis'),
    ])

    # Admin + sample student
    c.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
              ('Administrator', 'admin@pup.edu.ph', generate_password_hash('admin123'), 'admin'))
    c.execute("""INSERT INTO users (name, student_id, email, password_hash, program_id, role, xp, streak)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              ('Juan Dela Cruz', '2020-00123-MN-0', 'juan@pup.edu.ph',
               generate_password_hash('student123'), 1, 'student', 350, 5))

    # Quizzes
    c.executemany("INSERT INTO quizzes (subject_id, title, difficulty, time_limit) VALUES (?, ?, ?, ?)", [
        (1, 'HTML & CSS Fundamentals', 'easy', 300),
        (2, 'SQL Basics Quiz', 'medium', 300),
        (3, 'Data Structures Remedial Quiz', 'hard', 420),
        (4, 'Networking Basics: OSI Model', 'medium', 300),
        (5, 'Programming Logic & Algorithms', 'medium', 360),
        (6, 'Business Writing Fundamentals', 'easy', 300),
        (8, 'Typing Speed & Accuracy Test', 'easy', 180),
        (11, 'Hospitality Industry Overview', 'easy', 300),
        (13, 'Tourism Geography Quiz', 'medium', 300),
        (16, 'Electronics Fundamentals Quiz', 'easy', 300),
        (17, 'Digital Logic Gates', 'medium', 360),
    ])

    # Questions
    c.executemany("""INSERT INTO questions (quiz_id, question, choice_a, choice_b, choice_c, choice_d, correct)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""", [
        # Quiz 1 – HTML & CSS
        (1, 'What does HTML stand for?', 'HyperText Markup Language', 'HighText Machine Language', 'Hyperlink and Text Markup Language', 'None of the above', 'a'),
        (1, 'Which tag defines an internal style sheet?', '<css>', '<script>', '<style>', '<link>', 'c'),
        (1, 'Which CSS property changes background color?', 'color', 'bgcolor', 'background-color', 'background', 'c'),
        (1, 'What does CSS stand for?', 'Colorful Style Sheets', 'Cascading Style Sheets', 'Computer Style Sheets', 'Creative Style Sheets', 'b'),
        (1, 'Which HTML element defines the document title?', '<meta>', '<head>', '<title>', '<header>', 'c'),
        # Quiz 2 – SQL
        (2, 'Which SQL statement extracts data from a database?', 'OPEN', 'EXTRACT', 'SELECT', 'GET', 'c'),
        (2, 'Which keyword sorts the result set?', 'ORDER BY', 'SORT BY', 'GROUP BY', 'ARRANGE BY', 'a'),
        (2, 'Which operator searches for a specified pattern?', 'LIKE', 'MATCH', 'FIND', 'SEARCH', 'a'),
        (2, 'What does PRIMARY KEY mean?', 'A key that can be NULL', 'Uniquely identifies each row', 'A foreign key reference', 'An encrypted key', 'b'),
        (2, 'Which command deletes a table?', 'DELETE TABLE', 'DROP TABLE', 'REMOVE TABLE', 'ERASE TABLE', 'b'),
        # Quiz 3 – Data Structures
        (3, 'Which structure uses LIFO?', 'Queue', 'Array', 'Stack', 'Linked List', 'c'),
        (3, 'Time complexity of binary search?', 'O(n)', 'O(log n)', 'O(n²)', 'O(1)', 'b'),
        (3, 'Which structure uses FIFO?', 'Stack', 'Queue', 'Tree', 'Graph', 'b'),
        (3, 'A binary tree node has at most how many children?', '1', '3', '2', '4', 'c'),
        (3, 'What is a linked list?', 'A collection of arrays', 'Nodes connected by pointers', 'A tree structure', 'A hash table', 'b'),
        # Quiz 4 – Networking
        (4, 'How many layers does the OSI model have?', '5', '6', '7', '8', 'c'),
        (4, 'Which OSI layer handles routing?', 'Data Link', 'Transport', 'Network', 'Session', 'c'),
        (4, 'What does IP stand for?', 'Internet Protocol', 'Internal Process', 'Information Port', 'Interface Protocol', 'a'),
        (4, 'Which protocol sends email?', 'HTTP', 'FTP', 'SMTP', 'DNS', 'c'),
        (4, 'What is the purpose of a router?', 'Connect same-network devices', 'Route data between networks', 'Amplify signals', 'Filter content', 'b'),
        # Quiz 5 – Programming Logic
        (5, 'What is an algorithm?', 'A programming language', 'A step-by-step problem-solving procedure', 'A type of variable', 'A compiler', 'b'),
        (5, 'Which loop always executes at least once?', 'for', 'while', 'do-while', 'foreach', 'c'),
        (5, 'What is a variable?', 'A fixed value', 'A named storage location', 'A type of function', 'A loop counter', 'b'),
        (5, 'What does if-else represent?', 'A loop structure', 'A function call', 'A conditional structure', 'A class definition', 'c'),
        (5, 'Which is NOT a programming paradigm?', 'Object-Oriented', 'Functional', 'Sequential Logic', 'Procedural', 'c'),
        # Quiz 6 – Business Communication
        (6, 'Correct format for a business letter?', 'Informal and casual', 'Formal with salutation and closing', 'Brief without greeting', 'Handwritten only', 'b'),
        (6, 'Which is a type of business document?', 'Novel', 'Memorandum', 'Poetry', 'Biography', 'b'),
        (6, 'A memorandum is used for?', 'External communication', 'Internal organizational communication', 'Legal contracts', 'Personal notes', 'b'),
        (6, 'A professional email should always include?', 'Emojis and slang', 'Clear subject line and professional tone', 'Attachments only', 'CC to everyone', 'b'),
        (6, 'Correct business greeting?', 'Hey there!', 'What up?', 'Dear Mr./Ms. [Last Name],', 'Yo boss,', 'c'),
        # Quiz 7 – Typing
        (7, 'Standard keyboard layout?', 'AZERTY', 'DVORAK', 'QWERTY', 'COLEMAK', 'c'),
        (7, 'Home row keys (left hand)?', 'QWER', 'ASDF', 'ZXCV', 'UIOP', 'b'),
        (7, 'WPM stands for?', 'Words Per Minute', 'Work Per Module', 'Web Page Management', 'Width Per Margin', 'a'),
        (7, 'Which finger presses the spacebar?', 'Index', 'Ring', 'Thumb', 'Pinky', 'c'),
        (7, 'Proper typing posture?', 'Hunching over keyboard', 'Wrists resting while typing', 'Straight back and elevated wrists', 'Typing with one finger', 'c'),
        # Quiz 8 – Hospitality
        (8, 'Hospitality industry is primarily about?', 'Manufacturing goods', 'Providing service and accommodation', 'Agricultural production', 'Technology development', 'b'),
        (8, 'F&B stands for?', 'Finance and Banking', 'Food and Beverage', 'Front and Back', 'Facilities and Booking', 'b'),
        (8, 'Service recovery means?', 'Recovering lost equipment', 'Fixing a poor guest experience', 'Recovering from illness', 'Backup service system', 'b'),
        (8, 'A concierge is?', 'A chef', 'A housekeeping staff', 'A guest services specialist', 'A security officer', 'c'),
        (8, 'Most important skill in hospitality?', 'Technical programming', 'Customer service and communication', 'Accounting', 'Legal knowledge', 'b'),
        # Quiz 10 – Electronics
        (10, 'Unit of electric current?', 'Volt', 'Watt', 'Ampere', 'Ohm', 'c'),
        (10, "Ohm's Law: V equals?", 'I + R', 'I × R', 'I / R', 'I - R', 'b'),
        (10, 'What does a capacitor store?', 'Magnetic energy', 'Electric charge', 'Light energy', 'Sound energy', 'b'),
        (10, 'A diode allows current to flow in?', 'Both directions', 'Neither direction', 'One direction only', 'Random directions', 'c'),
        (10, 'Function of a resistor?', 'Amplify current', 'Store charge', 'Limit current flow', 'Generate voltage', 'c'),
        # Quiz 11 – Digital Logic
        (11, 'Inputs of a 2-input AND gate?', '1', '2', '3', '4', 'b'),
        (11, 'OR gate output is 0 only when?', 'All inputs are 1', 'All inputs are 0', 'One input is 1', 'Inputs are mixed', 'b'),
        (11, 'NOT gate is also called?', 'Buffer', 'Inverter', 'Amplifier', 'Splitter', 'b'),
        (11, 'In binary, 1 + 1 =?', '2', '10', '11', '01', 'b'),
        (11, 'NAND gate outputs?', 'AND output inverted', 'OR output inverted', 'XOR output', 'NOT output', 'a'),
    ])

    # Resources
    c.executemany("INSERT INTO resources (subject_id, title, type, url, description) VALUES (?, ?, ?, ?, ?)", [
        (1, 'HTML Complete Guide', 'pdf', 'https://developer.mozilla.org/en-US/docs/Web/HTML', 'Comprehensive HTML reference from MDN'),
        (1, 'CSS Flexbox Tutorial', 'video', 'https://www.youtube.com/watch?v=fYq5PXgSsbE', 'Learn CSS Flexbox in 15 minutes'),
        (2, 'SQL Tutorial for Beginners', 'pdf', 'https://www.w3schools.com/sql/', 'Interactive SQL learning from W3Schools'),
        (2, 'Database Design Fundamentals', 'video', 'https://www.youtube.com/watch?v=ztHopE5Wnpc', 'ER diagrams and normalization'),
        (3, 'Trees and Graphs Guide', 'pdf', 'https://www.geeksforgeeks.org/tree-data-structure/', 'Complete guide to tree data structures'),
        (3, 'Data Structures Full Course', 'video', 'https://www.youtube.com/watch?v=RBSGKlAvoiM', 'Full data structures video course'),
        (3, 'Stack and Queue Visualizer', 'activity', 'https://visualgo.net/en/list', 'Interactive visualization tool'),
        (4, 'OSI Model Explained', 'pdf', 'https://www.cloudflare.com/learning/ddos/glossary/open-systems-interconnection-model-osi/', 'Complete OSI model reference'),
        (4, 'Networking Fundamentals', 'video', 'https://www.youtube.com/watch?v=3QhU9jd03a0', 'Network fundamentals crash course'),
        (5, 'Algorithms & Flowcharts', 'pdf', 'https://www.geeksforgeeks.org/introduction-to-algorithms/', 'Introduction to algorithms'),
        (5, 'Programming Logic Tutorial', 'video', 'https://www.youtube.com/watch?v=zOjov-2OZ0E', 'Programming logic and problem solving'),
        (6, 'Business Letter Writing Guide', 'pdf', 'https://www.indeed.com/career-advice/career-development/business-letter-format', 'How to write professional business letters'),
        (8, 'Touch Typing Practice', 'activity', 'https://www.typingclub.com/', 'Free typing practice platform'),
        (10, 'Excel for Beginners', 'video', 'https://www.youtube.com/watch?v=rwbho0CgEAI', 'Microsoft Excel complete beginner guide'),
        (11, 'Hospitality Industry Guide', 'pdf', 'https://www.ahla.com/', 'Hotel & Lodging Association resources'),
        (12, 'Food Safety Fundamentals', 'video', 'https://www.youtube.com/watch?v=eIWGkFSf9sk', 'Food safety and handling basics'),
        (14, 'Customer Service Excellence', 'pdf', 'https://www.serviceskills.com/', 'Customer service training resources'),
        (16, 'Electronics Fundamentals', 'pdf', 'https://www.electronics-tutorials.ws/', 'Complete electronics tutorial'),
        (17, 'Digital Logic Design', 'video', 'https://www.youtube.com/watch?v=M0mx8S05v60', 'Digital logic gates and circuits'),
        (19, 'Arduino for Beginners', 'activity', 'https://www.arduino.cc/en/Tutorial/HomePage', 'Hands-on embedded systems with Arduino'),
    ])

    # Sample scores, weak areas, recommendations, achievements, progress for Juan (user_id=2)
    c.executemany("INSERT INTO scores (user_id, quiz_id, score, total) VALUES (?, ?, ?, ?)", [
        (2, 1, 4, 5), (2, 2, 4, 5), (2, 3, 2, 5), (2, 4, 3, 5), (2, 5, 2, 5),
    ])
    c.executemany("INSERT INTO weak_areas (user_id, subject_id, avg_score) VALUES (?, ?, ?)", [
        (2, 3, 40.0), (2, 5, 40.0),
    ])
    c.executemany("INSERT INTO recommendations (user_id, resource_id) VALUES (?, ?)", [
        (2, 5), (2, 6), (2, 7), (2, 10), (2, 11),
    ])
    c.executemany("INSERT INTO achievements (user_id, badge_name, badge_icon) VALUES (?, ?, ?)", [
        (2, 'First Quiz', '🎯'), (2, 'Week Warrior', '🔥'), (2, 'Rising Star', '⭐'),
    ])
    c.executemany("INSERT INTO progress_reports (user_id, week_label, avg_score) VALUES (?, ?, ?)", [
        (2, 'Week 1', 55.0), (2, 'Week 2', 62.0), (2, 'Week 3', 68.0),
        (2, 'Week 4', 72.0), (2, 'Week 5', 78.0), (2, 'Week 6', 80.0),
    ])

    conn.commit()
    conn.close()
