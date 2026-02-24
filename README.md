# 📊 Epitech Pool – Progression Analyzer

A tool to analyze Pool results and visualize student and promotion statistics, available as a **Jupyter Notebook** or an **interactive Streamlit dashboard**.

---

## 📚 Dependencies

This project uses the following libraries:

- **matplotlib** – Static graph generation (notebook)
- **Jupyter Notebook** – Notebook execution
- **NumPy** – Mathematical operations
- **Pandas** – Dataset processing
- **Streamlit** – Interactive web dashboard
- **Plotly** – Interactive charts (dashboard)

All dependencies are listed in `requirements.txt`.

---

## ⚙️ Installation

1. **Clone the repository**

```bash
git clone <repository_url>
cd <repository_name>
```

2. **Create a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

---

## ▶️ Getting started

1. Create a `datasets` folder at the root of the repository.
2. Add your Pool CSV datasets inside this folder (ou upload directement depuis le dashboard).

You can download tested datasets from:
👉 https://hermes.epitest.eu/
Go to the results page and click on **"CSV (All instances)"**.

⚠️ You need at least **two Pool days datasets** for the graphs to work properly.

---

## 📓 Running the Notebook

```bash
jupyter notebook
```

1. Open `progression.ipynb`.
2. Click **Run All**.
3. When prompted, copy/paste the notebook link displayed in the terminal if required.

Graphs are generated and saved automatically in `plots_students/`.

---

## 🌐 Running the Dashboard

### Local (sans Docker)

```bash
streamlit run dashboard.py
```

### Avec Docker

```bash
# Build et lancement
docker-compose up --build

# Ou en arrière-plan
docker-compose up -d --build
```

Le dashboard est accessible sur `http://localhost:8501`

**Notes Docker :**
- Les datasets sont persistés via un volume (`./datasets`)
- Les graphs générés sont sauvegardés dans `./plots_students`

---

Le dashboard comprend les sections suivantes :

| Section | Description |
|---|---|
| **KPIs** | Active students, global average, best student, hardest day |
| **Class progression** | Interactive line chart of daily class averages |
| **Individual view** | Per-student curve vs. class average + score table |
| **Hardest days** | Bar chart of the N days with the lowest scores (configurable) |
| **Leaderboard** | Students ranked by average score with color gradient |

The sidebar lets you filter students and adjust the number of hardest days shown.

---

## 🚀 Features

- ✅ Generate cleaned daily results in the format `[login, percentage]`
- 📁 **Upload direct de datasets** depuis le dashboard (drag & drop) – même quand vide
- 🗑️ **Clear data** – bouton pour supprimer tous les datasets en un clic
- 📈 Class average progression chart (static + interactive)
- 👨‍🎓 Individual student progression charts → saved in `plots_students/`
- 📊 Bar chart highlighting the hardest Pool days
- 🌐 Interactive Streamlit dashboard with Plotly charts and filters
- 🐳 **Docker support** – déploiement facile avec `docker-compose`

---

## 🗺️ Roadmap

- 🔄 Automatic dataset retrieval from Hermes
- 🔌 REST API (Nest.js backend serving stats + graphs)
- 📁 Automatic report generation (PDF summary per promotion)

---

## 📁 Project Structure

```
.
├── datasets/               # CSV files (mounted volume in Docker)
├── datasets_backup/        # Backup folder for development
├── plots_students/         # Generated plots
├── dashboard.py            # Streamlit dashboard
├── progression.ipynb       # Jupyter notebook
├── requirements.txt        # Full dependencies (notebook + dashboard)
├── requirements-dashboard.txt  # Light dependencies (dashboard only)
├── Dockerfile              # Docker image
├── docker-compose.yml      # Docker orchestration
└── README.md
```
