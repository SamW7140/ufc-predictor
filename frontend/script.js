// API Configuration
const API_BASE_URL = window.location.origin;

// State Management
let allFighters = [];
let weightClasses = [];
let currentPrediction = null;
let comparisonChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadWeightClasses();
    loadFighters();
    loadStats();
    loadPredictionHistory();
    setupEventListeners();
    
    // Initial console effect
    console.log("RETRO PREDICTOR SYSTEM INITIALIZED");
});

// Event Listeners
function setupEventListeners() {
    document.getElementById('predictBtn').addEventListener('click', makePrediction);
    document.getElementById('toggle-details').addEventListener('click', toggleModelDetails);
    document.getElementById('save-prediction').addEventListener('click', savePrediction);
    document.getElementById('clear-history').addEventListener('click', clearHistory);
    document.getElementById('weight-class').addEventListener('change', handleWeightClassChange);

    setupFighterAutocomplete('fighter1');
    setupFighterAutocomplete('fighter2');
}

// Load Overall Stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        const data = await response.json();

        document.getElementById('total-fights').textContent = data.total_fights || '0';
        document.getElementById('total-fighters').textContent = data.total_fighters || '0';
        document.getElementById('weight-classes-count').textContent = data.weight_classes || '0';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load Weight Classes
async function loadWeightClasses() {
    try {
        const response = await fetch(`${API_BASE_URL}/weight-classes`);
        const data = await response.json();
        weightClasses = data.weight_classes || [];

        const select = document.getElementById('weight-class');
        select.innerHTML = '<option value="All">ALL CLASSES</option>';

        weightClasses.forEach(wc => {
            if (wc !== 'Unknown') {
                const option = document.createElement('option');
                option.value = wc;
                option.textContent = wc.toUpperCase();
                select.appendChild(option);
            }
        });
    } catch (error) {
        console.error('Error loading weight classes:', error);
    }
}

// Load Fighters
async function loadFighters() {
    const weightClass = document.getElementById('weight-class').value;
    const url = weightClass === 'All'
        ? `${API_BASE_URL}/fighters`
        : `${API_BASE_URL}/fighters?weight_class=${encodeURIComponent(weightClass)}`;

    try {
        const response = await fetch(url);
        const data = await response.json();
        allFighters = data.fighters || [];
    } catch (error) {
        console.error('Error loading fighters:', error);
    }
}

function handleWeightClassChange() {
    loadFighters();
    document.getElementById('fighter1').value = '';
    document.getElementById('fighter2').value = '';
}

// Autocomplete Setup
function setupFighterAutocomplete(inputId) {
    const input = document.getElementById(inputId);
    const suggestionsDiv = document.getElementById(`${inputId}-suggestions`);

    input.addEventListener('input', function() {
        const value = this.value.toLowerCase();
        suggestionsDiv.innerHTML = '';

        if (value.length < 2) {
            suggestionsDiv.style.display = 'none';
            return;
        }

        const filtered = allFighters.filter(fighter =>
            fighter.toLowerCase().includes(value)
        ).slice(0, 10);

        if (filtered.length === 0) {
            suggestionsDiv.style.display = 'none';
            return;
        }

        filtered.forEach(fighter => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.textContent = fighter;
            div.addEventListener('click', function() {
                input.value = fighter;
                suggestionsDiv.innerHTML = '';
                suggestionsDiv.style.display = 'none';
            });
            suggestionsDiv.appendChild(div);
        });

        suggestionsDiv.style.display = 'block';
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target !== input && e.target !== suggestionsDiv) {
            suggestionsDiv.style.display = 'none';
        }
    });
}

// Make Prediction
async function makePrediction() {
    const fighter1 = document.getElementById('fighter1').value.trim();
    const fighter2 = document.getElementById('fighter2').value.trim();
    let weightClass = document.getElementById('weight-class').value;
    const btn = document.getElementById('predictBtn');
    const resultDiv = document.getElementById('prediction-result');

    if (!fighter1 || !fighter2) {
        alert('ERROR: INPUT BOTH FIGHTERS');
        return;
    }

    if (fighter1.toLowerCase() === fighter2.toLowerCase()) {
        alert('ERROR: SAME FIGHTER SELECTED');
        return;
    }

    if (weightClass === 'All') {
        weightClass = '';
    }

    // UI Loading State
    btn.textContent = 'COMPUTING...';
    btn.disabled = true;
    resultDiv.style.display = 'none';

    try {
        // Load fighter comparison first
        await loadFighterComparison(fighter1, fighter2);

        // Make prediction
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                fighter1: fighter1,
                fighter2: fighter2,
                weight_class: weightClass
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Prediction failed');
        }

        const data = await response.json();
        currentPrediction = {
            fighter1,
            fighter2,
            ...data,
            timestamp: new Date().toISOString()
        };

        displayPrediction(data, fighter1, fighter2);
    } catch (error) {
        alert(`SYSTEM ERROR: ${error.message}`);
    } finally {
        btn.textContent = 'INITIATE PREDICTION SEQUENCE';
        btn.disabled = false;
    }
}

// Load Fighter Comparison
async function loadFighterComparison(fighter1, fighter2) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/compare/${encodeURIComponent(fighter1)}/${encodeURIComponent(fighter2)}`);

        if (!response.ok) {
            throw new Error('Failed to load comparison data');
        }

        const data = await response.json();
        displayFighterComparison(data);
    } catch (error) {
        console.error('Error loading fighter comparison:', error);
    }
}

function displayFighterComparison(data) {
    const f1 = data.fighter1;
    const f2 = data.fighter2;

    // Populate Tale of the Tape
    const tape = document.getElementById('tale-of-tape');
    tape.innerHTML = `
        <div class="tape-cell tape-label">METRIC</div>
        <div class="tape-cell tape-label" style="color: var(--retro-green)">${f1.name}</div>
        <div class="tape-cell tape-label" style="color: var(--retro-red)">${f2.name}</div>

        <div class="tape-cell">RECORD</div>
        <div class="tape-cell">${f1.career_wins}-${f1.career_losses}</div>
        <div class="tape-cell">${f2.career_wins}-${f2.career_losses}</div>

        <div class="tape-cell">WIN RATE</div>
        <div class="tape-cell">${(f1.win_rate * 100).toFixed(1)}%</div>
        <div class="tape-cell">${(f2.win_rate * 100).toFixed(1)}%</div>

        <div class="tape-cell">STRIKES/MIN</div>
        <div class="tape-cell">${f1.avg_strikes.toFixed(2)}</div>
        <div class="tape-cell">${f2.avg_strikes.toFixed(2)}</div>

        <div class="tape-cell">TAKEDOWNS</div>
        <div class="tape-cell">${f1.avg_takedowns.toFixed(2)}</div>
        <div class="tape-cell">${f2.avg_takedowns.toFixed(2)}</div>
    `;

    // Create radar chart
    createComparisonChart(f1, f2);
}

function createComparisonChart(fighter1, fighter2) {
    const ctx = document.getElementById('comparisonChart');

    // Destroy existing chart if any
    if (comparisonChart) {
        comparisonChart.destroy();
    }

    // Normalize values
    const maxWinRate = Math.max(fighter1.win_rate, fighter2.win_rate) || 1;
    const maxFights = Math.max(fighter1.career_fights, fighter2.career_fights) || 1;
    const maxStrikes = Math.max(fighter1.avg_strikes, fighter2.avg_strikes) || 1;
    const maxTakedowns = Math.max(fighter1.avg_takedowns, fighter2.avg_takedowns) || 1;
    const maxKnockdowns = Math.max(fighter1.avg_knockdowns, fighter2.avg_knockdowns) || 1;

    Chart.defaults.color = '#33ff00';
    Chart.defaults.borderColor = '#222';

    comparisonChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['WIN RATE', 'EXP', 'STRIKING', 'TAKEDOWNS', 'KNOCKDOWNS'],
            datasets: [{
                label: fighter1.name,
                data: [
                    (fighter1.win_rate / maxWinRate) * 100,
                    (fighter1.career_fights / maxFights) * 100,
                    (fighter1.avg_strikes / maxStrikes) * 100,
                    (fighter1.avg_takedowns / maxTakedowns) * 100,
                    (fighter1.avg_knockdowns / maxKnockdowns) * 100
                ],
                backgroundColor: 'rgba(51, 255, 0, 0.2)',
                borderColor: '#33ff00',
                borderWidth: 2,
                pointBackgroundColor: '#33ff00'
            }, {
                label: fighter2.name,
                data: [
                    (fighter2.win_rate / maxWinRate) * 100,
                    (fighter2.career_fights / maxFights) * 100,
                    (fighter2.avg_strikes / maxStrikes) * 100,
                    (fighter2.avg_takedowns / maxTakedowns) * 100,
                    (fighter2.avg_knockdowns / maxKnockdowns) * 100
                ],
                backgroundColor: 'rgba(255, 51, 51, 0.2)',
                borderColor: '#ff3333',
                borderWidth: 2,
                pointBackgroundColor: '#ff3333'
            }]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    angleLines: { color: '#333' },
                    grid: { color: '#333' },
                    pointLabels: { font: { family: 'VT323', size: 14 } },
                    ticks: { display: false }
                }
            },
            plugins: {
                legend: {
                    labels: { font: { family: 'VT323', size: 14 } }
                }
            }
        }
    });
}

// Display Prediction
function displayPrediction(data, fighter1, fighter2) {
    const resultDiv = document.getElementById('prediction-result');
    const winnerDisplay = document.getElementById('predicted-winner');
    const probBar = document.getElementById('probability-bar');
    const probValue = document.getElementById('probability-value');
    const methodDisplay = document.getElementById('predicted-method');
    const modelDetails = document.getElementById('model-details');

    // Winner
    winnerDisplay.textContent = data.winner;
    winnerDisplay.style.color = data.winner === fighter1 ? 'var(--retro-green)' : 'var(--retro-red)';

    // Probability
    const confidence = data.confidence_level * 100;
    probBar.style.width = `${confidence}%`;
    probValue.textContent = `${confidence.toFixed(1)}% PROBABILITY`;

    // Method (if available)
    if (data.model_details && data.model_details.prediction_method) {
        methodDisplay.textContent = data.model_details.prediction_method.toUpperCase();
    } else {
        methodDisplay.textContent = 'N/A';
    }

    // Model Details
    if (data.model_details) {
        modelDetails.innerHTML = `
            <p>RED MODEL CONFIDENCE: ${(data.model_details.red_model_confidence * 100).toFixed(1)}%</p>
            <p>BLUE MODEL CONFIDENCE: ${(data.model_details.blue_model_confidence * 100).toFixed(1)}%</p>
            <p>RANDOMIZED ORDER: ${data.fighter_order_randomized ? 'YES' : 'NO'}</p>
        `;
    }

    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

function toggleModelDetails() {
    const details = document.getElementById('model-details');
    const btn = document.getElementById('toggle-details');
    
    if (details.style.display === 'none') {
        details.style.display = 'block';
        btn.textContent = 'HIDE RAW DATA';
    } else {
        details.style.display = 'none';
        btn.textContent = 'VIEW RAW DATA';
    }
}

// Prediction History
function savePrediction() {
    if (!currentPrediction) return;

    let history = JSON.parse(localStorage.getItem('retroPredictionHistory') || '[]');
    history.unshift(currentPrediction);

    if (history.length > 10) history = history.slice(0, 10);

    localStorage.setItem('retroPredictionHistory', JSON.stringify(history));
    loadPredictionHistory();
    alert('LOG SAVED TO MEMORY BANK');
}

function loadPredictionHistory() {
    const history = JSON.parse(localStorage.getItem('retroPredictionHistory') || '[]');
    const historyDiv = document.getElementById('prediction-history');
    const clearBtn = document.getElementById('clear-history');

    if (history.length === 0) {
        historyDiv.innerHTML = '<div style="text-align: center; color: #555;">NO LOGS FOUND</div>';
        clearBtn.style.display = 'none';
        return;
    }

    historyDiv.innerHTML = history.map(pred => `
        <div style="border-bottom: 1px dashed #333; padding: 10px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--retro-green)">WIN: ${pred.winner}</span>
                <span style="color: #666">${new Date(pred.timestamp).toLocaleDateString()}</span>
            </div>
            <div style="font-size: 0.9rem; color: #aaa;">
                ${pred.fighter1} vs ${pred.fighter2}
            </div>
        </div>
    `).join('');

    clearBtn.style.display = 'inline-block';
}

function clearHistory() {
    if (confirm('PURGE ALL LOGS?')) {
        localStorage.removeItem('retroPredictionHistory');
        loadPredictionHistory();
    }
}
