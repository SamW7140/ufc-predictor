document.addEventListener('DOMContentLoaded', () => {
    const predictBtn = document.getElementById('predictBtn');
    const fighter1Input = document.getElementById('fighter1');
    const fighter2Input = document.getElementById('fighter2');
    const loadingDiv = document.getElementById('loading');
    const resultDiv = document.getElementById('result');
    const predictionText = document.getElementById('predictionText');
    const fighter1EloDiv = document.getElementById('fighter1Elo');
    const fighter2EloDiv = document.getElementById('fighter2Elo');
    const errorDiv = document.getElementById('error');
    let fighterList = [];

    // Fetch fighter list for autocomplete
    async function fetchFighterList() {
        try {
            const response = await fetch('/fighters');
            const data = await response.json();
            fighterList = data.fighters;
        } catch (error) {
            console.error('Failed to fetch fighter list:', error);
        }
    }

    // Initialize autocomplete for both inputs
    function initAutocomplete(input, suggestionsDiv) {
        input.addEventListener('input', () => {
            const value = input.value.toLowerCase();
            const suggestions = fighterList.filter(fighter => 
                fighter.toLowerCase().includes(value)
            );
            
            suggestionsDiv.innerHTML = '';
            suggestionsDiv.classList.remove('active');
            
            if (suggestions.length > 0 && value.length > 0) {
                suggestions.forEach(fighter => {
                    const div = document.createElement('div');
                    div.textContent = fighter;
                    div.addEventListener('click', () => {
                        input.value = fighter;
                        suggestionsDiv.classList.remove('active');
                    });
                    suggestionsDiv.appendChild(div);
                });
                suggestionsDiv.classList.add('active');
            }
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !suggestionsDiv.contains(e.target)) {
                suggestionsDiv.classList.remove('active');
            }
        });
    }

    // Initialize autocomplete for both inputs
    initAutocomplete(fighter1Input, document.getElementById('fighter1-suggestions'));
    initAutocomplete(fighter2Input, document.getElementById('fighter2-suggestions'));

    // Fetch fighter list when page loads
    fetchFighterList();

    predictBtn.addEventListener('click', async () => {
        const fighter1 = fighter1Input.value.trim();
        const fighter2 = fighter2Input.value.trim();

        // Validate input
        if (!fighter1 || !fighter2) {
            showError('Please enter both fighter names');
            return;
        }

        // Show loading state
        loadingDiv.classList.remove('hidden');
        resultDiv.classList.add('hidden');
        errorDiv.classList.add('hidden');

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    fighter1: fighter1,
                    fighter2: fighter2
                })
            });

            const data = await response.json();

            if (data.status === 'error') {
                showError(data.error);
                return;
            }

            // Display results
            predictionText.textContent = data.prediction;
            fighter1EloDiv.textContent = `${fighter1} (Elo: ${Math.round(data.fighter1_elo)})`;
            fighter2EloDiv.textContent = `${fighter2} (Elo: ${Math.round(data.fighter2_elo)})`;

            loadingDiv.classList.add('hidden');
            resultDiv.classList.remove('hidden');
        } catch (error) {
            showError('Failed to connect to the prediction server. Please make sure the backend is running.');
        }
    });

    function showError(message) {
        loadingDiv.classList.add('hidden');
        resultDiv.classList.add('hidden');
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    }
});