import os
from flask import Flask, render_template, request, session, redirect
import logging
from datetime import datetime, timedelta
import time
from flask_session import Session

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key")
app.permanent_session_lifetime = timedelta(days=180)

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '.flask_session'
Session(app)  

# Questions data structure
questions = [
    {
        "sentence": "All dogs are mammals.",
        "answer": "∀x(Dog(x) → Mammal(x))",
        "hints": [
            "Think about universal quantification (for all).",
            "You'll need an implication (if-then).",
            "The general form is: ∀x(P(x) → Q(x))"
        ]
    },
    {
        "sentence": "Some cats are friendly.",
        "answer": "∃x(Cat(x) & Friendly(x))",
        "hints": [
            "Think about existential quantification (there exists).",
            "You'll need a conjunction (and).",
            "The general form is: ∃x(P(x) & Q(x))"
        ]
    },
    {
        "sentence": "No birds can fly.",
        "answer": "~∃x(Bird(x) & Fly(x))",
        "hints": [
            "Consider negation (not).",
            "This can be expressed using existential quantification or universal quantification.",
            "Think: 'There does not exist a bird that can fly.'"
        ]
    },
    {
        "sentence": "If something is a square, then it is a rectangle.",
        "answer": "∀x(Square(x) → Rectangle(x))",
        "hints": [
            "This is a conditional statement.",
            "Use universal quantification for 'something'.",
            "The implication (→) represents the 'if-then'."
        ]
    },
    {
        "sentence": "There is a student who likes logic.",
        "answer": "∃x(Student(x) & LikesLogic(x))",
        "hints": [
            "This requires existential quantification.",
            "You'll need a conjunction to connect the properties.",
            "The general form is 'There exists an x such that...'."
        ]
    },
    {
        "sentence": "Beatrice is a scientist or a novelist.",
        "answer": "Scientist(b) ∨ Novelist(b)",
        "hints": [
            "This is a disjunction (or) statement.",
            "Use individual constants for named individuals.",
            "The general form is P(b) ∨ Q(b)"
        ]
    },
    {
        "sentence": "Hermione is a scientist if Beatrice is a novelist.",
        "answer": "Novelist(b) → Scientist(h)",
        "hints": [
            "This is a conditional statement.",
            "Use individual constants for named individuals.",
            "The general form is P(b) → Q(h)"
        ]
    },
    {
        "sentence": "Some Canadians are friendly.",
        "answer": "∃x(Canadian(x) & Friendly(x))",
        "hints": [
            "Use existential quantification for 'some'.",
            "Connect the properties with conjunction.",
            "The general form is ∃x(P(x) & Q(x))"
        ]
    },
    {
        "sentence": "No Canadians are friendly.",
        "answer": "~∃x(Canadian(x) & Friendly(x))",
        "hints": [
            "This can be written with negation and existential quantification.",
            "Think: 'There does not exist a Canadian who is friendly'.",
            "Alternative form: ∀x(Canadian(x) → ~Friendly(x))"
        ]
    },
    {
        "sentence": "All introverts are quiet and thoughtful.",
        "answer": "∀x(Introvert(x) → (Quiet(x) & Thoughtful(x)))",
        "hints": [
            "Use universal quantification for 'all'.",
            "The consequent has a conjunction.",
            "The general form is ∀x(P(x) → (Q(x) & R(x)))"
        ]
    },
    {
        "sentence": "Only Democrats and Republicans can be president.",
        "answer": "∀x(President(x) → (Democrat(x) ∨ Republican(x)))",
        "hints": [
            "Use universal quantification.",
            "The consequent has a disjunction.",
            "Think about the logical form of 'only'"
        ]
    },
    {
        "sentence": "All dogs are canines only if some cats are not reptiles.",
        "answer": "∀x(Dog(x) → Canine(x)) → ∃x(Cat(x) & ~Reptile(x))",
        "hints": [
            "This is a complex conditional.",
            "Break it down into two parts.",
            "Use both universal and existential quantification"
        ]
    },
    {
        "sentence": "Yetis exist if and only if some mammals are bipedal.",
        "answer": "∃x(Yeti(x)) ↔ ∃x(Mammal(x) & Bipedal(x))",
        "hints": [
            "Use biconditional for 'if and only if'.",
            "Both sides use existential quantification.",
            "The right side needs conjunction"
        ]
    },
    {
        "sentence": "It is not true that either some reptiles have wings or all friendly cats are orange.",
        "answer": "~(∃x(Reptile(x) & Wings(x)) ∨ ∀x((Friendly(x) & Cat(x)) → Orange(x)))",
        "hints": [
            "This is a complex negation.",
            "Break down the disjunction inside the negation.",
            "Pay attention to the scope of quantifiers"
        ]
    },
    {
        "sentence": "All students are either freshmen or seniors.",
        "answer": "∀x(Student(x) → (Freshman(x) ∨ Senior(x)))",
        "hints": [
            "Use universal quantification for 'all'.",
            "The consequent contains a disjunction.",
            "Think about the structure: if student then (freshman or senior)"
        ]
    }
]

many_place_questions = [
    {
        "sentence": "Iris reads the Odyssey.",
        "answer": "Rio",
        "hints": [
            "This is a two-place predicate.",
            "Use capital letters for the predicates and lowercase for constants.",
            "The first constant represents the subject, the second the object."
        ]
    },
    {
        "sentence": "Arielle is a friend of either Inez or Claudia.",
        "answer": "Fai ∨ Fac",
        "hints": [
            "Use F for 'friend of'",
            "Use lowercase letters for the constants: a (Arielle), i (Inez), c (Claudia)",
            "Connect the two possibilities with OR (∨)"
        ]
    },
    {
        "sentence": "Nigel loathes Hubert if Hubert loathes Uriah.",
        "answer": "Lhu → Lnh",
        "hints": [
            "Use L for 'loathes'",
            "Use lowercase letters for constants: n (Nigel), h (Hubert), u (Uriah)",
            "This is a conditional statement using →"
        ]
    },
    {
        "sentence": "Iris is not afraid of anything.",
        "answer": "∀x~Aix",
        "hints": [
            "This involves universal quantification and negation.",
            "A stands for 'afraid of'",
            "i represents Iris"
        ]
    },
    {
        "sentence": "All things Iris is afraid of are yellow.",
        "answer": "∀x(Aix → Yx)",
        "hints": [
            "This involves universal quantification.",
            "Use A for 'afraid of' and Y for 'yellow'",
            "i represents Iris"
        ]
    },
    {
        "sentence": "Barnabas eats only healthy items.",
        "answer": "∀x(Ebx → Hx)",
        "hints": [
            "Use E for 'eats' and H for 'healthy'",
            "b represents Barnabas",
            "The quantifier ranges over the items eaten"
        ]
    },
    {
        "sentence": "Some people cannot sell anything.",
        "answer": "∃x[Px & (∀y)~Sxy]",
        "hints": [
            "This involves both existential and universal quantification.",
            "P stands for 'person', S for 'can sell'",
            "Use & for conjunction"
        ]
    },
    {
        "sentence": "No person can sell everything.",
        "answer": "∀x[Px → (∃y)~Sxy]",
        "hints": [
            "This can be written in two ways.",
            "Alternative form: ~(∃x)[Px & (∀y)Sxy]",
            "P stands for 'person', S for 'can sell'"
        ]
    }
]

def get_current_question():
    """Gets the current question based on the session's progress."""
    if 'user_state' not in session:
        return None
    question_set = session['user_state'].get('question_set', 'basic_translation')
    questions_list = many_place_questions if question_set == 'many_place' else questions
    question_index = session['user_state'].get('question_index', 0)
    if question_index < len(questions_list):
        return questions_list[question_index]
    return None

# Dictionary storing equivalent answers for each question
equivalent_answers = {
    "∀x(Dog(x) → Mammal(x))": ["∀x(Dog(x) → Mammal(x))", "∀x(Dog(x) → Mammal(x))", "∀x(Dog(x) → Mammal(x))"],
    "∃x(Cat(x) & Friendly(x))": ["∃x(Cat(x) & Friendly(x))", "∃x(Cat(x) & Friendly(x))", "∃x(Cat(x) & Friendly(x))"],
    "~∃x(Bird(x) & Fly(x))": ["~∃x(Bird(x) & Fly(x))", "~∃x(Bird(x) & Fly(x))", "~∃x(Bird(x) & Fly(x))"],
    "∀x(Square(x) → Rectangle(x))": ["∀x(Square(x) → Rectangle(x))", "∀x(Square(x) → Rectangle(x))", "∀x(Square(x) → Rectangle(x))"],
    "∃x(Student(x) & LikesLogic(x))": ["∃x(Student(x) & LikesLogic(x))", "∃x(Student(x) & LikesLogic(x))", "∃x(Student(x) & LikesLogic(x))"],
    "Scientist(b) ∨ Novelist(b)": ["Scientist(b) ∨ Novelist(b)", "Scientist(b) ∨ Novelist(b)", "Scientist(b) ∨ Novelist(b)"],
    "Novelist(b) → Scientist(h)": ["Novelist(b) → Scientist(h)", "Novelist(b) → Scientist(h)", "Novelist(b) → Scientist(h)"],
    "∃x(Canadian(x) & Friendly(x))": ["∃x(Canadian(x) & Friendly(x))", "∃x(Canadian(x) & Friendly(x))", "∃x(Canadian(x) & Friendly(x))"],
    "~∃x(Canadian(x) & Friendly(x))": ["~∃x(Canadian(x) & Friendly(x))", "~∃x(Canadian(x) & Friendly(x))", "~∃x(Canadian(x) & Friendly(x))"],
    "∀x(Introvert(x) → (Quiet(x) & Thoughtful(x)))": ["∀x(Introvert(x) → (Quiet(x) & Thoughtful(x)))", "∀x(Introvert(x) → (Quiet(x) & Thoughtful(x)))", "∀x(Introvert(x) → (Quiet(x) & Thoughtful(x)))"],
    "∀x(President(x) → (Democrat(x) ∨ Republican(x)))": ["∀x(President(x) → (Democrat(x) ∨ Republican(x)))", "∀x(President(x) → (Democrat(x) ∨ Republican(x)))", "∀x(President(x) → (Democrat(x) ∨ Republican(x)))"],
    "∀x(Dog(x) → Canine(x)) → ∃x(Cat(x) & ~Reptile(x))": ["∀x(Dog(x) → Canine(x)) → ∃x(Cat(x) & ~Reptile(x))", "∀x(Dog(x) → Canine(x)) → ∃x(Cat(x) & ~Reptile(x))", "∀x(Dog(x) → Canine(x)) → ∃x(Cat(x) & ~Reptile(x))"],
    "∃x(Yeti(x)) ↔ ∃x(Mammal(x) & Bipedal(x))": ["∃x(Yeti(x)) ↔ ∃x(Mammal(x) & Bipedal(x))", "∃x(Yeti(x)) ↔ ∃x(Mammal(x) & Bipedal(x))", "∃x(Yeti(x)) ↔ ∃x(Mammal(x) & Bipedal(x))"],
    "~(∃x(Reptile(x) & Wings(x)) ∨ ∀x((Friendly(x) & Cat(x)) → Orange(x)))": ["~(∃x(Reptile(x) & Wings(x)) ∨ ∀x((Friendly(x) & Cat(x)) → Orange(x)))", "~(∃x(Reptile(x) & Wings(x)) ∨ ∀x((Friendly(x) & Cat(x)) → Orange(x)))", "~(∃x(Reptile(x) & Wings(x)) ∨ ∀x((Friendly(x) & Cat(x)) → Orange(x)))"],
    "∀x(Student(x) → (Freshman(x) ∨ Senior(x)))": ["∀x(Student(x) → (Freshman(x) ∨ Senior(x)))", "∀x(Student(x) → (Freshman(x) ∨ Senior(x)))", "∀x(Student(x) → (Freshman(x) ∨ Senior(x)))"],
    "Rio": ["Rio", "Rio", "Rio"],
    "Fai ∨ Fac": ["Fai ∨ Fac", "Fai ∨ Fac", "Fai ∨ Fac"],
    "Lhu → Lnh": ["Lhu → Lnh", "Lhu → Lnh", "Lhu → Lnh"],
    "∀x~Aix": ["∀x~Aix", "∀x~Aix", "∀x~Aix"],
    "∀x(Aix → Yx)": ["∀x(Aix → Yx)", "∀x(Aix → Yx)", "∀x(Aix → Yx)"],
    "∀x(Ebx → Hx)": ["∀x(Ebx → Hx)", "∀x(Ebx → Hx)", "∀x(Ebx → Hx)"],
    "∃x[Px & (∀y)~Sxy]": ["∃x[Px & (∀y)~Sxy]", "∃x[Px & (∀y)~Sxy]", "∃x[Px & (∀y)~Sxy]"],
    "∀x[Px → (∃y)~Sxy]": ["∀x[Px → (∃y)~Sxy]", "∀x[Px → (∃y)~Sxy]", "∀x[Px → (∃y)~Sxy]"]
}

def check_answer(user_answer, correct_answer):
    """Checks if the user's answer matches any of the equivalent correct answers."""
    normalized_user_answer = user_answer.strip().lower().replace(" ", "")
    equivalent_list = equivalent_answers.get(correct_answer, [correct_answer])
    return any(normalized_user_answer == ans.strip().lower().replace(" ", "") for ans in equivalent_list)

@app.route('/', methods=['GET', 'POST'])
def quiz():
    """Handles the main quiz logic."""
    # Initialize session variables if not present
    if not session.get('user_state'):
        session.permanent = True
        session['user_state'] = {
            'score': 0,
            'total_attempts': 0,
            'question_index': 0,
            'hint_index': 0,
            'question_set': 'basic_translation',
            'last_answer': '',
            'timestamp': datetime.now().timestamp()
        }

    # Session expiry check (optional, set to 24 hours)
    if time.time() - session['user_state'].get('timestamp', 0) > 15552000:  # 180 days in seconds
        session['user_state'] = {
            'score': 0, 
            'total_attempts': 0,
            'question_index': 0,
            'hint_index': 0,
            'question_set': 'basic_translation',
            'last_answer': '',
            'timestamp': datetime.now().timestamp()
        }

    if request.method == 'POST':
        user_answer = request.form.get('answer', '')
        question = get_current_question()

        if question:
            session['user_state']['total_attempts'] += 1
            if check_answer(user_answer, question['answer']):
                session['user_state']['score'] += 1
                session['user_state']['question_index'] = session['user_state'].get('question_index', 0) + 1
                session['user_state']['hint_index'] = 0
                message = {"text": "Correct! Moving to next question...", "type": "success"}
                next_question = get_current_question()
                if not next_question:
                    message = {"text": f"Congratulations! Quiz completed. Score: {session['user_state']['score']}/{len(questions)}", "type": "success"}
            else:
                session['user_state']['hint_index'] = session['user_state'].get('hint_index', 0) + 1
                hint_index = session['user_state']['hint_index']
                if hint_index <= len(question['hints']):
                    message = {"text": f"Hint {hint_index}: {question['hints'][hint_index - 1]}", "type": "warning"}
                else:
                    message = {"text": f"The correct answer was: {question['answer']}", "type": "danger"}
                    session['user_state']['question_index'] = session['user_state'].get('question_index', 0) + 1
                    session['user_state']['hint_index'] = 0
            session.modified = True

            return render_template('quiz.html', 
                                    question=get_current_question(), 
                                    message=message,
                                    progress=(session['user_state'].get('question_index', 0) / len(questions)) * 100,
                                    score=session['user_state']['score'],
                                    total_questions=len(questions))

    # Initial load or reset
    if 'user_state' not in session:
        session['user_state'] = {
            'question_index': 0,
            'hint_index': 0,
            'score': 0,
            'total_attempts': 0,
            'question_set': 'basic_translation',
            'last_answer': '',
            'timestamp': datetime.now().timestamp()
        }
    
    # Get the correct total questions count based on question set
    question_set = session['user_state'].get('question_set', 'basic_translation')
    total_questions = len(many_place_questions if question_set == 'many_place' else questions)
    
    # Calculate progress based on current state
    progress = (session['user_state'].get('question_index', 0) / total_questions) * 100 if total_questions > 0 else 0
    
    return render_template('quiz.html', 
                            question=get_current_question(),
                            message=None,
                            progress=progress,
                            score=session['user_state'].get('score', 0),
                            total_questions=total_questions)

@app.route('/reset')
def reset():
    """Resets the quiz."""
    if 'user_state' in session:
        session['user_state'] = {
            'score': 0,
            'total_attempts': 0,
            'question_index': 0,
            'hint_index': 0,
            'question_set': 'basic_translation',
            'last_answer': '',
            'timestamp': datetime.now().timestamp()
        }
    return redirect('/')

@app.route('/set_question_type', methods=['POST'])
def set_question_type():
    """Sets the type of questions to display."""
    question_type = request.form.get('type', 'basic_translation')
    
    # Initialize if user_state doesn't exist
    if 'user_state' not in session:
        session['user_state'] = {}
        
    # Save current progress
    current_type = session['user_state'].get('question_set', 'basic_translation')
    if current_type not in session:
        session[current_type] = {
            'score': session['user_state'].get('score', 0),
            'total_attempts': session['user_state'].get('total_attempts', 0),
            'question_index': session['user_state'].get('question_index', 0),
            'hint_index': session['user_state'].get('hint_index', 0)
        }
    
    # Load progress for selected type or initialize new
    if question_type not in session:
        session[question_type] = {
            'score': 0,
            'total_attempts': 0,
            'question_index': 0,
            'hint_index': 0
        }
    
    # Update user_state with saved progress
    session['user_state'] = {
        'score': session[question_type]['score'],
        'total_attempts': session[question_type]['total_attempts'],
        'question_index': session[question_type]['question_index'],
        'hint_index': session[question_type]['hint_index'],
        'question_set': question_type,
        'last_answer': '',
        'timestamp': datetime.now().timestamp()
    }
    session.modified = True
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)