# 📊 Epitech Pool -- Notebook Graph Generator

A Jupyter Notebook tool to analyze Pool results and automatically
generate student and promotion statistics graphs.

------------------------------------------------------------------------

## 📚 Dependencies

This project uses the following libraries:

-   **matplotlib** -- Graph generation\
-   **Jupyter Notebook** -- Notebook execution\
-   **NumPy** -- Mathematical operations\
-   **Pandas** -- Dataset processing

All dependencies are listed in `requirements.txt`.

------------------------------------------------------------------------

## ⚙️ Installation

1.  **Clone the repository**

``` bash
git clone <repository_url>
cd <repository_name>
```

2.  **Create a virtual environment**

``` bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3.  **Install dependencies**

``` bash
pip install -r requirements.txt
```

4.  **Run Jupyter Notebook**

``` bash
jupyter notebook
```

------------------------------------------------------------------------

## ▶️ Running the Notebook

1.  Create a `datasets` folder at the root of the repository.
2.  Add your Pool CSV datasets inside this folder.

You can download tested datasets from:\
👉 https://hermes.epitest.eu/\
Go to the results page and click on **"CSV (All instances)"**.

⚠️ You need at least **two Pool days datasets** for the graphs to work
properly.

3.  Open `progression.ipynb`.
4.  Click **Run All**.
5.  When prompted, copy/paste the notebook link displayed in the
    terminal if required.

You should now have all graphs generated automatically.

------------------------------------------------------------------------

## 🚀 Features

-   ✅ Generate cleaned daily results in the format:\
    `[login, percentage]`

-   📈 Generate a chart showing the **average promotion percentage per
    day**

-   👨‍🎓 Generate an individual chart for each student showing their
    progression across days\
    → Saved in the `plot_students/` folder

-   📊 Generate a bar chart highlighting the **three hardest Pool days**

------------------------------------------------------------------------

## 📁 Project Structure

    .
    ├── datasets/
    ├── plot_students/
    ├── progression.ipynb
    ├── requirements.txt
    └── README.md
