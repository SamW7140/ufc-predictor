document.addEventListener('DOMContentLoaded', () => {
    const predictBtn = document.getElementById('predictBtn');
    const fighter1Input = document.getElementById('fighter1');
    const fighter2Input = document.getElementById('fighter2');
    const weightClassSelect = document.getElementById('weight-class');
    const loadingDiv = document.getElementById('loading');
    const resultDiv = document.getElementById('result');
    const predictionText = document.getElementById('predictionText');
    const confidenceInfo = document.getElementById('confidence-info');
    const weightClassInfo = document.getElementById('weight-class-info');
    const modelDetails = document.getElementById('model-details');
    const predictionMethod = document.getElementById('prediction-method');
    const modelConfidences = document.getElementById('model-confidences');
    const fighterOrderInfo = document.getElementById('fighter-order-info');
    const toggleDetailsBtn = document.getElementById('toggle-details');
    const errorDiv = document.getElementById('error');
    
    let fighterList = [];
    let weightClassList = [];
    let currentWeightClass = 'All';

    // Fetch weight classes and populate dropdown
    async function fetchWeightClasses() {
        try {
            const response = await fetch('/weight-classes');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            weightClassList = data.weight_classes;
            
            // Populate weight class dropdown
            weightClassSelect.innerHTML = '<option value="All">All Weight Classes</option>';
            weightClassList.forEach(weightClass => {
                const option = document.createElement('option');
                option.value = weightClass;
                option.textContent = weightClass;
                weightClassSelect.appendChild(option);
            });
            
            console.log(`Loaded ${weightClassList.length} weight classes`);
        } catch (error) {
            console.error('Failed to fetch weight classes:', error);
        }
    }

    // Fetch fighter list for autocomplete (optionally filtered by weight class)
    async function fetchFighterList(weightClass = 'All') {
        try {
            const url = weightClass === 'All' ? '/fighters' : `/fighters?weight_class=${encodeURIComponent(weightClass)}`;
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (!data.fighters || !Array.isArray(data.fighters)) {
                throw new Error('Invalid fighter data received');
            }
            fighterList = data.fighters;
            console.log(`Loaded ${fighterList.length} fighters for weight class: ${weightClass}`);
            
            // Clear current fighter inputs if weight class changed
            if (weightClass !== currentWeightClass) {
                fighter1Input.value = '';
                fighter2Input.value = '';
                hideFighterWeightClasses();
            }
            currentWeightClass = weightClass;
            
        } catch (error) {
            console.error('Failed to fetch fighter list:', error);
            showError('Failed to load fighter list. Please refresh the page.');
        }
    }

    // Fetch and display fighter weight classes
    async function fetchFighterWeightClasses(fighterName, displayElement) {
        try {
            const response = await fetch(`/fighter-weight-classes/${encodeURIComponent(fighterName)}`);
            if (!response.ok) {
                displayElement.classList.add('hidden');
                return;
            }
            const data = await response.json();
            if (data.weight_classes && data.weight_classes.length > 0) {
                displayElement.innerHTML = `<strong>Weight Classes:</strong> ${data.weight_classes.join(', ')}`;
                displayElement.classList.remove('hidden');
            } else {
                displayElement.classList.add('hidden');
            }
        } catch (error) {
            console.error('Failed to fetch fighter weight classes:', error);
            displayElement.classList.add('hidden');
        }
    }

    function hideFighterWeightClasses() {
        document.getElementById('fighter1-weight-classes').classList.add('hidden');
        document.getElementById('fighter2-weight-classes').classList.add('hidden');
    }

    // Initialize autocomplete for inputs
    function initAutocomplete(input, suggestionsDiv, weightClassDiv) {
        input.addEventListener('input', () => {
            const value = input.value.toLowerCase();
            const suggestions = fighterList.filter(fighter => 
                fighter.toLowerCase().includes(value)
            );
            
            suggestionsDiv.innerHTML = '';
            
            if (suggestions.length > 0 && value.length > 0) {
                // Limit suggestions to first 10 for performance
                suggestions.slice(0, 10).forEach(fighter => {
                    const div = document.createElement('div');
                    div.textContent = fighter;
                    div.addEventListener('click', () => {
                        input.value = fighter;
                        suggestionsDiv.classList.remove('active');
                        // Fetch and display fighter weight classes
                        fetchFighterWeightClasses(fighter, weightClassDiv);
                    });
                    suggestionsDiv.appendChild(div);
                });
                suggestionsDiv.classList.add('active');
            } else {
                suggestionsDiv.classList.remove('active');
            }
            
            // If input is cleared, hide weight classes
            if (value.length === 0) {
                weightClassDiv.classList.add('hidden');
            }
        });

        // Handle manual input (not from autocomplete)
        input.addEventListener('blur', () => {
            setTimeout(() => {
                if (input.value.trim() && fighterList.includes(input.value.trim())) {
                    fetchFighterWeightClasses(input.value.trim(), weightClassDiv);
                } else if (input.value.trim()) {
                    weightClassDiv.innerHTML = '<span style="color: orange;">Fighter not found in database</span>';
                    weightClassDiv.classList.remove('hidden');
                }
            }, 100);
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !suggestionsDiv.contains(e.target)) {
                suggestionsDiv.classList.remove('active');
            }
        });

        // Show suggestions when input is focused and has value
        input.addEventListener('focus', () => {
            if (input.value.length > 0) {
                const value = input.value.toLowerCase();
                const suggestions = fighterList.filter(fighter => 
                    fighter.toLowerCase().includes(value)
                );
                if (suggestions.length > 0) {
                    suggestionsDiv.classList.add('active');
                }
            }
        });
    }

    // Weight class change handler
    weightClassSelect.addEventListener('change', () => {
        const selectedWeightClass = weightClassSelect.value;
        fetchFighterList(selectedWeightClass);
    });

    // Initialize autocomplete for both inputs
    initAutocomplete(
        fighter1Input, 
        document.getElementById('fighter1-suggestions'),
        document.getElementById('fighter1-weight-classes')
    );
    initAutocomplete(
        fighter2Input, 
        document.getElementById('fighter2-suggestions'),
        document.getElementById('fighter2-weight-classes')
    );

    // Toggle details button
    toggleDetailsBtn.addEventListener('click', () => {
        if (modelDetails.classList.contains('hidden')) {
            modelDetails.classList.remove('hidden');
            toggleDetailsBtn.textContent = 'Hide Details';
        } else {
            modelDetails.classList.add('hidden');
            toggleDetailsBtn.textContent = 'Show Details';
        }
    });

    // Initialize data
    fetchWeightClasses();
    fetchFighterList();

    predictBtn.addEventListener('click', async () => {
        const fighter1 = fighter1Input.value.trim();
        const fighter2 = fighter2Input.value.trim();
        const selectedWeightClass = weightClassSelect.value === 'All' ? '' : weightClassSelect.value;

        // Validate input
        if (!fighter1 || !fighter2) {
            showError('Please enter both fighter names');
            return;
        }

        if (fighter1 === fighter2) {
            showError('Please select two different fighters');
            return;
        }

        // Show loading state
        loadingDiv.classList.remove('hidden');
        resultDiv.classList.add('hidden');
        errorDiv.classList.add('hidden');

        try {
            const requestBody = {
                fighter1: fighter1,
                fighter2: fighter2
            };
            
            if (selectedWeightClass) {
                requestBody.weight_class = selectedWeightClass;
            }

            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (data.status === 'error') {
                showError(data.error);
                return;
            }

            // Display main prediction
            predictionText.innerHTML = `<strong>${data.winner}</strong> is predicted to win with <strong>${(data.win_probability * 100).toFixed(1)}%</strong> probability`;
            
            // Display confidence and weight class info
            confidenceInfo.textContent = `Confidence Level: ${(data.confidence_level * 100).toFixed(1)}%`;
            weightClassInfo.textContent = `Weight Class: ${data.weight_class}`;
            
            // Display model details
            if (data.model_details) {
                predictionMethod.textContent = `Prediction Method: ${data.model_details.prediction_method === 'weighted' ? 'Confidence-Weighted Average' : 'Simple Average'}`;
                modelConfidences.textContent = `Red Model Confidence: ${(data.model_details.red_model_confidence * 100).toFixed(1)}%, Blue Model Confidence: ${(data.model_details.blue_model_confidence * 100).toFixed(1)}%`;
                fighterOrderInfo.textContent = `Fighter Order Randomized: ${data.fighter_order_randomized ? 'Yes' : 'No'}`;
            }

            // Reset details to hidden
            modelDetails.classList.add('hidden');
            toggleDetailsBtn.textContent = 'Show Details';

            loadingDiv.classList.add('hidden');
            resultDiv.classList.remove('hidden');
            
        } catch (error) {
            console.error('Prediction error:', error);
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