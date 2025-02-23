document.addEventListener('DOMContentLoaded', function() {
    // Category definitions
    const categories = {
        'truth-tables': ['TT1', 'TT2', 'TT3', 'TT4'],
        'sentential-logic': ['SL1', 'SL2', 'SL3', 'SL4', 'SL5'],
        'predicate-logic': [
            'Basic Translation',
            'Many Place Translation',
            'UI and EE proofs',
            'EE and EI proofs'
        ]
    };

    // Initialize category buttons
    const categoryButtons = document.querySelectorAll('.category-btn');
    const subcategoryContainer = document.querySelector('.subcategory-buttons');
    const quizContainer = document.querySelector('.quiz-container');

    // Set initial state
    if (categoryButtons.length > 0) {
        // Select Predicate Logic by default
        const predicateLogicBtn = document.querySelector('[data-category="predicate-logic"]');
        if (predicateLogicBtn) {
            predicateLogicBtn.classList.add('active');
            updateSubcategories('predicate-logic');
        }
    }

    // Category button click handler
    categoryButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active state
            categoryButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Update subcategories
            const category = this.getAttribute('data-category');
            updateSubcategories(category);
        });
    });

    function updateSubcategories(category) {
        // Clear existing subcategories
        subcategoryContainer.innerHTML = '';

        // Add new subcategory buttons
        categories[category].forEach((subcategory, index) => {
            const button = document.createElement('button');
            button.className = 'btn btn-outline-secondary subcategory-btn';
            button.textContent = subcategory;

            // For predicate logic's basic translation, make it functional
            if (category === 'predicate-logic' && subcategory === 'Basic Translation') {
                button.classList.add('active');
                if (quizContainer) quizContainer.classList.remove('hidden');
                button.addEventListener('click', () => {
                    document.querySelectorAll('.subcategory-btn').forEach(btn => 
                        btn.classList.remove('active'));
                    button.classList.add('active');
                    if (quizContainer) quizContainer.classList.remove('hidden');
                });
            } else {
                // Placeholder buttons
                button.addEventListener('click', () => {
                    document.querySelectorAll('.subcategory-btn').forEach(btn => 
                        btn.classList.remove('active'));
                    button.classList.add('active');
                    if (quizContainer) quizContainer.classList.add('hidden');
                    alert('This section is coming soon!');
                });
            }

            subcategoryContainer.appendChild(button);
        });
    }

    // Enable dismissible alerts
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        new bootstrap.Alert(alert);
    });

    // Focus on answer input when page loads
    var answerInput = document.getElementById('answer');
    if (answerInput) {
        answerInput.focus();
    }

    // Handle symbol button clicks
    document.querySelectorAll('.symbol-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const symbol = this.getAttribute('data-symbol');
            if (answerInput) {
                const start = answerInput.selectionStart;
                const end = answerInput.selectionEnd;
                answerInput.value = answerInput.value.substring(0, start) + 
                                  symbol + 
                                  answerInput.value.substring(end);
                answerInput.selectionStart = answerInput.selectionEnd = start + 1;
                answerInput.focus();
            }
        });
    });

    // Keyboard shortcuts for special symbols
    if (answerInput) {
        answerInput.addEventListener('keydown', function(e) {
            const shortcuts = {
                'a': '∀',  // Alt + A for universal quantifier
                'e': '∃',  // Alt + E for existential quantifier
                'i': '→',  // Alt + I for implies
                'n': '¬',  // Alt + N for not
                'd': '∧',  // Alt + D for and
                'o': '∨'   // Alt + O for or
            };

            if (e.altKey && shortcuts[e.key.toLowerCase()]) {
                e.preventDefault();
                const start = this.selectionStart;
                const end = this.selectionEnd;
                const symbol = shortcuts[e.key.toLowerCase()];

                this.value = this.value.substring(0, start) + 
                            symbol + 
                            this.value.substring(end);

                this.selectionStart = this.selectionEnd = start + 1;
            }
        });
    }
});