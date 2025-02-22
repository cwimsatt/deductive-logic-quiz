document.addEventListener('DOMContentLoaded', function() {
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

    // Add keyboard shortcuts for special symbols
    if (answerInput) {
        answerInput.addEventListener('keydown', function(e) {
            const shortcuts = {
                'a': '∀',  // Alt + A for universal quantifier
                'e': '∃',  // Alt + E for existential quantifier
                'i': '→',  // Alt + I for implies
                'n': '¬',  // Alt + N for not
                'd': '∧'   // Alt + D for and
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
