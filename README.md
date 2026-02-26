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

## 🔐 Environment Variables

The project uses a `.env` file for API authentication (Hermes API credentials).

1. **Create a `.env` file from the example**

```bash
cp .env.example .env
```

Then edit `.env` with your actual credentials:

```bash
PAT=your_pat_here
PAT_ID=your_pat_id_here
HERMES_ENDPOINT=https://api.epitest.eu/api/
```

### Available Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PAT` | Personal Access Token | **Yes** | - |
| `PAT_ID` | PAT identifier | **Yes** | - |
| `HERMES_ENDPOINT` | Hermes API endpoint | No | `https://api.epitest.eu/api/` |

**Notes:**
- `PAT` and `PAT_ID` are obtained from your Epitech account (Profile → API Tokens)
- These tokens are used for all API calls to fetch student results
- ⚠️ **Never commit the `.env` file** to version control. It's already in `.gitignore`

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

### Data Sources

The dashboard supports 3 data sources (selectable in the sidebar):

| Source | Description | Requirements |
|--------|-------------|--------------|
| **CSV** | Load from local CSV files in `datasets/` folder | CSV files in `datasets/` |
| **API** | Fetch live data from Hermes API | `.env` file with credentials |
| **Sync** | Synchronize CSV files from API | `.env` file with credentials |

### Local (without Docker)

```bash
# Standard mode
streamlit run dashboard.py

# With custom port
streamlit run dashboard.py --server.port 8502
```

### With Docker

```bash
# Build and run (with environment variables)
docker-compose up --build

# Or detached mode
docker-compose up -d --build
```

**Docker with environment variables:**

If your `.env` file is not automatically loaded, pass variables explicitly:

```bash
# Option 1: Export before docker-compose
export HERMES_EMAIL=your.email@epitech.eu
export HERMES_PASSWORD=your_password
docker-compose up -d --build

# Option 2: Create a docker-compose.override.yml (not committed)
```

The dashboard is accessible at `http://localhost:8501`

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
- 🔌 **Hermes API integration** – Fetch live data directly from Epitech's API
- 🕵️ **Suspicious submissions detection** – 4 algorithms to detect cheating patterns:
  - **Copieurs** – Students with similar scores across multiple days
  - **Pics isolés** – Isolated high scores (>70%) surrounded by low scores (<30%)
  - **Montagnes russes** – Rapid alternations indicating selective cheating
  - **Copies collectives** – Clusters of students with identical scores
- 🧪 **Unit tests** – Comprehensive test suite with pytest (16 tests)
- 🔄 **CI/CD** – GitHub Actions workflow for automated testing

---

## 🗺️ Roadmap

### ✅ Completed
- 🔄 Automatic dataset retrieval from Hermes
- 🕵️ Suspicious behavior detection algorithms
- 🧪 Unit tests with pytest
- 🔄 CI/CD with GitHub Actions

### 🚧 In Progress / Planned
- 📊 Export suspicious reports (PDF/Excel)
- 🔌 REST API (Nest.js backend serving stats + graphs)
- 📱 Email alerts for new suspicious patterns
- 📈 Historical tracking (week-over-week comparison)
- 🔐 Single Sign-On (SSO) Epitech integration

---

## 🧪 Running Tests

The project includes a comprehensive test suite with **16 tests** covering detection algorithms and API functions.

### Install test dependencies

```bash
pip install -r requirements-dev.txt
```

### Run all tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=.
```

### Run specific test file

```bash
pytest tests/test_detection.py
```

---

## 📁 Project Structure

```
.
├── .github/workflows/      # CI/CD configuration
│   └── tests.yml           # GitHub Actions workflow
├── datasets/               # CSV files (mounted volume in Docker)
├── datasets_backup/        # Backup folder for development
├── plots_students/         # Generated plots
├── tests/                  # Unit tests
│   ├── __init__.py
│   ├── pytest.ini          # pytest configuration
│   ├── test_api.py         # API tests
│   ├── test_detection.py   # Detection algorithm tests
│   └── README.md           # Test documentation
├── .env                    # Environment variables (not committed)
├── .env.example            # Environment variables template
├── dashboard.py            # Streamlit dashboard
├── hermes_api.py           # Hermes API integration
├── progression.ipynb       # Jupyter notebook
├── requirements.txt        # Full dependencies (notebook + dashboard)
├── requirements-dashboard.txt  # Light dependencies (dashboard only)
├── requirements-dev.txt    # Development dependencies (tests)
├── Dockerfile              # Docker image
├── docker-compose.yml      # Docker orchestration
└── README.md
```
