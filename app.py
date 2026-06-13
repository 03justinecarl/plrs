from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = 'plrs-pup-secret-key-2024'

# Jinja2 globals
app.jinja_env.globals['enumerate'] = enumerate
app.jinja_env.globals['min'] = min
app.jinja_env.globals['max'] = max

with app.app_context():
    init_db()
    seed_db()

# ── Decorators ────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' not in session:
        return None
    db = get_db()
    user = db.execute(
        "SELECT u.*, p.name as program_name, p.code as program_code "
        "FROM users u LEFT JOIN programs p ON u.program_id = p.id WHERE u.id = ?",
        (session['user_id'],)
    ).fetchone()
    db.close()
    return user

# ── Auth Routes ───────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home') if session.get('role') == 'student' else url_for('admin_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'error')
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()
    programs = db.execute("SELECT * FROM programs").fetchall()
    db.close()

    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        student_id = request.form.get('student_id', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        program_id = request.form.get('program_id')

        if not all([name, student_id, email, password, program_id]):
            flash('All fields are required.', 'error')
        else:
            try:
                db2 = get_db()
                # Check duplicates explicitly first for a friendlier message
                existing = db2.execute(
                    "SELECT id FROM users WHERE email = ? OR student_id = ?",
                    (email, student_id)
                ).fetchone()
                if existing:
                    flash('Email or Student ID is already registered.', 'error')
                    db2.close()
                else:
                    db2.execute(
                        "INSERT INTO users (name, student_id, email, password_hash, program_id, role) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (name, student_id, email,
                         generate_password_hash(password), program_id, 'student')
                    )
                    db2.commit()
                    db2.close()
                    flash('Account created! Please sign in.', 'success')
                    return redirect(url_for('login'))
            except Exception as e:
                flash('Registration failed. Please try again.', 'error')

    return render_template('register.html', programs=programs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Student Routes ────────────────────────────────────────────────────────────

@app.route('/home')
@login_required
def home():
    user = get_current_user()
    db = get_db()
    weak = db.execute(
        "SELECT wa.avg_score, s.name FROM weak_areas wa "
        "JOIN subjects s ON wa.subject_id = s.id WHERE wa.user_id = ? ORDER BY wa.avg_score ASC LIMIT 1",
        (user['id'],)
    ).fetchone()
    recent_scores = db.execute(
        "SELECT sc.score, sc.total, q.title, sc.taken_at FROM scores sc "
        "JOIN quizzes q ON sc.quiz_id = q.id WHERE sc.user_id = ? ORDER BY sc.taken_at DESC LIMIT 3",
        (user['id'],)
    ).fetchall()
    recommendations = db.execute(
        "SELECT r.title, r.type, r.url FROM recommendations rec "
        "JOIN resources r ON rec.resource_id = r.id WHERE rec.user_id = ? LIMIT 4",
        (user['id'],)
    ).fetchall()
    achievements = db.execute(
        "SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at DESC LIMIT 3",
        (user['id'],)
    ).fetchall()
    db.close()
    return render_template('home.html', user=user, weak=weak,
                           recent_scores=recent_scores,
                           recommendations=recommendations,
                           achievements=achievements)

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    db = get_db()
    subject_scores = db.execute(
        "SELECT s.name, AVG(sc.score * 100.0 / sc.total) as avg_pct "
        "FROM scores sc JOIN quizzes q ON sc.quiz_id = q.id "
        "JOIN subjects s ON q.subject_id = s.id "
        "WHERE sc.user_id = ? GROUP BY s.id ORDER BY avg_pct DESC",
        (user['id'],)
    ).fetchall()
    weak_areas = db.execute(
        "SELECT s.name, wa.avg_score FROM weak_areas wa "
        "JOIN subjects s ON wa.subject_id = s.id WHERE wa.user_id = ? ORDER BY wa.avg_score ASC",
        (user['id'],)
    ).fetchall()
    total_quizzes = db.execute("SELECT COUNT(*) FROM scores WHERE user_id = ?", (user['id'],)).fetchone()[0]
    avg_score = db.execute(
        "SELECT AVG(score * 100.0 / total) FROM scores WHERE user_id = ?", (user['id'],)
    ).fetchone()[0] or 0
    achievements = db.execute("SELECT * FROM achievements WHERE user_id = ?", (user['id'],)).fetchall()
    db.close()
    return render_template('dashboard.html', user=user,
                           subject_scores=subject_scores,
                           weak_areas=weak_areas,
                           total_quizzes=total_quizzes,
                           avg_score=round(avg_score, 1),
                           achievements=achievements)

@app.route('/api/progress')
@login_required
def api_progress():
    db = get_db()
    rows = db.execute(
        "SELECT week_label, avg_score FROM progress_reports WHERE user_id = ? ORDER BY id",
        (session['user_id'],)
    ).fetchall()
    subject_rows = db.execute(
        "SELECT s.name, AVG(sc.score * 100.0 / sc.total) as avg_pct "
        "FROM scores sc JOIN quizzes q ON sc.quiz_id = q.id "
        "JOIN subjects s ON q.subject_id = s.id "
        "WHERE sc.user_id = ? GROUP BY s.id",
        (session['user_id'],)
    ).fetchall()
    db.close()
    return jsonify({
        'weeks': [r['week_label'] for r in rows],
        'scores': [r['avg_score'] for r in rows],
        'subjects': [r['name'] for r in subject_rows],
        'subject_scores': [round(r['avg_pct'], 1) for r in subject_rows],
    })

@app.route('/quiz')
@login_required
def quiz():
    user = get_current_user()
    db = get_db()
    taken_ids = [r[0] for r in db.execute(
        "SELECT DISTINCT quiz_id FROM scores WHERE user_id = ?", (user['id'],)
    ).fetchall()]
    quizzes = db.execute(
        "SELECT q.*, s.name as subject_name FROM quizzes q "
        "JOIN subjects s ON q.subject_id = s.id WHERE s.program_id = ?",
        (user['program_id'],)
    ).fetchall()
    db.close()
    pending = [q for q in quizzes if q['id'] not in taken_ids]
    completed = [q for q in quizzes if q['id'] in taken_ids]
    return render_template('quiz.html', user=user, pending=pending, completed=completed)

@app.route('/quiz/<int:quiz_id>')
@login_required
def quiz_take(quiz_id):
    user = get_current_user()
    db = get_db()
    quiz = db.execute("SELECT q.*, s.name as subject_name FROM quizzes q JOIN subjects s ON q.subject_id = s.id WHERE q.id = ?", (quiz_id,)).fetchone()
    questions = db.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,)).fetchall()
    db.close()
    if not quiz or not questions:
        flash('Quiz not found.', 'error')
        return redirect(url_for('quiz'))
    return render_template('quiz_take.html', user=user, quiz=quiz, questions=questions)

@app.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def quiz_submit(quiz_id):
    user = get_current_user()
    db = get_db()
    questions = db.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,)).fetchall()
    quiz = db.execute("SELECT q.*, s.id as subject_id FROM quizzes q JOIN subjects s ON q.subject_id = s.id WHERE q.id = ?", (quiz_id,)).fetchone()
    score = sum(1 for q in questions if request.form.get(f'q{q["id"]}') == q['correct'])
    total = len(questions)
    db.execute("INSERT INTO scores (user_id, quiz_id, score, total) VALUES (?, ?, ?, ?)",
               (user['id'], quiz_id, score, total))

    # Update weak areas
    pct = score * 100.0 / total if total > 0 else 0
    db.execute("""INSERT INTO weak_areas (user_id, subject_id, avg_score) VALUES (?, ?, ?)
                  ON CONFLICT(user_id, subject_id) DO UPDATE SET avg_score =
                  (avg_score + excluded.avg_score) / 2""",
               (user['id'], quiz['subject_id'], pct))

    # Award XP
    xp_gain = score * 10
    db.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (xp_gain, user['id']))

    # Auto-recommend resources if weak (<60%)
    if pct < 60:
        resources = db.execute(
            "SELECT id FROM resources WHERE subject_id = ? LIMIT 3", (quiz['subject_id'],)
        ).fetchall()
        for r in resources:
            db.execute("INSERT OR IGNORE INTO recommendations (user_id, resource_id) VALUES (?, ?)",
                       (user['id'], r['id']))
        # Add progress report entry
        db.execute("INSERT INTO progress_reports (user_id, week_label, avg_score) VALUES (?, ?, ?)",
                   (user['id'], f"Quiz {quiz_id}", pct))

    # Badges
    quiz_count = db.execute("SELECT COUNT(*) FROM scores WHERE user_id = ?", (user['id'],)).fetchone()[0]
    if quiz_count == 1:
        db.execute("INSERT OR IGNORE INTO achievements (user_id, badge_name, badge_icon) VALUES (?, ?, ?)",
                   (user['id'], 'First Quiz', '🎯'))
    if score == total:
        db.execute("INSERT OR IGNORE INTO achievements (user_id, badge_name, badge_icon) VALUES (?, ?, ?)",
                   (user['id'], 'Perfect Score', '💯'))

    db.commit()
    wrong = [q for q in questions if request.form.get(f'q{q["id"]}') != q['correct']]
    db.close()
    return render_template('quiz_result.html', user=user, score=score, total=total,
                           pct=round(pct, 1), quiz=quiz, wrong=wrong, xp_gain=xp_gain)

@app.route('/learn')
@login_required
def learn():
    user = get_current_user()
    db = get_db()
    search = request.args.get('q', '').strip()
    rtype = request.args.get('type', '')
    weak_subject_ids = [r[0] for r in db.execute(
        "SELECT subject_id FROM weak_areas WHERE user_id = ? AND avg_score < 60", (user['id'],)
    ).fetchall()]
    recommended = db.execute(
        "SELECT r.*, s.name as subject_name FROM resources r JOIN subjects s ON r.subject_id = s.id "
        "WHERE r.subject_id IN ({})".format(','.join('?' * len(weak_subject_ids)) if weak_subject_ids else '0'),
        weak_subject_ids
    ).fetchall()
    query = ("SELECT r.*, s.name as subject_name FROM resources r JOIN subjects s ON r.subject_id = s.id "
             "WHERE s.program_id = ?")
    params = [user['program_id']]
    if search:
        query += " AND (r.title LIKE ? OR r.description LIKE ?)"
        params += [f'%{search}%', f'%{search}%']
    if rtype:
        query += " AND r.type = ?"
        params.append(rtype)
    all_resources = db.execute(query, params).fetchall()
    db.close()
    return render_template('learn.html', user=user, recommended=recommended,
                           all_resources=all_resources, search=search, rtype=rtype)

@app.route('/calendar')
@login_required
def calendar():
    user = get_current_user()
    db = get_db()
    upcoming_quizzes = db.execute(
        "SELECT q.title, s.name as subject_name, q.difficulty FROM quizzes q "
        "JOIN subjects s ON q.subject_id = s.id WHERE s.program_id = ? "
        "AND q.id NOT IN (SELECT quiz_id FROM scores WHERE user_id = ?)",
        (user['program_id'], user['id'])
    ).fetchall()
    db.close()
    return render_template('calendar.html', user=user, upcoming_quizzes=upcoming_quizzes)

@app.route('/games')
@login_required
def games():
    user = get_current_user()
    return render_template('games.html', user=user)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        db.execute("UPDATE users SET name = ? WHERE id = ?", (name, user['id']))
        db.commit()
        session['name'] = name
        flash('Profile updated!', 'success')
        db.close()
        return redirect(url_for('profile'))
    achievements = db.execute("SELECT * FROM achievements WHERE user_id = ?", (user['id'],)).fetchall()
    quiz_count = db.execute("SELECT COUNT(*) FROM scores WHERE user_id = ?", (user['id'],)).fetchone()[0]
    db.close()
    return render_template('profile.html', user=user, achievements=achievements, quiz_count=quiz_count)

# ── Admin Routes ──────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    total_students = db.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    total_quizzes_taken = db.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
    top_weak = db.execute(
        "SELECT s.name, COUNT(*) as cnt FROM weak_areas wa JOIN subjects s ON wa.subject_id = s.id "
        "WHERE wa.avg_score < 60 GROUP BY s.id ORDER BY cnt DESC LIMIT 5"
    ).fetchall()
    recent_users = db.execute(
        "SELECT u.name, u.student_id, p.code, u.created_at FROM users u "
        "LEFT JOIN programs p ON u.program_id = p.id WHERE u.role = 'student' "
        "ORDER BY u.created_at DESC LIMIT 5"
    ).fetchall()
    db.close()
    return render_template('admin/dashboard.html', total_students=total_students,
                           total_quizzes_taken=total_quizzes_taken,
                           top_weak=top_weak, recent_users=recent_users)

@app.route('/admin/users', methods=['GET', 'POST'])
@admin_required
def admin_users():
    if request.method == 'POST':
        role = request.form.get('role', 'student')
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        student_id = request.form.get('student_id', '').strip() if role == 'student' else None
        program_id = request.form.get('program_id') if role == 'student' else None

        if not all([name, email, password]) or (role == 'student' and not all([student_id, program_id])):
            flash('All required fields must be filled.', 'error')
        else:
            try:
                db = get_db()
                if role == 'student':
                    existing = db.execute("SELECT id FROM users WHERE email = ? OR student_id = ?", (email, student_id)).fetchone()
                else:
                    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
                
                if existing:
                    flash('Email or Student ID is already registered.', 'error')
                else:
                    db.execute(
                        "INSERT INTO users (name, student_id, email, password_hash, program_id, role) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (name, student_id, email, generate_password_hash(password), program_id, role)
                    )
                    db.commit()
                    flash(f'New {role.capitalize()} added successfully!', 'success')
                db.close()
            except Exception as e:
                flash(f'Failed to add user. Please try again.', 'error')
        return redirect(url_for('admin_users'))

    db = get_db()
    students = db.execute(
        "SELECT u.*, p.name as program_name, "
        "(SELECT COUNT(*) FROM scores WHERE user_id = u.id) as quiz_count "
        "FROM users u LEFT JOIN programs p ON u.program_id = p.id WHERE u.role = 'student' "
        "ORDER BY u.created_at DESC"
    ).fetchall()
    admins = db.execute(
        "SELECT u.*, (SELECT COUNT(*) FROM scores WHERE user_id = u.id) as quiz_count "
        "FROM users u WHERE u.role = 'admin' "
        "ORDER BY u.created_at DESC"
    ).fetchall()
    programs = db.execute("SELECT * FROM programs").fetchall()
    db.close()
    return render_template('admin/users.html', students=students, admins=admins, programs=programs, current_user_id=session.get('user_id'))

@app.route('/admin/users/delete/<int:user_id>')
@admin_required
def admin_delete_user(user_id):
    if user_id == session.get('user_id'):
        flash('You cannot delete your own admin account.', 'error')
        return redirect(url_for('admin_users'))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user:
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        flash(f"{user['role'].capitalize()} '{user['name']}' removed.", 'success')
    else:
        flash('User not found.', 'error')
    db.close()
    return redirect(url_for('admin_users'))

@app.route('/admin/quizzes', methods=['GET', 'POST'])
@admin_required
def admin_quizzes():
    db = get_db()
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        title = request.form.get('title', '').strip()
        difficulty = request.form.get('difficulty', 'medium')
        time_limit = request.form.get('time_limit', 300)
        db.execute("INSERT INTO quizzes (subject_id, title, difficulty, time_limit) VALUES (?,?,?,?)",
                   (subject_id, title, difficulty, time_limit))
        db.commit()
        flash('Quiz added!', 'success')
    quizzes = db.execute(
        "SELECT q.*, s.name as subject_name, "
        "(SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as q_count "
        "FROM quizzes q JOIN subjects s ON q.subject_id = s.id ORDER BY q.id DESC"
    ).fetchall()
    subjects = db.execute("SELECT * FROM subjects ORDER BY program_id, name").fetchall()
    db.close()
    return render_template('admin/quizzes.html', quizzes=quizzes, subjects=subjects)

@app.route('/admin/resources', methods=['GET', 'POST'])
@admin_required
def admin_resources():
    db = get_db()
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        title = request.form.get('title', '').strip()
        rtype = request.form.get('type', 'pdf')
        url = request.form.get('url', '').strip()
        description = request.form.get('description', '').strip()
        db.execute("INSERT INTO resources (subject_id, title, type, url, description) VALUES (?,?,?,?,?)",
                   (subject_id, title, rtype, url, description))
        db.commit()
        flash('Resource added!', 'success')
    resources = db.execute(
        "SELECT r.*, s.name as subject_name FROM resources r JOIN subjects s ON r.subject_id = s.id ORDER BY r.id DESC"
    ).fetchall()
    subjects = db.execute("SELECT * FROM subjects ORDER BY program_id, name").fetchall()
    db.close()
    return render_template('admin/resources.html', resources=resources, subjects=subjects)

@app.route('/admin/resources/delete/<int:res_id>')
@admin_required
def admin_delete_resource(res_id):
    db = get_db()
    db.execute("DELETE FROM resources WHERE id = ?", (res_id,))
    db.commit()
    db.close()
    flash('Resource deleted.', 'success')
    return redirect(url_for('admin_resources'))

if __name__ == '__main__':
    app.run(debug=True)
