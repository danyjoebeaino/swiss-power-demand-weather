# AnSeqDa – Getting started (for the new team member)

Welcome to the project! This file explains how to set up the project on your machine, where we are, what comes next, and how we work together with Git.

**Project:** *Analyse et prévision de la consommation électrique en Suisse (2009–2025)*
**Research question:** Can we accurately predict Swiss daily electricity consumption, and how much does temperature improve the forecast?

> 📖 The full history of the project (decisions, problems solved, results, code) is in **`journal_projet_AnSeqDa.md`**. Read sections **0** (handover), **8** (problems), **9** (decisions) and **14** (next steps) first.

---

## 1. Setup (once)

### 1.1 Accept the GitHub invitation
You will receive an email invitation to the private repository. Accept it (or go to the repo page on GitHub and accept it there).

### 1.2 Install Git and introduce yourself
```bash
sudo apt install git            # Ubuntu/Debian (on macOS: xcode-select --install; on Windows: install "Git for Windows")
git config --global user.name "Your Name"
git config --global user.email "your@email"   # same email as your GitHub account
```

### 1.3 Download (clone) the project
```bash
git clone <REPO-URL>            # the URL from the green "Code" button on GitHub
cd <repo-folder>
```

> **Login:** GitHub no longer accepts your password in the terminal. The easiest way is the GitHub CLI: `sudo apt install gh` then `gh auth login` (choose HTTPS, log in with the browser). Alternatively, create a *Personal Access Token* on GitHub (Settings → Developer settings) and paste it when Git asks for a password.

### 1.4 Create the Python environment
```bash
python3 -m venv .venv
source .venv/bin/activate       # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook
```
We use **Python 3.14** and **pandas 3.0**. Please use the same versions: some pandas 3.0 API changes matter (e.g. `day_of_year` instead of `dayofyear`).

---

## 2. What is in the repository

```
Projet/
├── data/processed/          cleaned data (raw data is NOT in the repo)
│   ├── dataset_daily.csv    ← THE file to start from (6,209 days × 6 columns, no missing values)
│   ├── swissgrid_daily.csv
│   └── temperature_daily.csv
├── figures/                 saved plots for the presentation
├── notebooks/
│   ├── 01_cleaning.ipynb    Swissgrid cleaning (documentation only – needs raw data)
│   ├── 02_temperature.ipynb MeteoSwiss + holidays + final dataset (documentation only – needs raw data)
│   └── 03_exploration.ipynb exploration – runs from dataset_daily.csv
├── journal_projet_AnSeqDa.md  project log
├── requirements.txt
└── .gitignore
```

⚠️ **Notebooks 01 and 02 cannot be re-run**: the raw Excel/CSV files (~450 MB) are not in the repo. You don't need them – everything new starts from `data/processed/dataset_daily.csv`. If ever needed, raw data can be re-downloaded from Swissgrid ("Energy Statistic Switzerland") and MeteoSwiss (`download_meteo.py`).

### `dataset_daily.csv` columns
| Column | Meaning |
|---|---|
| `date` (index) | day, 2009-01-01 → 2025-12-31 |
| `consumption_gwh` | daily end-user consumption (GWh) – **the series to forecast** |
| `temp_ch` | mean daily temperature of 4 stations (Zürich, Bern, Geneva, Lugano), °C |
| `holiday_share` | share of the 26 cantons where the day is a public holiday (0–1) |
| `is_holiday` | True if holiday in ≥ 50 % of cantons |
| `weekday` | 0 = Monday … 6 = Sunday |
| `month` | 1–12 |

Load it like this (types must be restored, a CSV only stores text):
```python
import pandas as pd
df = pd.read_csv("../data/processed/dataset_daily.csv", index_col="date", parse_dates=True)
```
Note: `temp_anomaly` (used in notebook 03) is **not** saved in the CSV – recompute it if needed:
```python
df["temp_anomaly"] = df["temp_ch"] - df.groupby(df.index.day_of_year)["temp_ch"].transform("mean")
```

---

## 3. Where we are

| Presentation section | Status |
|---|---|
| 1. Data presentation | ✅ done |
| 2. Exploration | ✅ done (`03_exploration.ipynb`) |
| 3. Autocorrelation & stationarity | ⏭ **next** |
| 4. Smoothing (Holt-Winters) | ⬜ |
| 5. ARIMA (SARIMA / SARIMAX) | ⬜ |
| 6. LSTM | ⬜ |
| 7. Comparison & conclusion | ⬜ |

### The 5 findings that drive the modelling
1. **The calendar explains ~90 % of the variation** (MSTL: yearly 61.7 %, weekly 27.8 %, trend 3.4 %, residual 6.7 %) → models need weekly (s = 7) and yearly seasonality.
2. **Biggest unexplained errors = moving holidays** (Easter Monday, Good Friday, Ascension ≈ −30 GWh) → holiday variable needed. A weekday holiday ≈ a Sunday.
3. **The rest correlates with temperature anomalies** (r = −0.56) → temperature enters as **HDD** = max(0, T_base − T), because the relationship is a "hockey stick", not a straight line.
4. **Structural break in 2022–23:** consumption fell from ~58 TWh/year (2010–13) to ~53.4 TWh (2023–25) and stayed there → models trained on old years risk **over-predicting** the test period.
5. **Planned split:** train 2009–2022, validation 2023, test 2024–2025. Metrics: MAE, RMSE, MAPE. Baselines: naive and seasonal naive.

---

## 4. Next steps

### Step A – `notebooks/04_stationarity.ipynb` (presentation section 3)
1. Rolling mean and rolling std (30 and 365 days) → does level/variance change over time?
2. ACF and PACF of the raw series (`statsmodels.graphics.tsaplots`): lags up to ~60 (weekly peaks at 7, 14, 21…) and up to ~400 (yearly cycle).
3. Stationarity tests: **ADF** (H0 = non-stationary) and **KPSS** (H0 = stationary) – use both.
4. Differencing: weekly `y - y.shift(7)`, then if needed a first difference; redo ACF/PACF + tests after each step.
5. Propose SARIMA orders (p, d, q)(P, D, Q)₇ from the differenced ACF/PACF.
6. Write down the final decision on the train/validation/test split given the 2022–23 break.

### Step B – Feature engineering
- HDD: choose the base temperature (~16–18 °C) from the consumption-vs-temperature scatter.
- "Christmas period" variable (24 Dec – 2 Jan) and bridge days (Friday after Ascension).
- Lags (t−1, t−7, t−365) and rolling means (for the LSTM).

### Step C – Models (simple → complex), all evaluated on the same test period
Baselines → Holt-Winters → SARIMA (+ Fourier terms for the yearly cycle) → SARIMAX (HDD + holidays) → LSTM → comparison table + conclusion.

**After each step, update `journal_projet_AnSeqDa.md`** (what was done, results, problems, decisions) so the log stays the single source of truth.

---

## 5. How to use Git (day-to-day)

### The idea in one minute
- The **repository on GitHub** is the shared version.
- Your **clone** is your local copy.
- **commit** = save a snapshot of your changes *on your machine*.
- **push** = send your commits to GitHub.
- **pull** = get the other person's commits from GitHub.

### Every work session
```bash
cd <repo-folder>
source .venv/bin/activate
git pull                      # 1. ALWAYS start by getting the latest version

jupyter notebook              # 2. work...

git status                    # 3. see what you changed
git add notebooks/04_stationarity.ipynb figures/   # select what to save (or "git add ." for everything)
git commit -m "Stationarity: ACF/PACF and ADF/KPSS on raw series"
git push                      # 4. send it to GitHub
```

### Useful commands
| Command | What it does |
|---|---|
| `git status` | Shows changed / new files and what is selected for the next commit |
| `git diff` | Shows line-by-line changes not yet selected |
| `git log --oneline` | History of commits |
| `git restore <file>` | Throws away your local changes to a file (⚠️ cannot be undone) |
| `git pull` | Downloads and merges the latest commits from GitHub |

### Good commit messages
Short, say *what* changed: `"Add HDD feature with base 17 °C"`, `"SARIMA(1,0,1)(1,1,1)7 baseline"`. Not `"update"` or `"stuff"`.

### Rules to avoid trouble (important with notebooks!)
1. **Pull before you start, push when you stop.** Small, frequent commits are better than one huge one.
2. **Never work on the same notebook at the same time.** Notebooks are big JSON files; Git cannot merge two people's edits of the same notebook cleanly. Each new step = a new notebook, and we tell each other who works on which one.
3. **Before committing a notebook: Kernel → Restart & Run All.** It must run top to bottom without errors.
4. **Don't commit** `.venv/`, raw data, or huge files (GitHub refuses files > 100 MB). `.gitignore` already handles the usual ones – check with `git status` before `git add .`.
5. New Python package? Install it, then update the list and commit it:
   ```bash
   pip install <package>
   pip freeze > requirements.txt
   ```
   The other person then runs `pip install -r requirements.txt` after pulling.

### If `git push` is rejected
Message like *"Updates were rejected because the remote contains work that you do not have"* → the other person pushed in the meantime. Do:
```bash
git pull
git push
```

### If `git pull` reports a CONFLICT
Both of you changed the same lines of the same file.
- **Text file (`.md`, `.py`):** open the file, find the blocks between `<<<<<<<` and `>>>>>>>`, keep the right version, delete the markers, then:
  ```bash
  git add <file>
  git commit -m "Resolve merge conflict in <file>"
  git push
  ```
- **Notebook:** easiest is to keep one whole version: `git checkout --theirs <notebook>` (theirs) or `git checkout --ours <notebook>` (yours), then `git add` + `git commit`. Then redo the lost changes by hand. (This is why rule 2 matters.)
- When in doubt: **stop and ask** before forcing anything. Never use `git push --force`.

---

## 6. Reminders for the report
- Cite MeteoSwiss for temperature data ("Source: MeteoSwiss").
- No dual-y-axis charts: use stacked plots with a shared x-axis.
- Every modelling choice should be justified by a finding in the data (see section 3 above).
- Using *observed* temperature in the test period is optimistic (in reality only forecasts exist) – mention it as a limitation.
