import os
from flask import Flask, render_template, request, session, redirect
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key")  

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
        "answer": "∃x(Cat(x) ∧ Friendly(x))",
        "hints": [
            "Think about existential quantification (there exists).",
            "You'll need a conjunction (and).",
            "The general form is: ∃x(P(x) ∧ Q(x))"
        ]
    },
    {
        "sentence": "No birds can fly.",
        "answer": "¬∃x(Bird(x) ∧ Fly(x))",
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
        "answer": "∃x(Student(x) ∧ LikesLogic(x))",
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
        "answer": "∃x(Canadian(x) ∧ Friendly(x))",
        "hints": [
            "Use existential quantification for 'some'.",
            "Connect the properties with conjunction.",
            "The general form is ∃x(P(x) ∧ Q(x))"
        ]
    },
    {
        "sentence": "No Canadians are friendly.",
        "answer": "¬∃x(Canadian(x) ∧ Friendly(x))",
        "hints": [
            "This can be written with negation and existential quantification.",
            "Think: 'There does not exist a Canadian who is friendly'.",
            "Alternative form: ∀x(Canadian(x) → ¬Friendly(x))"
        ]
    },
    {
        "sentence": "All introverts are quiet and thoughtful.",
        "answer": "∀x(Introvert(x) → (Quiet(x) ∧ Thoughtful(x)))",
        "hints": [
            "Use universal quantification for 'all'.",
            "The consequent has a conjunction.",
            "The general form is ∀x(P(x) → (Q(x) ∧ R(x)))"
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
        "answer": "∀x(Dog(x) → Canine(x)) → ∃x(Cat(x) ∧ ¬Reptile(x))",
        "hints": [
            "This is a complex conditional.",
            "Break it down into two parts.",
            "Use both universal and existential quantification"
        ]
    },
    {
        "sentence": "Yetis exist if and only if some mammals are bipedal.",
        "answer": "∃x(Yeti(x)) ↔ ∃x(Mammal(x) ∧ Bipedal(x))",
        "hints": [
            "Use biconditional for 'if and only if'.",
            "Both sides use existential quantification.",
            "The right side needs conjunction"
        ]
    },
    {
        "sentence": "It is not true that either some reptiles have wings or all friendly cats are orange.",
        "answer": "¬(∃x(Reptile(x) ∧ Wings(x)) ∨ ∀x((Friendly(x) ∧ Cat(x)) → Orange(x)))",
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

def get_current_question():
    """Gets the current question based on the session's progress."""
    question_index = session.get('question_index', 0)
    if question_index < len(questions):
        return questions[question_index]
    return None

def check_answer(user_answer, correct_answer):
    """Checks if the user's answer is correct (case-insensitive, ignores extra spaces)."""
    return user_answer.strip().lower().replace(" ", "") == correct_answer.strip().lower().replace(" ", "")

@app.route('/', methods=['GET', 'POST'])
def quiz():
    """Handles the main quiz logic."""
    if 'score' not in session:
        session['score'] = 0
    if 'total_attempts' not in session:
        session['total_attempts'] = 0

    if request.method == 'POST':
        user_answer = request.form.get('answer', '')
        question = get_current_question()

        if question:
            session['total_attempts'] += 1
            if check_answer(user_answer, question['answer']):
                session['score'] += 1
                session['question_index'] = session.get('question_index', 0) + 1
                session['hint_index'] = 0
                message = {"text": "Correct! Moving to next question...", "type": "success"}
                next_question = get_current_question()
                if not next_question:
                    message = {"text": f"Congratulations! Quiz completed. Score: {session['score']}/{len(questions)}", "type": "success"}
            else:
                session['hint_index'] = session.get('hint_index', 0) + 1
                hint_index = session['hint_index']
                if hint_index <= len(question['hints']):
                    message = {"text": f"Hint {hint_index}: {question['hints'][hint_index - 1]}", "type": "warning"}
                else:
                    message = {"text": f"The correct answer was: {question['answer']}", "type": "danger"}
                    session['question_index'] = session.get('question_index', 0) + 1
                    session['hint_index'] = 0
                    
            return render_template('quiz.html', 
                                question=get_current_question(), 
                                message=message,
                                progress=(session.get('question_index', 0) / len(questions)) * 100,
                                score=session['score'],
                                total_questions=len(questions))

    # Initial load or reset
    session['question_index'] = 0
    session['hint_index'] = 0
    session['score'] = 0
    session['total_attempts'] = 0
    
    return render_template('quiz.html', 
                         question=get_current_question(),
                         message=None,
                         progress=0,
                         score=0,
                         total_questions=len(questions))

@app.route('/reset')
def reset():
    """Resets the quiz."""
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
