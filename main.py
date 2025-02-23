import os
import json
from flask import Flask, redirect, url_for, flash, render_template, request, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.orm.exc import NoResultFound
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# --- Flask Setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('SESSION_SECRET', os.urandom(24))

# --- Session Cookie Security ---
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# --- Database Setup ---
db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    current_question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    progress = relationship("UserProgress", back_populates="user")

class QuizSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    questions = relationship("Question", back_populates="section")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('quiz_section.id'), nullable=False)
    sentence = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    hints = db.Column(db.Text)
    section = relationship("QuizSection", back_populates="questions")
    progress = relationship("UserProgress", back_populates="question")

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    attempts = db.Column(db.Integer, default=0)
    correct = db.Column(db.Boolean, default=False)
    user = relationship("User", back_populates="progress")
    question = relationship("Question", back_populates="progress")
    __table_args__ = (db.UniqueConstraint('user_id', 'question_id'),)

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'google.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Flask-Dance (Google OAuth) Setup ---
try:
    google_secrets = json.loads(os.environ.get("GOOGLE_OAUTH_SECRETS", "{}"))
    if not google_secrets or "web" not in google_secrets:
        raise ValueError("Invalid Google OAuth secrets format")

    # Get the configured redirect URI from the secrets
    oauth_redirect_uri = google_secrets["web"]["redirect_uris"][0]

    google_bp = make_google_blueprint(
        client_id=google_secrets["web"]["client_id"],
        client_secret=google_secrets["web"]["client_secret"],
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_to="oauth2callback"
    )
    app.register_blueprint(google_bp)
except (json.JSONDecodeError, KeyError) as e:
    logging.error(f"Failed to parse Google OAuth secrets: {e}")
    raise ValueError("Invalid Google OAuth secrets configuration")


# --- OAuth Routes ---
@app.route('/oauth2callback')
def oauth2callback():
    if not google.authorized:
        flash("You denied the request to sign in.")
        return redirect(url_for("index"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash(f"Failed to fetch user info: {resp.text}")
        return redirect(url_for("index"))

    user_info = resp.json()
    google_id = user_info["id"]
    email = user_info["email"]
    name = user_info.get("name")

    try:
        user = User.query.filter_by(google_id=google_id).one()
    except NoResultFound:
        user = User(google_id=google_id, email=email, name=name)
        db.session.add(user)
        db.session.commit()
        flash("New user created and logged in!")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {e}")
        return redirect(url_for('index'))

    login_user(user)
    flash("Successfully logged in with Google!")
    return redirect(url_for("quiz"))

# --- Initial Data Loading ---
def load_initial_data():
    with app.app_context():
        db.create_all()

        quiz_data = {
            "Basic Predicates": {
                "description": "Simple sentences with predicates.",
                "questions": [
                    {"sentence": "John loves Mary.", "answer": "Loves(John, Mary)", "hints": ["Hint 1", "Hint 2", "Hint 3"]},
                    {"sentence": "All dogs are mammals.", "answer": "∀x(Dog(x) → Mammal(x))", "hints": ["Think about universal quantification (for all).", "You'll need an implication (if-then).", "The general form is: ∀x(P(x) → Q(x))"]},
                    {"sentence": "Some cats are friendly.", "answer": "∃x(Cat(x) & Friendly(x))", "hints": ["Think about existential quantification (there exists).", "You'll need a conjunction (and).", "The general form is: ∃x(P(x) & Q(x))"]},
                    {"sentence": "No birds can fly.", "answer": "~∃x(Bird(x) & Fly(x))", "hints": ["Consider negation (not).", "This can be expressed using existential quantification or universal quantification.", "Think: 'There does not exist a bird that can fly'."]},
                    {"sentence": "If something is a square, then it is a rectangle.", "answer": "∀x(Square(x) → Rectangle(x))", "hints": ["This is a conditional statement.", "Use universal quantification for 'something'.", "The implication (→) represents the 'if-then'."]},
                    {"sentence": "There is a student who likes logic.", "answer": "∃x(Student(x) & LikesLogic(x))", "hints": ["This requires existential quantification.", "You'll need a conjunction to connect the properties.", "The general form is 'There exists an x such that...'."]},
                    {"sentence": "Beatrice is a scientist or a novelist.", "answer": "Scientist(b) ∨ Novelist(b)", "hints": ["This is a disjunction (or) statement.", "Use individual constants for named individuals.", "The general form is P(b) ∨ Q(b)"]},
                    {"sentence": "Hermione is a scientist if Beatrice is a novelist.", "answer": "Novelist(b) → Scientist(h)", "hints": ["This is a conditional statement.", "Use individual constants for named individuals.", "The general form is P(b) → Q(h)"]},
                    {"sentence": "Some Canadians are friendly.", "answer": "∃x(Canadian(x) & Friendly(x))", "hints": ["Use existential quantification for 'some'.", "Connect the properties with conjunction.", "The general form is ∃x(P(x) & Q(x))"]},
                    {"sentence": "No Canadians are friendly.", "answer": "~∃x(Canadian(x) & Friendly(x))", "hints": ["This can be written with negation and existential quantification.", "Think: 'There does not exist a Canadian who is friendly'.", "Alternative form: ∀x(Canadian(x) → ~Friendly(x))"]},
                    {"sentence": "All introverts are quiet and thoughtful.", "answer": "∀x(Introvert(x) → (Quiet(x) & Thoughtful(x)))", "hints": ["Use universal quantification for 'all'.", "The consequent has a conjunction.", "The general form is ∀x(P(x) → (Q(x) & R(x)))"]},
                    {"sentence": "Only Democrats and Republicans can be president.", "answer": "∀x(President(x) → (Democrat(x) ∨ Republican(x)))", "hints": ["Use universal quantification.", "The consequent has a disjunction.", "Think about the logical form of 'only'"]},
                    {"sentence": "All dogs are canines only if some cats are not reptiles.", "answer": "∀x(Dog(x) → Canine(x)) → ∃x(Cat(x) & ~Reptile(x))", "hints": ["This is a complex conditional.", "Break it down into two parts.", "Use both universal and existential quantification"]},
                    {"sentence": "Yetis exist if and only if some mammals are bipedal.", "answer": "∃x(Yeti(x)) ↔ ∃x(Mammal(x) & Bipedal(x))", "hints": ["Use biconditional for 'if and only if'.", "Both sides use existential quantification.", "The right side needs conjunction"]},
                    {"sentence": "It is not true that either some reptiles have wings or all friendly cats are orange.", "answer": "~(∃x(Reptile(x) & Wings(x)) ∨ ∀x((Friendly(x) & Cat(x)) → Orange(x)))", "hints": ["This is a complex negation.", "Break down the disjunction inside the negation.", "Pay attention to the scope of quantifiers"]},
                    {"sentence": "All students are either freshmen or seniors.", "answer": "∀x(Student(x) → (Freshman(x) ∨ Senior(x)))", "hints": ["Use universal quantification for 'all'.", "The consequent contains a disjunction.", "Think about the structure: if student then (freshman or senior)"]}
                ]
            },
            "Many-Place Predicates": {
                "description": "Sentences with predicates that take more than one argument.",
                "questions": [
                    {"sentence": "Iris reads the Odyssey.", "answer": "Rio", "hints": ["This is a two-place predicate.", "Use capital letters for the predicates and lowercase for constants.", "The first constant represents the subject, the second the object."]},
                    {"sentence": "Arielle is a friend of either Inez or Claudia.", "answer": "Fai ∨ Fac", "hints": ["Use F for 'friend of'", "Use lowercase letters for the constants: a (Arielle), i (Inez), c (Claudia)", "Connect the two possibilities with OR (∨)"]},
                    {"sentence": "Nigel loathes Hubert if Hubert loathes Uriah.", "answer": "Lhu → Lnh", "hints": ["Use L for 'loathes'", "Use lowercase letters for constants: n (Nigel), h (Hubert), u (Uriah)", "This is a conditional statement using →"]},
                    {"sentence": "Iris is not afraid of anything.", "answer": "∀x~Aix", "hints": ["This involves universal quantification and negation.", "A stands for 'afraid of'", "i represents Iris"]},
                    {"sentence": "All things Iris is afraid of are yellow.", "answer": "∀x(Aix → Yx)", "hints": ["This involves universal quantification.", "Use A for 'afraid of' and Y for 'yellow'", "i represents Iris"]},
                    {"sentence": "Barnabas eats only healthy items.", "answer": "∀x(Ebx → Hx)", "hints": ["Use E for 'eats' and H for 'healthy'", "b represents Barnabas", "The quantifier ranges over the items eaten"]},
                    {"sentence": "Some people cannot sell anything.", "answer": "∃x[Px & (∀y)~Sxy]", "hints": ["This involves both existential and universal quantification.", "P stands for 'person', S for 'can sell'", "Use & for conjunction"]},
                    {"sentence": "No person can sell everything.", "answer": "∀x[Px → (∃y)~Sxy]", "hints": ["This can be written in two ways.", "Alternative form: ~(∃x)[Px & (∀y)Sxy]", "P stands for 'person', S for 'can sell'"]}
                ]
            }
        }

        for section_name, section_data in quiz_data.items():
            try:
                section = QuizSection.query.filter_by(name=section_name).one()
                print(f"Section '{section_name}' already exists.")
            except NoResultFound:
                section = QuizSection(name=section_name, description=section_data["description"])
                db.session.add(section)
                db.session.commit()
                print(f"Section '{section_name}' created.")

            for question_data in section_data["questions"]:
                try:
                    question = Question.query.filter_by(sentence=question_data['sentence']).one()
                    print(f"Question {question_data['sentence']} already exists.")
                except NoResultFound:
                    hints_string = "|".join(question_data["hints"])
                    question = Question(
                        sentence=question_data["sentence"],
                        answer=question_data["answer"],
                        hints=hints_string,
                        section_id=section.id
                    )
                    db.session.add(question)
                    print(f"Created question {question_data['sentence']}.")
        db.session.commit()
        print("Initial data loaded successfully.")

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    if not current_user.is_authenticated:
        return redirect(url_for('google.login'))

    if 'score' not in session:
        session['score'] = 0
    if 'total_attempts' not in session:
        session['total_attempts'] = 0

    current_question = get_current_question()

    if request.method == 'POST':
        user_answer = request.form.get('answer', '')

        if current_question:
            session['total_attempts'] += 1
            user_progress = UserProgress.query.filter_by(
                user_id=current_user.id,
                question_id=current_question.id
            ).first()

            if check_answer(user_answer, current_question.answer):
                session['score'] += 1
                if user_progress:
                    user_progress.correct = True
                    user_progress.attempts += 1
                else:
                    user_progress = UserProgress(
                        user_id=current_user.id,
                        question_id=current_question.id,
                        correct=True,
                        attempts=1
                    )
                    db.session.add(user_progress)
                db.session.commit()

                session['question_index'] = session.get('question_index', 0) + 1
                session['hint_index'] = 0
                flash("Correct! Moving to next question...", "success")
                return redirect(url_for('quiz'))
            else:
                if user_progress:
                    user_progress.attempts += 1
                else:
                    user_progress = UserProgress(
                        user_id=current_user.id,
                        question_id=current_question.id,
                        correct=False,
                        attempts=1
                    )
                    db.session.add(user_progress)
                db.session.commit()
                flash("Incorrect. Try again!", "danger")

    return render_template('quiz.html',
                         question=current_question,
                         progress=(session.get('question_index', 0) / len(questions)) * 100,
                         score=session['score'],
                         total_questions=len(questions))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("index"))

def get_current_question():
    """Gets the current question based on the session's progress."""
    if not current_user.is_authenticated:
        return None
    question_set = session.get('question_set', 'basic_translation')
    questions_list = Question.query.filter(Question.section.has(name=question_set)).all()
    question_index = session.get('question_index', 0)
    if question_index < len(questions_list):
        return questions_list[question_index]
    return None

def check_answer(user_answer, correct_answer):
    """Checks if the user's answer matches any of the equivalent correct answers."""
    normalized_user_answer = user_answer.strip().lower().replace(" ", "")
    return normalized_user_answer == correct_answer.strip().lower().replace(" ", "")

questions = [] #This needs to be populated dynamically based on the database.


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        load_initial_data()
    app.run(host='0.0.0.0', port=3000, debug=True)