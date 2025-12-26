# UFC Fight Predictor

**Solving the "Red Corner" bias with dual-perspective Machine Learning.**

[Live Demo](https://samw7140.github.io/ufc-predictor/) · [API Docs](https://www.google.com/search?q=/api/docs) · [Case Study](https://www.google.com/search?q=CASE_STUDY.md) · [Report Bug](https://github.com/your-username/ufc-predictor/issues)

---

## Highlights

* **Dual-Perspective ML** - Eliminates positional bias with a two-model approach
* **Interactive Visualizations** - Radar charts for fighter comparison
* **Theme Support** - Responsive UI with dark and light modes
* **Real-time Stats** - 7,500+ fights analyzed across all weight classes
* **Production Ready** - Docker-compatible, CI/CD, and comprehensive testing

---

## The Problem: Positional Bias

In the UFC, the "Red Corner" is traditionally reserved for the higher-ranked fighter or the favorite. Standard Machine Learning models often fall into a trap: they learn that the Red Corner wins more often, creating a positional bias rather than analyzing the actual matchup.

**The Solution:** I developed a dual-model system that evaluates every fight twice—once from each perspective—and averages the confidence levels. This ensures the prediction is based on performance metrics, not just which name is listed first in the data.

---

## Core Tech Stack

* **Backend:** Python, Flask (CORS-enabled)
* **ML:** Scikit-learn (Dual-model architecture), Pandas, Joblib
* **Frontend:** Vanilla JS, CSS3 (Modern UI with Grid/Flexbox)
* **Data:** 7,500+ historical fights analyzed

---

## Key Features

### 1. The Prediction Engine

* **Dual-Perspective ML:** Uses two separate models (Red-Perspective and Blue-Perspective). The final output is a confidence-weighted average, effectively neutralizing the favorite bias.
* **Confidence Scoring:** Provides a probability percentage based on model certainty rather than a simple binary outcome.
* **Feature Engineering:** Calculates statistical deltas in striking accuracy, takedown defense, and reach to determine how styles clash.

### 2. Weight Class Logic

* **Dynamic Filtering:** The UI updates fighter lists based on the selected weight class to prevent unrealistic matchups (e.g., a Flyweight vs. a Heavyweight).
* **Auto-Detection:** Suggests the appropriate weight class based on the fighters' historical competition data.

### 3. User Experience

* **Responsive Design:** Fully optimized for mobile devices.
* **Real-time Search:** Optimized autocomplete functionality for finding fighters in a database of thousands.

---

## Getting Started

### Prerequisites

* Python 3.9+
* Virtual environment (recommended)

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/SamW7140/ufc-predictor.git
cd ufc-predictor

```


2. **Install dependencies**
```bash
pip install -r requirements.txt

```


3. **Run the server**
```bash
python backend/app.py

```


The application will be live at `http://localhost:5000`.

---

## How the Model Works

Instead of a single pass/fail check, the pipeline follows these steps:

1. **Deltas:** Calculate the statistical gap between Fighter A and Fighter B.
2. **Symmetry Check:** Pass the data through the Red Model (Fighter A as favorite) and the Blue Model (Fighter A as underdog).
3. **Weighted Average:** If the Red Model is 80% sure and the Blue Model is 60% sure, the system weights the more confident model more heavily to produce the final result.

---

## Project Structure

* `backend/`: Flask API and .joblib model files.
* `frontend/`: Main web interface and assets.
* `docs/`: Static demo files for GitHub Pages deployment.
* `.github/workflows/`: CI/CD pipelines for Azure and GitHub Pages.

---

## Future Roadmap

* **Head-to-Head Analysis:** Factoring in previous matchups between the same fighters.
* **Live Data Integration:** Automating scrapers to pull live odds and updated stats from UFC.com.
* **Stylistic Matchups:** Adding categorical weights for different fighting styles (e.g., Grappler vs. Striker).

**Developed by Sam Wale-Bogunjoko**
*Data Science Student at Penn State University*

---

Would you like me to help you refine the **API Documentation** or the **Case Study** to match this professional tone?
