# Project log – AnSeqDa (Analysis of Sequential Data)

*Record of everything decided, done and found so far. Last update: 22 November 2026 – section 6 COMPLETE (LSTM ensemble test MAE 3.19, behind SARIMAX + HDD 2.50); next = section 7 comparison + report; section 5: SARIMAX + calendar + Fourier + HDD test MAE 2.51 GWh / 1.75 %; temperature cuts error by 21 % (14 % with 1 °C forecast error); next = LSTM (section 6) and comparison; feature engineering COMPLETE: `dataset_features.csv` saved (6,209 × 22); HDD base = 16.5 °C; forecasting task fixed = day-ahead; Youssef takes baselines + Holt-Winters.*

---

## 0. Handover – where we are and how to resume

### Status at a glance
| Presentation section | Status | Notebook |
|---|---|---|
| 1. Data presentation | ✅ material ready (sources, cleaning, problems solved) | `01_cleaning.ipynb`, `02_temperature.ipynb` |
| 2. Exploration | ✅ complete | `03_exploration.ipynb` |
| 3. Autocorrelation & stationarity | ✅ complete (17 Nov) | `04_stationarity.ipynb` |
| – Feature engineering | ✅ complete (21 Nov) | `05_features.ipynb` → `dataset_features.csv` |
| 4. Smoothing (Holt-Winters) + baselines | ✅ complete (21 Nov) – HW test MAE 4.05 GWh (2.85 %) | `06_baselines_holtwinters.ipynb` |
| 5. ARIMA (SARIMA / SARIMAX) | ✅ complete (21 Nov) – best model test MAE 2.51 GWh (1.75 %) | `07_sarima.ipynb` |
| 6. LSTM | ✅ complete (22 Nov) – ensemble test MAE 3.19 (does not beat SARIMAX + HDD 2.50) | `08_lstm.ipynb` |
| 7. Comparison & conclusion | ⏭ **in progress – Danyjoe** (from 22 Nov) | `09_comparison.ipynb` |

### Team and repository
- GitHub repo: **https://github.com/danyjoebeaino/swiss-power-demand-weather** (MIT license; private until grading, then public for portfolio).
- Branches: `main` (shared, stable), `joe` (Youssef), `danyjoe` (Danyjoe). Work on your own branch → pull request into `main`.
- Rule: **never edit the same notebook at the same time** (notebooks don't merge).
- Onboarding guide for the colleague: `GETTING_STARTED.md` (setup, data, next steps, Git usage).
- Not in the repo (`.gitignore`): `data/raw/`, `.venv/`, `.ipynb_checkpoints/`, caches, archives.

### What you need to resume
- **One file is enough to continue:** `data/processed/dataset_daily.csv` (6,209 days × 6 columns, no missing values). Every new notebook starts from it.
- Raw data (~450 MB) is only needed to re-run notebooks 01–02; it can be re-downloaded (see section 5). Not in the repo.
- Environment: see section 4 (venv + `pip install -r requirements.txt`).
- Note: the column `temp_anomaly` is computed inside `03_exploration.ipynb` only (not saved in the CSV). Recompute it if needed (code in section 13).

### The things to know before modelling
1. **Calendar explains ~90 % of the variation** (MSTL: yearly 61.7 %, weekly 27.8 %, trend 3.4 %, residual 6.7 %) → seasonal models (s = 7, plus yearly cycle) are the base.
2. **Largest unexplained errors = moving holidays** (Easter Monday, Good Friday, Ascension: ≈ −30 GWh) → holiday variable is essential; a weekday holiday ≈ a Sunday (130.6 vs 130.3 GWh). Holidays still leave paired spikes after differencing → exogenous variable in SARIMAX.
3. **Temperature anomalies explain the rest** (r = −0.56 with the MSTL residual, holidays excluded) → temperature as HDD (non-linear, hockey stick).
4. **Structural break 2022–23:** train mean 155.3 GWh/day vs test 146.2 (≈ −9 GWh, −6 %); only ~1 GWh explained by temperature → ~8 GWh structural. **Decided handling (section 9, decisions 23–25):** SARIMA with D = 1 absorbs the level; level-based models get lag features (t−7, t−364); all final models refit on 2009–2023 before the test.
5. **Stationarity:** raw series not stationary in mean (KPSS); weekly difference (D = 1, s = 7) is enough; variance stable → no log transform. **Candidate model: SARIMA(1,0,0)(0,1,1)₇** + Fourier terms (yearly) + exogenous holidays/HDD.
6. **Yearly lag = 364 days (52 × 7, same weekday), not 365.**
7. **HDD base = 16.5 °C** (chosen on train, R² = 0.916; slope ≈ 2.95 GWh per HDD). Christmas-period and bridge-day variables built (bridge day ≈ a Saturday, −22 GWh; Christmas-period weekday −28.5 GWh vs other winter weekdays). Lags, 7-day rolling mean (ending yesterday), yesterday's HDD and 4 Fourier pairs built; all saved in `data/processed/dataset_features.csv`.
8. **Forecasting task = day-ahead:** predict tomorrow with data up to today; evaluated over all of 2023 (validation) and 2024–2025 (test). **No leakage:** only inputs known before the forecast day (calendar, temperature of the day, consumption lags; rolling means must end yesterday).

### Immediate next steps
- Danyjoe: commit + PR notebooks 06 and 07, `results/scores.csv`, figures. **Bar to beat on test: SARIMAX + calendar + Fourier + HDD, MAE 2.51 GWh, MAPE 1.75 %.** Then section 7 comparison (table/plot from `results/scores.csv`) and the report.
- Youssef: task to agree – suggested `08_lstm.ipynb` (section 6; needs `dataset_features.csv` from `main`). Youssef does not edit the journal; his findings go in his notebook summary and are merged into the journal by Danyjoe.

---

## 1. Project overview

- **Course:** TSM-AnSeqDa – Project in Analysis of Sequential Data (MSE, HES-SO)
- **Subject:** *Analyse et prévision de la consommation électrique en Suisse (2009–2025)*
- **English / GitHub title:** *Does the Weather Matter? Forecasting Daily Electricity Demand in Switzerland* (repo `swiss-power-demand-weather`)
- **Research question:** Can we accurately predict Swiss electricity consumption, and how much does weather (temperature) improve the forecast?
- **Main data:** Swissgrid – energy consumed by end users in the Swiss control block, every 15 minutes, since 2009.
- **External variables:** daily mean temperature (MeteoSwiss), Swiss public holidays (Python `holidays` library).
- **Project folder:** `/run/media/odin/New Volume/Switzerland/HES-SO/sem1/TSM-AnSeqDa/Projet` (Ubuntu)

### Why this subject
- Past project titles (natural disasters, CO in Phoenix, thermal energy in Geneva) all share the same shape: one quantity measured over time → analyse → forecast.
- Swissgrid data is official, continuous since 2009, high resolution (15 min), and has rich structure: daily, weekly and yearly cycles, holidays, COVID (2020), the 2022–23 energy crisis.
- Temperature is a natural explanatory variable (heating in winter).
- Alternatives considered: Lausanne air quality (NABEL, second choice – more gaps), Swiss tourism (monthly), MeteoSwiss climate, Lake Geneva level, bike counters.
- "Energy consumption" in general (all fuels, OFEN statistics) was rejected: mostly yearly figures → too few data points for time-series models.

### Why daily data (and not yearly)
- Yearly values would give only ~17 points: far too few for SARIMA / LSTM, and they erase the weekly and seasonal patterns.
- Daily data gives 6,209 points (2009–2025).
- Swissgrid files are *split* by year but contain 15-minute values; MeteoSwiss daily files contain one value per day for every day.

---

## 2. Comparison with the example presentation (natural disasters project)

The example presentation confirmed the expected structure: **data → exploration → ACF/stationarity → smoothing → ARIMA → LSTM → conclusion**. Our plan follows the same spirit, with these improvements:

| Weakness in the example | What we do instead |
|---|---|
| No train/test split (forecasts 2022–2031 with no real data to compare) | Hold out 2024–2025, all models evaluated on the same period |
| No baseline | Naive and seasonal-naive baselines |
| ARIMA(12,1,8) imitating seasonality with many lags | SARIMA with explicit seasonality (s = 7) + Fourier terms for the yearly cycle |
| LSTM forecast collapses to a flat line | LSTM with temperature and calendar features as inputs |
| Data quality bias (better reporting over time) | Metered electricity has no such bias |
| Inconsistent figures between plots and stats | Keep plots and numbers consistent |

**Changes to our first plan after seeing the example:** LSTM becomes required (was optional); Prophet / LightGBM become optional; report follows the course's section order.

---

## 3. Work plan

### 0. Framing
- Main horizon: daily consumption, forecast over several weeks/months (extensions: hourly day-ahead, monthly long-term).
- **Split (final, decided 17 Nov):** train 2009–2022 (5,113 days), validation 2023 (365 days), test 2024–2025 (731 days). Test now covers all of 2025 (December 2025 data became reliable in June 2026).
- Final models are refit on 2009–2023 before forecasting the test period.
- Metrics: MAE, RMSE, MAPE.

### 1. Data collection ✅
### 2. Cleaning and preparation ✅ (Swissgrid, MeteoSwiss, holidays, final dataset)
### 3. Exploratory analysis ✅
- Yearly totals vs yearly temperature; long-term trend (365-day rolling mean).
- Weekly profile (holidays excluded); monthly boxplot; holiday effect.
- MSTL decomposition (periods 7 and 365); variance shares; largest residuals.
- Residual vs temperature anomaly.
- Consumption vs temperature (hockey stick) – done in notebook 02.

### 4. Autocorrelation and stationarity ✅
- Rolling mean / std; ACF / PACF (raw and differenced); ADF and KPSS; differencing; SARIMA orders; split decision. Results in section 10.

### 5. Feature engineering (colleague)
- Calendar: weekday, month, holidays, bridge days, Christmas period.
- Heating degree days (HDD) from temperature.
- Lags (t−1, t−7, **t−364**) and rolling means.

### 6. Modelling (simple → complex)
1. Baselines: naive, seasonal naive.
2. Smoothing: Holt-Winters / ETS.
3. SARIMA(1,0,0)(0,1,1)₇ + neighbours by AIC, with Fourier terms for the yearly cycle; then SARIMAX with HDD and holidays.
4. LSTM with temperature, calendar and lag inputs.
5. Optional: Prophet, LightGBM/XGBoost.

### 7. Evaluation
- Same test period for all models (MAE, RMSE, MAPE); walk-forward validation.
- Residual diagnostics (Ljung-Box); prediction intervals.
- Limitation: using *observed* temperature in the test period is optimistic (in practice only forecasts exist).

### 8. Interpretation and report
- Which model wins; how much temperature helps; where models fail.

### Presentation structure (aligned with the course)
1. Data presentation – 2. Exploration – 3. Autocorrelation & stationarity – 4. Smoothing – 5. ARIMA (SARIMA/SARIMAX) – 6. LSTM – 7. Comparison & conclusion

### Indicative timeline (~8 weeks)
| Week | Work |
|---|---|
| 1 | Framing and data collection |
| 2 | Cleaning and preparation |
| 3 | Exploration, autocorrelation, stationarity |
| 4 | Feature engineering and baselines |
| 5 | Smoothing and SARIMA / SARIMAX |
| 6 | LSTM |
| 7 | Evaluation and comparison |
| 8 | Report and presentation |

### Notebook organisation
- `01_cleaning.ipynb` – Swissgrid cleaning and daily aggregation ✅ (needs raw data)
- `02_temperature.ipynb` – MeteoSwiss cleaning, holidays, merge into the final dataset ✅ (needs raw data)
- `03_exploration.ipynb` – exploration (section 2 of the presentation) ✅
- `04_stationarity.ipynb` – autocorrelation and stationarity (section 3) ✅
- `05_features.ipynb` – feature engineering ⏭ (colleague)
- `06_baselines_holtwinters.ipynb` – baselines + smoothing (section 4) ⏭ (Danyjoe)
- later notebooks – SARIMA/SARIMAX, LSTM, comparison (each starts from `dataset_daily.csv` or `dataset_features.csv`)

---

## 4. Environment setup

```bash
# folder structure (created inside Projet/)
mkdir -p data/{raw/{swissgrid,meteo},processed} notebooks figures

# virtual environment + packages (Ubuntu does not allow pip into system Python)
python3 -m venv .venv
source .venv/bin/activate
pip install pandas xlrd openpyxl python-calamine matplotlib jupyter holidays statsmodels
pip freeze > requirements.txt      # committed to the repo
jupyter notebook
```

```bash
# start a work session
cd "/run/media/odin/New Volume/Switzerland/HES-SO/sem1/TSM-AnSeqDa/Projet"
source .venv/bin/activate
git pull                            # get the team's latest work first
jupyter notebook
# stop: save (Ctrl+S) -> File > Shut Down (or Ctrl+C in the terminal) -> commit + push -> deactivate
```

- Python 3.14, pandas 3.0.
- `xlrd` reads old `.xls`, `openpyxl` reads `.xlsx`; `python-calamine` reads both and is ~3× faster (used for the final loading loop).

```
Projet/
├── data/
│   ├── raw/swissgrid/      17 Excel files (2009–2025), 428 MB   (not in Git)
│   ├── raw/meteo/          MeteoSwiss daily files, 22 MB          (not in Git)
│   └── processed/          cleaned CSV files
├── figures/
├── notebooks/              01–04 (+ next ones)
├── .gitignore
├── GETTING_STARTED.md      onboarding for the colleague
├── LICENSE                 MIT
├── requirements.txt
├── download_meteo.py
├── journal_projet_AnSeqDa.md
└── sujet_projet_AnSeqDa.md (course text – check before making the repo public)
```

## 4b. Git and GitHub setup (9 November)

```bash
# one-time setup
sudo apt install git gh
git config --global user.name "Danyjoe Beaino"
git config --global user.email "<github email>"
gh auth login                       # GitHub.com → HTTPS → authenticate Git → browser

# first commit and push
git init
git branch -M main
git add .                           # .gitignore must exist and be SAVED first
git status                          # check: no data/raw, no .venv, no checkpoints
git commit -m "AnSeqDa: data preparation and exploration complete"
git remote add origin https://github.com/danyjoebeaino/swiss-power-demand-weather.git
git pull origin main --allow-unrelated-histories --no-rebase   # GitHub repo already had a LICENSE
git push -u origin main
```

Daily workflow on a personal branch:
```bash
git switch danyjoe                  # (created with: git switch -c danyjoe)
git pull                            # + git merge main if main moved
# ... work ...
git add notebooks/<notebook>.ipynb figures/
git commit -m "<what changed>"
git push                            # first time: git push -u origin danyjoe
# then open a pull request danyjoe → main on GitHub
```

Check what the colleague has pushed:
```bash
git fetch
git log --oneline main..origin/joe  # empty = nothing new on his branch
```

---

## 5. Data collection

### Swissgrid
- Page: "Energy data CH" → section **"Energy Statistic Switzerland"** (one file per year).
- Downloaded 2009–2025: `.xls` for 2009–2019, `.xlsx` for 2020–2025. 2026 skipped (incomplete, not yet reliable).
- Ignored: "Control Area Balance" and "Total System Imbalance" (real-time balancing data, not consumption).
- Note for the report: the Swiss control block does not match Swiss territory exactly (includes Liechtenstein and small areas in France/Germany, excludes some Swiss grids around Laufenburg); deviation < 2 %.
- Data are published ~15 working days after month end and considered reliable after 6 months.
- No explicit open-data license found for reuse → in the public repo: cite the source, state the data belong to Swissgrid / MeteoSwiss and are used for educational purposes.

### MeteoSwiss
- Swissgrid and MeteoSwiss block downloads from Claude's environment → files downloaded manually / by script on the local machine.
- Script `download_meteo.py` (STAC API of data.geo.admin.ch, collection `ch.meteoschweiz.ogd-smn`) downloads the **daily** files (`_d_historical`, `_d_recent`) of 4 stations + the parameter description file.
- Stations: Zürich/Fluntern (SMA), Bern/Zollikofen (BER), Genève/Cointrin (GVE), Lugano (LUG).
- Column needed: **`tre200d0`** = air temperature 2 m above ground, daily mean (°C).
- File format: `;`-separated, date as `dd.mm.yyyy HH:MM`; historical file runs to 31.12.2025, recent from 01.01.2026. Parameter file is Latin-1 encoded.
- Citation required: "Source: MeteoSwiss".

### Holidays
- Python `holidays` library (nothing to download).

---

## 6. Swissgrid file structure (what we found)

- 4 sheets: `Einstellungen`, `Uebersicht`, `Zeitreihen0h15` (15-min), `Zeitreihen1h00` (hourly). We use **`Zeitreihen0h15`**.
- 21 columns in 2009, 65 in 2020 (per-canton data added). We use only:
  - column 0 → timestamp
  - column 1 → *"Summe endverbrauchte Energie Regelblock Schweiz"* (energy consumed by end users, kWh)
- Why end-user consumption and not total consumption: total consumption includes pumped-storage pumping, which follows electricity prices, not demand.
- Row 2 of the sheet contains units ("Zeitstempel", "kWh") → must be skipped.
- Rows per year: 35,040 (365 × 96), 35,136 in leap years (2012, 2016, 2020, 2024).

---

## 7. Cleaning steps – Swissgrid (notebook `01_cleaning.ipynb`)

| Lesson | What we did | Result |
|---|---|---|
| 1 | Loaded one file (2009) and inspected it | 35,040 rows, first timestamp 00:15, last = next year 00:00, no NaN |
| 2 | Studied timestamps and DST (daylight-saving time) | 2 abnormal gaps per year, duplicates in October, days of 92 and 100 values |
| 3 | Loaded and merged the 17 files | 596,064 rows, but timestamp column became `object` (mix of dates and text) |
| 3b | Diagnosed timestamp types and first/last values per file | 2021–2025 stored as text; 2025 uses start-of-interval labels |
| 3c | Parsed text dates, shifted 2025 by +15 min, rechecked gaps | Exactly 17 "+1h15" and 17 "−45 min" gaps, everything else 15 min |
| 4 | Aggregated to daily with 24-hour correction | 6,209 days, 0 missing, mean 154 GWh/day |
| 5 | Checked extremes, weekly cycle, COVID; saved daily CSV | Extremes explained, no outliers removed |

---

## 7b. Preparation steps – temperature, holidays, final dataset (notebook `02_temperature.ipynb`)

| Lesson | What we did | Result |
|---|---|---|
| 6 | Loaded one station (Bern) and inspected it | 41 columns; measurements since 1 January 1864; 6,209 rows for 2009–2025; 0 missing temperatures |
| 7 | Function `load_station()` + loaded the 4 stations side by side (`concat(axis=1)`, aligned by date) | 6,209 × 4 table, 0 missing dates, 0 missing values for every station |
| 8 | Checked correlation between stations, averaged them into `temp_ch`, saved | Correlations 0.93–0.99 → averaging justified |
| 9 | Swiss public holidays per canton (26 cantons), `holiday_share` and `is_holiday` | ~9 holidays per year (153 days over 17 years) |
| 10 | Joined consumption + temperature + holidays + calendar; scatter consumption vs temperature; saved final dataset | 6,209 × 6, 0 missing values; correlation −0.745; hockey-stick relationship |

### Station details
| Station | Code | Mean (°C) | Min | Max | Comment |
|---|---|---|---|---|---|
| Zürich / Fluntern | SMA | 10.4 | −13.5 | 27.8 | north of the Alps |
| Bern / Zollikofen | BER | 9.9 | −14.2 | 27.7 | coldest (plateau, ~550 m) |
| Genève / Cointrin | GVE | 11.6 | −9.2 | 29.5 | low altitude, lake; shorter history (smaller file) but complete for 2009–2025 |
| Lugano | LUG | 13.6 | −5.3 | 28.8 | warmest (south of the Alps, Mediterranean influence) |

### Correlation between stations
|  | SMA | BER | GVE | LUG |
|---|---|---|---|---|
| SMA | 1.000 | 0.991 | 0.979 | 0.933 |
| BER | 0.991 | 1.000 | 0.989 | 0.947 |
| GVE | 0.979 | 0.989 | 1.000 | 0.952 |
| LUG | 0.933 | 0.947 | 0.952 | 1.000 |

- North-of-Alps stations correlate ≥ 0.979 with each other.
- Least correlated pair: Zürich–Lugano (0.933) – the Alps act as a weather barrier.

### Holidays found for 2024 (share of the 26 cantons)
New Year 1.00 · Good Friday 0.88 · Easter Monday 0.73 · Ascension 1.00 · Whit Monday 0.73 · National Day 1.00 · All Saints (1 Nov) 0.50 · Christmas 1.00 · St Stephen's Day (26 Dec) 0.62

### Final dataset columns (`dataset_daily.csv`)
| Column | Meaning |
|---|---|
| `date` (index) | day, 2009-01-01 → 2025-12-31 |
| `consumption_gwh` | daily end-user consumption, 24-h corrected (GWh) |
| `temp_ch` | mean daily temperature of the 4 stations (°C) |
| `holiday_share` | share of the 26 cantons where the day is a public holiday (0–1) |
| `is_holiday` | True if holiday in ≥ 50 % of cantons |
| `weekday` | 0 = Monday … 6 = Sunday |
| `month` | 1–12 |

---

## 7c. Exploration steps (notebook `03_exploration.ipynb`)

| Lesson | What we did | Result |
|---|---|---|
| 11 | Yearly totals (TWh) and yearly mean temperature, two stacked plots; 365-day rolling mean | Slow decline (~−8 %), COVID dip 2020, rebound 2021, step down 2022–23; cold years consume more |
| 12 | Weekly profile (holidays excluded), monthly boxplot, holiday effect | Sat −13.4 %, Sun −19.6 %; winter months vary most; weekday holiday ≈ Sunday |
| 13 | MSTL decomposition (periods 7 and 365), variance shares, top-10 residuals, residual vs temperature | Calendar ≈ 90 % of variation; 9/10 largest residuals = moving holidays; corr −0.19 (raw) |
| 13b | Temperature anomaly (vs normal for that day of year), holidays excluded | corr(residual, anomaly) = **−0.559**; slope ≈ −1.5 GWh per °C of anomaly |

---

## 7d. Stationarity steps (notebook `04_stationarity.ipynb`, 17 November)

| Lesson | What we did | Result |
|---|---|---|
| 14 | `asfreq("D")`; rolling mean and std (30 and 365 days) | 30-day mean follows yearly wave (~125 → ~190) → not stationary in mean; 365-day std stable 21–24 → no transform; 30-day std spikes at Christmas/New Year |
| 15 | ACF (lags 60 and 400) and PACF (lags 60) of the raw series | Very slow decay, peaks at 7k; yearly wave (min −0.55 at ~180, max ≈ 0.8 at **364**); PACF: lags 1, 6–8, negative spikes at 7k+1 |
| 16 | ADF + KPSS with a reusable function `stationarity_tests()` | ADF −4.71 (p < 0.001) "stationary"; KPSS 0.65 (p = 0.018) "non-stationary" → difference |
| 17 | Weekly difference (D=1, s=7) and weekly + first difference (d=1); tests + std + plot | Both pass ADF and KPSS; std 23.1 → 10.4 → 7.6; paired holiday spikes remain |
| 18 | ACF/PACF of both differenced series (lags 42, ticks every 7) | Weekly diff: ACF geometric decay 0.73^k, PACF cut-off after lag 1 → AR(1); lag-7 ACF −0.17 → seasonal MA(1). d=1 adds artificial negative correlations → rejected |
| 19 | Train/validation/test split, figure and level comparison | Train 155.3, validation 146.5, test 146.2 GWh/day; ~8 GWh structural gap; validation ≈ test level |

---

## 7e. Feature engineering steps (notebook `05_features.ipynb`, from 21 November)

| Lesson | What we did | Result |
|---|---|---|
| 20 | HDD base scan 12–22 °C: regression consumption ~ weekday dummies + HDD, train 2009–2022, holidays excluded (4,987 days) | Best base **16.5 °C** (R² 0.9162); flat top 16–17 °C (0.9161–0.9157); slope 2.95 GWh per HDD (≈ the −3 GWh/°C seen in notebook 02) |
| 21 | Calendar features: `christmas_period` (24 Dec – 2 Jan) and `bridge_day` (non-holiday weekday between a holiday and an off day) | 170 Christmas days (10/year); 36 bridge days (~2/year: Fri after Ascension, 2 Jan, 31 Oct/2 Nov around All Saints, 2 Aug, 24/27/31 Dec); bridge day **139.8 GWh ≈ Saturday (140.3)** vs normal weekday 162.2; Christmas-period weekday 159.4 (raw, season-confounded) → **fair winter check: 159.9 vs 188.4 for other Dec/Jan weekdays = −28.5 GWh (−15 %)** |
| 22 | Lags (t−1, t−7, t−364), 7-day rolling mean ending yesterday, `hdd_lag1`, Fourier pairs k = 1–4 (period 365.25); Fourier-only fit on train; saved `dataset_features.csv` | NaN only at the start (364 for lag_364, 7 for lag_7/roll7, 1 for lag_1/hdd_lag1); Fourier fit follows the yearly wave (~182 winter peak, ~133 summer trough) and even a small Christmas notch; misses weekdays, holidays, cold spells and the 2022–23 level drop (by design); final file 6,209 × 22 |

---

## 7f. Baselines and Holt-Winters (notebook `06_baselines_holtwinters.ipynb`, from 21 November, Danyjoe)

| Lesson | What we did | Result |
|---|---|---|
| 23 | `evaluate()` (MAE, RMSE, MAPE) + `log_scores()` → `results/scores.csv`; naive (t−1), seasonal naive (t−7), yearly naive (t−364) on validation 2023; zoom Jan–Apr 2023 | **Seasonal naive best: MAE 7.98, RMSE 10.74, MAPE 5.37 %** (= bar to beat); yearly naive 8.97 / 11.38 / 6.26 %; naive 9.30 / 12.98 / 6.60 %. Naive is one day late (fails Mon/Sat); seasonal naive fails the 2 weeks after New Year (copies Christmas lows), one week after Easter (echo spike) and when the weather turns |
| 24 | Holt-Winters additive, s = 7, day-ahead (parameters estimated on train, then fixed and run through 2023); variants: no trend / trend / damped trend | **MAE 3.58, RMSE 5.28, MAPE 2.50 %** for all three (halves seasonal naive); α = 0.79 (level follows recent days), γ = 0.011 (weekly shape almost fixed), β ≈ 0 and damped φ 0.916 → trend useless → **keep no-trend variant**. Recovers within 1–2 days after New Year and Easter, but still misses the holiday day itself |
| 25 | Residuals of HW on 2023 (ACF, Ljung-Box lags 7/14, top-10 errors); final test 2024–2025 after refit on 2009–2023 | Ljung-Box p = 0.0004 (lag 7), 0.014 (lag 14) → structure left; top-10 errors: 5 holidays over-predicted (Christmas −30.8, Easter Mon −24.5, Ascension −24.2, Whit Mon −20.6, Good Fri −19.9), 2 rebound days after them (+18.4, +16.0), 2 Jan (−13.6), Mon 31 Jul before 1 Aug (bridge, −13.4), one cold Sunday (+14.1 at 1.4 °C) → 9/10 calendar, 1 weather. **Test: HW MAE 4.05, RMSE 5.76, MAPE 2.85 %**; seasonal naive 7.75 / 10.85 / 5.24 %; yearly naive 7.56 / 10.39 / 5.12 %; naive 9.59 / 13.08 / 6.83 %. Refit parameters stable (α 0.795, γ 0.011) |

---

## 7g. SARIMA / SARIMAX (notebook `07_sarima.ipynb`, from 21 November, Danyjoe)

| Lesson | What we did | Result |
|---|---|---|
| 26 | SARIMA(p,d,q)(0,1,1)₇ for (1,0,0), (2,0,0), (1,0,1), (1,1,1) fitted on train; AIC/BIC; day-ahead on 2023 via `res.apply()` + `get_prediction(dynamic=False)` (parameters fixed) | AIC: (1,0,0) 31955.8, (2,0,0) 31897.9, (1,0,1) 31865.7, (1,1,1) 31791.0 (d=1 not comparable). **Validation MAE: (1,0,0) 3.51 (best, MAPE 2.46 %)**, others 3.53–3.56 → **keep (1,0,0)(0,1,1)₇**. Coefficients: ar.L1 = 0.958, ma.S.L7 = −0.988, σ² = 30.4. Seasonal MA ≈ −1 cancels the weekly difference → model ≈ fixed weekly shape + very persistent level (AR 0.96) = same structure as Holt-Winters (γ ≈ 0, α 0.79) → near-identical scores (3.51 vs 3.58) |
| 27 | SARIMAX(1,0,0)(0,1,1)₇ + calendar (weekday-only: `holiday_wd` = holiday_share × weekday, `christmas_wd` excl. official holidays, `bridge_day`), then + Fourier k = 1–4; day-ahead on 2023 | **Calendar: MAE 2.96, RMSE 3.91, MAPE 2.04 %** (vs SARIMA 3.51 / 5.28: MAE −16 %, RMSE −26 %); **+ Fourier: 2.93 / 3.80 / 2.03 %** (small extra gain, kept). Coefficients: holiday_wd −27.5, christmas_wd −10.5, bridge_day −8.6 (all p < 0.001); ar.L1 0.984, ma.S.L7 −0.980; σ² 30.4 → 10.9 (−64 % one-step error variance) |
| 28 | **Research question:** same SARIMAX + calendar + Fourier, with vs without temperature (`hdd` today + `hdd_lag1`); validation 2023, then final test 2024–2025 after refit on 2009–2023 (ablation of all 4 SARIMA variants) | **Validation: 2.93 → 2.38 MAE (−19 %), RMSE 3.80 → 3.10, MAPE 2.03 → 1.67 %. Test: SARIMA 3.93 / 5.70 / 2.77 %; + calendar 3.29 / 4.25 / 2.28 %; + Fourier 3.17 / 4.11 / 2.19 %; + HDD 2.51 / 3.26 / 1.75 %** → temperature cuts test MAE by 21 %; full model −36 % vs SARIMA, −38 % vs Holt-Winters (4.05), −68 % vs seasonal naive. Of the 1.42 GWh gain over SARIMA: calendar + Fourier 0.76, temperature 0.66. Coefficients: hdd 1.38, hdd_lag1 +0.31 (inertia; ≈ 1.7 GWh per sustained HDD), ar.L1 0.984 → 0.859 (weather explains part of the 'persistence'), σ² 10.9 → 6.6 |
| 29 | Robustness: forecast-day temperature replaced by observed + N(0, σ) noise on test days (simulated weather-forecast error), same fitted model; winter 2024–25 zoom with vs without HDD | **σ = 0: 2.51; σ = 1 °C: 2.73 / 3.54 / 1.91 % (still −14 % vs no temperature 3.17); σ = 2 °C: 3.44 / 4.36 / 2.38 % (worse than no temperature, +9 %)** → the temperature gain depends on forecast quality; with a good (~1 °C) forecast most of it survives. Winter plot: both models close (calendar dominates), HDD model follows cold snaps / mild turns on the same day |

---

## 7h. LSTM (notebook `08_lstm.ipynb`, from 22 November, Danyjoe)

| Lesson | What we did | Result |
|---|---|---|
| 30 | PyTorch (CPU) installed; weekday-only calendar vars as in SARIMAX; target `d7` = y − y(t−7); scaling on train only (d7 ÷ 10.33 GWh, hdd ÷ 26.9); windows: 28 past days × 5 features + 19 day-t features (hdd, 3 calendar, 7 weekday dummies, 8 Fourier) | train 5,078 samples (first 35 days of 2009 lack history), validation 365, test 731 – every day forecast |
| 31 | `DayAheadLSTM` (LSTM 32 units over 28-day window + dense head 32 ReLU on [summary, day-t features]; 6,689 parameters); Adam lr 1e-3, batch 64, MSE, early stopping on 2023 (patience 10), seed 42 | Stopped after 67 epochs, best epoch 57; smooth curves, train MSE ≈ 0.07 vs validation ≈ 0.115 (moderate gap, validation flat from ~epoch 40). **Validation MAE 2.68, RMSE 3.41, MAPE 1.87 %** – better than HW (3.58) and SARIMAX without temperature (2.93), behind SARIMAX + HDD (2.38). Slightly optimistic (2023 used for early stopping) |
| 32 | 5 seeds with early stopping on 2023 → ensemble (mean of 5 forecasts); test: each seed retrained on 2009–2023 for its best epoch count (43–66), ensemble scored on 2024–2025; leaderboard from `results/scores.csv` | Validation: single seeds MAE 2.79 ± 0.04, **ensemble 2.71 / 3.42 / 1.89 %**. **Test: single seeds 3.27 ± 0.04, ensemble 3.19 / 4.03 / 2.20 %** → beats Holt-Winters (4.05, −21 %) and SARIMA (3.93), ties SARIMAX without temperature (3.17), **27 % worse than SARIMAX + HDD (2.50)**. Larger val→test drop than SARIMAX (+18 % vs +5 %): early-stopping optimism + weaker generalisation |

### Final test leaderboard (2024–2025, day-ahead)
| Model | MAE | RMSE | MAPE |
|---|---|---|---|
| **SARIMAX + calendar + Fourier + HDD** | **2.50** | **3.26** | **1.75 %** |
| SARIMAX + calendar + Fourier | 3.17 | 4.12 | 2.19 % |
| LSTM (ensemble of 5 seeds) | 3.19 | 4.03 | 2.20 % |
| SARIMAX + calendar | 3.29 | 4.25 | 2.28 % |
| SARIMA(1,0,0)(0,1,1)₇ | 3.93 | 5.70 | 2.77 % |
| Holt-Winters (no trend) | 4.05 | 5.76 | 2.85 % |
| Yearly naive | 7.56 | 10.39 | 5.12 % |
| Seasonal naive | 7.74 | 10.85 | 5.24 % |
| Naive | 9.59 | 13.08 | 6.83 % |
(2.50 vs 2.51 and 7.74 vs 7.75 elsewhere = rounding of the 3-decimal values in scores.csv.)

---

## 8. Problems faced and how we solved them

| # | Problem | Diagnosis | Solution |
|---|---|---|---|
| 1 | Values labelled 00:15 → next year 00:00 | Each label marks the **end** of its quarter-hour | Subtract 15 min before assigning values to a date |
| 2 | Clock changes: 92-value days (March) and 100-value days (October) | Swissgrid uses Swiss local time; 92 + 100 = 2 × 96 hid the issue in row counts | Kept all values; daily value = mean × 96 (24-hour equivalent) |
| 3 | Duplicate timestamps in October | They are two *different real hours* with the same clock label (values differ) | **Not removed**; never sort by timestamp (would mix the two hours) |
| 4 | `TypeError: str − Timestamp` in `diff()` after merge | 2021–2025 files store timestamps as **text** `dd.mm.yyyy HH:MM` | Parsed only text values with explicit `format="%d.%m.%Y %H:%M"` (avoid month/day confusion) |
| 5 | 2025 runs 00:00 → 23:45 instead of 00:15 → next year 00:00 | 2025 changed to **start-of-interval** labels | Added +15 min to 2025; proved by year boundaries (35,040 rows ending 23:45 can only be start labels) and a clean 2024→2025 boundary |
| 6 | October duplicate test did not distinguish conventions | Recent files write the switch instant (02:00 CET = 03:00 CEST) differently; same moment, two labels | Recognised the test as non-discriminating; relied on year-boundary evidence |
| 7 | March test: 2024 shows "03:00", 2025 shows "02:00" at the switch | Same physical instant written two ways | No effect on daily totals (all quarter-hours stay on the right date) |
| 8 | `NameError: pd` after kernel restart | Restart wipes memory (imports and variables) | Run All Cells / put imports in the first cell |
| 9 | Run All crashed on an early check cell | Exploration cell ran `diff()` before the fix | Removed that line and the premature `to_csv`; notebook must run top to bottom |
| 10 | Risk of shifting 2025 several times | Cells that modify data are not safe to re-run | Restart kernel + Run All after edits |
| 11 | `.agg(["first","last"])` error on a Series | Not supported on a plain Series in pandas 3.0 (works after `groupby`) | Used `.iloc[[0, -1]]` |
| 12 | Warnings: `xlrd` deprecated, `dayofyear` deprecated | pandas 3.0 API changes | `engine="calamine"`; use `day_of_year` |
| 13 | Data too big to upload (260 MB zip) | Chat upload size limit | Uploaded samples only (2009, 2020 files, Bern meteo files); full processing runs locally |
| 14 | 2013 file seemed missing | `head -30` truncated the listing | Loop check over 2009–2025 confirmed all files present |
| 15 | Geneva file is half the size of the others | Shorter measurement history (starts later) | Checked completeness for 2009–2025: 0 missing → no problem for our period |
| 16 | `holidays.Switzerland()` without a canton gives only 4 holidays/year (New Year, Ascension, 1 August, Christmas) | In Switzerland most holidays are set by each **canton** (Good Friday, Easter Monday, Whit Monday, 26 Dec missing) | Counted for each day in how many of the 26 cantons it is a holiday → `holiday_share`; `is_holiday` = share ≥ 0.5 |
| 17 | `holidays.Switzerland.subdivisions` also contains "Stadt Zurich" | Not a canton | Kept only 2-letter codes (`len(c) == 2`) → 26 cantons |
| 18 | 24 Dec, 31 Dec and the Christmas–New Year period are not official holidays but consumption is low (companies closed) | Not captured by the holiday variable; confirmed again by the yearly 30-day std spikes (lesson 14) | **Solved (21 Nov, lesson 21)** – `christmas_period` (24 Dec – 2 Jan, −28.5 GWh vs other winter weekdays) and `bridge_day` (≈ a Saturday) |
| 19 | Consumption vs temperature is not linear (flat above ~18 °C) | Heating stops above ~16–18 °C; a straight line would under-predict summer | **Planned** – heating degree days HDD = max(0, T_base − T) |
| 20 | Residual vs temperature correlation looked weak (−0.19) | Two confounders: holidays dominate the residual (±30 GWh), and the yearly cycle already contains the *normal* seasonal temperature | Excluded holidays and used the **temperature anomaly** (temp − normal for that day of year) → −0.559 |
| 21 | Consumption level dropped in 2022–23 and stayed low; test period (2024–25) is below most training data | Structural break (energy crisis, saving campaign, possibly rooftop solar); quantified in lesson 19: −9 GWh/day, ~8 structural | **Decided (17 Nov)** – keep split; SARIMA (D=1) absorbs the level; level-based models get lag features (t−7, t−364); refit on 2009–2023 before test; 2023 validation detects over-prediction |
| 22 | Fixed-date holidays (Christmas, 1 August) do not appear among the largest residuals, moving ones do | The yearly cycle learns fixed dates automatically (spikes visible in `seasonal_365`); Easter/Ascension move by up to a month | Holiday variable needed mainly for **moving** holidays; keep it for all |
| 23 | Two measures with different units on one chart (consumption and temperature per year) | A dual y-axis chart can make lines look related or not depending on the scaling | Used **two stacked plots with a shared x-axis** |
| 24 | `fig.suptitle` duplicate title on pandas boxplot | pandas adds an automatic "Boxplot grouped by…" title | `fig.suptitle("")` |
| 25 | `git add .` staged `data/raw/` and `.ipynb_checkpoints/` | `.gitignore` was open in VS Code with **unsaved** changes (● on the tab) → empty on disk | Unstaged with `git rm -r --cached data/raw notebooks/.ipynb_checkpoints`; saved `.gitignore` (Ctrl+S); committed the fix |
| 26 | First `git push` rejected ("fetch first") | GitHub repo created with an MIT LICENSE → remote not empty | `git pull origin main --allow-unrelated-histories --no-rebase`, then push |
| 27 | `FutureWarning` from `adfuller` (return type will change in statsmodels 0.16) | API change announced | Add `result_object=False` to the `adfuller(...)` call |
| 28 | Expected std to rise after adding d=1 (over-differencing check), but it fell (10.4 → 7.6) | Var of a first difference = 2σ²(1−ρ₁) < σ² when ρ₁ > 0.5; here ρ₁ ≈ 0.74 (weather spells persist) | Not a reason for d=1: ρ₁ = 0.74 is persistence, not a unit root → handled by an AR(1) term; ACF/PACF of d=1 show artificial negative correlations → d=1 rejected |
| 29 | Christmas-period effect looked tiny (159.4 vs 162.2 GWh) | Seasonal confounding: Christmas days are in winter, the 162.2 average mixes all seasons; bridge days also overlap the period | Compared with Dec/Jan weekdays only, bridge days excluded → −28.5 GWh. Lesson: always compare like with like |
| 30 | Fourier curve is the same every year (fit on 2009–2022 mean level) | Deterministic terms cannot follow a level shift → would over-predict 2023+ | Use Fourier only together with something that carries the level: D = 1 in SARIMAX, or lag / roll7 features in regression and LSTM |
| 35 | LSTM with temperature only ties SARIMAX without temperature on the test | Simple, additive, near-linear structure (fixed weekly shape, holiday shifts, linear HDD) is built into SARIMAX but must be learned by the LSTM from ~5,000 samples; early stopping on 2023 flatters validation | Report honestly: more complex ≠ better here. Optional checks: LSTM without HDD (does it use temperature?), hybrid SARIMAX + LSTM on residuals as further work |
| 34 | With simulated 2 °C forecast errors the HDD model is worse than the model without temperature | Model trained on exact temperatures trusts HDD fully (errors-in-variables); single noise draw, independent errors (real forecast errors are smaller for a 4-station daily mean and correlated) | Report the 21 % gain as an upper bound; state that it holds for ~1 °C forecasts. Extension: train/test with archived MeteoSwiss forecasts, or train on noisy temperature |
| 33 | SARIMAX coefficients smaller than hand-measured effects (Christmas −10.5 vs −28.5; bridge −8.6 vs −22) | Coefficients are *extra* effects given the rest of the model: 26 Dec / 2 Jan are partly covered by `holiday_wd` (holiday_share > 0), the very persistent error (AR 0.98) absorbs multi-day lows, and the hand bridge-day figure compared May days with an all-year average (season confounding) | Interpret coefficients as conditional effects, not raw averages; judge variables by forecast gain |
| 32 | AIC prefers richer SARIMA models ((1,0,1) −90 vs (1,0,0)) but validation MAE does not improve | 5,113 training days: small in-sample likelihood gains become 'significant' for AIC without changing one-step forecasts | Choose on validation error (the forecasting task), keep the simplest model; report both |
| 31 | Holt-Winters makes a second error the day after each holiday (+16 to +18 GWh) | α = 0.79: the holiday drags the level down, so the next normal day is under-predicted | A model without calendar knowledge pays twice per holiday → strong argument for exogenous holiday variables in SARIMAX |

---

## 9. Decisions taken (with justification)

1. **Daily resolution** for the main models (enough points, keeps weekly/yearly patterns).
2. **End-user consumption** column (excludes pumped storage).
3. **15-minute shift** before daily aggregation (end-of-interval labels).
4. **24-hour correction:** daily value = mean of quarter-hours × 96. Otherwise every March shows a fake ~4 % drop and every October a fake ~4 % jump, caused by the clock, not by behaviour. On normal days it gives exactly the real total.
5. **DST duplicates kept** (real consumption), **no sorting** by timestamp.
6. **2025 aligned** to end-of-interval convention (+15 min).
7. **No outliers removed:** extremes are real (holidays, cold wave).
8. Units: kWh → **GWh** (÷ 1,000,000).
9. **Temperature stations:** Zürich, Bern, Geneva, Lugano (covering German-speaking, French-speaking and Italian-speaking regions, north and south of the Alps).
10. **Only the `_d_historical` files** are used (they end 31.12.2025, like the consumption data); `_d_recent` (2026) not needed.
11. **National temperature = simple mean of the 4 stations** (justified by correlations 0.93–0.99). Possible improvement for the report: population-weighted mean.
12. **Holidays per canton:** `holiday_share` (fraction of 26 cantons) as a nuanced model input + `is_holiday` (≥ 50 %) as a simple yes/no.
13. **Temperature will enter the models as HDD** (heating degree days), not raw temperature, because of the hockey-stick relationship.
14. **Decomposition method: MSTL** with periods (7, 365) – classic STL handles only one seasonality, we have two.
15. **Holidays are treated like Sundays** in the models (weekday holiday 130.6 GWh ≈ Sunday 130.3 GWh).
16. **Weekly profile computed without holidays** (a holiday Monday would bias the Monday average).
17. **No dual-axis charts** in the presentation: two stacked plots with shared x-axis instead.
18. **Model ingredients justified by the data:** (1) weekly + yearly seasonality, (2) holidays, (3) temperature (HDD), (4) trend / level shift.
19. **No log / Box-Cox transformation:** 365-day rolling std stable (21–24 GWh) → model in GWh directly.
20. **Differencing: D = 1 (s = 7), d = 0** – weekly difference passes ADF and KPSS; d = 1 adds artificial negative autocorrelation.
21. **Starting model: SARIMA(1,0,0)(0,1,1)₇**; compare by AIC with (2,0,0)(0,1,1)₇, (1,0,1)(0,1,1)₇, (1,1,1)(0,1,1)₇.
22. **Yearly cycle via Fourier terms**, not a seasonal period of 364 in SARIMA (too many lags, each seasonal difference costs a year of data). **Yearly lag feature = t−364** (same weekday).
23. **Split:** train 2009–2022, validation 2023, test 2024–2025 (731 days), identical for all models.
24. **Refit on 2009–2023** before forecasting the test period.
25. **Level shift handling:** SARIMA / Holt-Winters adapt automatically; regression / LSTM get lag features (t−7, t−364) carrying the current level; 2023 validation used to detect over-prediction.
31. **All model scores in one file:** `results/scores.csv` (model, period, MAE, RMSE, MAPE), appended by every modelling notebook → final comparison table.
32. **Journal has one editor (Danyjoe)** to avoid merge conflicts.
27. **Forecasting task = day-ahead** (tomorrow from data up to today), the same for all models; real-world task, fair comparison, lets temperature help. Limitation: observed (not forecast) temperature is used.
28. **No leakage:** a feature is allowed only if known before the forecast day; rolling means of consumption end yesterday; feature choices (e.g. HDD base) made on train only.
29. **HDD base temperature = 16.5 °C** (best R² on train; curve flat between 16 and 17 °C).
30. **Feature dataset:** `dataset_features.csv` = dataset_daily + hdd, christmas_period, bridge_day, lag_1, lag_7, lag_364, roll7_mean (shifted, ends yesterday), hdd_lag1, sin/cos_1–4. NaN rows kept at the start; each model drops what it needs.
34. **SARIMA order = (1,0,0)(0,1,1)₇** (best validation MAE 3.51; matches lesson 18; simplest). Exogenous variables enter on weekdays only (a holiday on a Sunday changes nothing).
33. **Holt-Winters variant = no trend** (additive, s = 7): trend and damped trend give identical scores with β ≈ 0 → simplest model kept (parsimony).
35. **LSTM design (22 Nov):** PyTorch (CPU); day-ahead; **target = weekly difference y(t) − y(t−7)** (same idea as D = 1 → immune to the 2022–23 level shift), forecast = y(t−7) + prediction; two inputs: (a) window of the past 28 days [weekly diff, hdd, holiday_wd, christmas_wd, bridge_day] → LSTM, (b) known features of day t [hdd, calendar, weekday one-hot, Fourier] → dense; scaling fitted on train only; same split, metrics and `results/scores.csv`.
36. **Test predictions saved to files** (`results/pred_06_holtwinters.csv`, `pred_07_sarimax.csv`, `pred_08_lstm.csv`) so the comparison notebook needs no retraining.
26. **Collaboration:** GitHub repo, one branch per person, pull requests into `main`, one notebook per person at a time. Repo private until grading, then public (MIT license, data sources credited).

---

## 10. Results so far

### Data completeness
- 17 files, 596,064 quarter-hours, **0 missing values**.
- Timestamps: 596,029 gaps of 15 min, 17 of +1h15 (March), 17 of −45 min (October).
- **6,209 days** (17 × 365 + 4 leap days), **0 missing days**: 6,175 days with 96 values, 17 with 92, 17 with 100.

### Daily consumption statistics (GWh/day)
| count | mean | std | min | 25 % | median | 75 % | max |
|---|---|---|---|---|---|---|---|
| 6,209 | 153.7 | 23.1 | 98.5 | 138.4 | 152.2 | 169.5 | 222.5 |

- Sanity check: 154 GWh × 365 ≈ **56 TWh/year**, plausible order of magnitude for Switzerland.

### Observations
- **Strong yearly seasonality:** winter ~200 GWh, summer ~110 GWh (heating, lighting).
- **Weekly cycle (period 7):** Mon–Fri high (~190–200 in January, Monday slightly lower), Saturday intermediate (~170), Sunday lowest (~160).
- **Highest days:** 6–10 February 2012 (Mon–Fri), max 222.5 GWh → cold wave + working days → strong temperature effect.
- **Lowest days:** Sundays in late July / early August, all in 2023–2025 (98.5–101.9 GWh) → weekend + summer holidays. All recent → fits a slight downward trend (hypothesis: efficiency gains, energy-saving campaigns, rooftop solar self-consumption not seen by the grid).
- **Winter peaks slightly lower in recent years** (to be checked in exploration).
- **COVID 2020:** from ~day 76–80 (lockdown 16 March 2020) consumption stays ~10–20 GWh/day (~10 %) below 2019 through May. Caveats: February 2020 already lower (milder winter?) → temperature must be accounted for; weekdays and Easter dates differ between years.

### Temperature (national mean of 4 stations)
- Clear yearly cycle, from about −10 °C (coldest days) to about 28 °C (hottest days).
- **Coldest point: early February 2012 (~−10 °C)** – the same week as the consumption record (222.5 GWh on 7 Feb 2012) → first visual link between the two datasets.
- Other cold spells visible around early 2017 and 2018; hottest summers appear to be 2015 (highest peak) and the recent ones (2019, 2022–2023) – to confirm in exploration.

### Consumption vs temperature (key figure: `figures/consumption_vs_temperature.png`)
- **Correlation: −0.745** (strong, negative).
- **Hockey-stick (L) shape, not a straight line:**
  - from about −5 °C to 16–18 °C: consumption falls steadily as temperature rises (weekdays: ~200 GWh at 0 °C → ~145 GWh at 17 °C, i.e. roughly **−3 GWh per extra °C**) → **heating effect**;
  - above ~18 °C: the curve flattens (no more heating);
  - above ~22–25 °C: slight rise on weekdays → small **cooling** (air conditioning) effect.
- **Two parallel bands:** weekdays vs weekends; at the same temperature a weekend day uses ~30–40 GWh less.
- Some weekday points sit in the weekend band → probably weekday **holidays** (Christmas, Easter Monday…).
- Isolated points top-left (−8 to −10 °C, 215–222 GWh) = February 2012 cold wave.
- Conclusion: temperature must enter the models as **HDD = max(0, T_base − T)** with T_base ≈ 16–18 °C, plus weekday and holiday variables.

### Exploration results (notebook 03)

#### Yearly consumption and temperature
| Year | TWh | °C | | Year | TWh | °C |
|---|---|---|---|---|---|---|
| 2009 | 56.27 | 10.97 | | 2018 | 56.29 | 11.99 |
| 2010 | **58.52** | **9.94** | | 2019 | 55.98 | 11.58 |
| 2011 | 57.55 | 11.42 | | 2020 | 54.66 | 11.76 |
| 2012 | 57.68 | 10.81 | | 2021 | 56.79 | 10.72 |
| 2013 | 58.03 | 10.25 | | 2022 | 55.45 | **12.43** |
| 2014 | 56.41 | 11.48 | | 2023 | 53.48 | 12.38 |
| 2015 | 56.85 | 11.52 | | 2024 | **53.37** | 11.91 |
| 2016 | 56.86 | 10.93 | | 2025 | 53.50 | 11.74 |
| 2017 | 56.88 | 11.16 | | | | |

- **Cold years consume more:** 2010 (coldest, 9.94 °C) = highest consumption (58.5 TWh); 2013 cold → 58.0; 2021 cold → rebound to 56.8; 2014 warm → 56.4.
- **But 2023–2025 stay low (~53.4 TWh) without being warmer than 2022** → structural decline on top of the temperature effect.
- **Trend** (365-day rolling mean and MSTL trend): ~160 GWh/day around 2010 → slow decline → 2020 dip (~149) → 2021–22 rebound (~156) → steep drop 2022–23 to ~145–146, then flat. Total change ~−8 %, small compared with the seasonal swing (~110 → 200 GWh/day).

#### Weekly profile (holidays excluded, % vs average Mon–Fri)
| Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|
| −1.1 | +0.5 | +0.7 | +0.6 | −0.8 | **−13.4** | **−19.6** |

- Tue–Thu highest; Monday and Friday slightly lower (slower start / earlier end of the week).

#### Monthly profile (boxplot)
- Highest: January–February (median ~180–185 GWh), lowest: July–August (~135 GWh).
- Winter months vary most (February whiskers 133 → 222 GWh): consumption depends on how cold the winter is; summer variation mostly weekday vs weekend.
- Low points in January and March/April: probably New Year and Easter.

#### Holiday effect (means, GWh/day)
| Normal weekday | Weekday holiday | Saturday | Sunday |
|---|---|---|---|
| 162.0 | **130.6** | 140.3 | **130.3** |

- A weekday holiday behaves like a Sunday. Holidays fall mostly in high-consumption seasons (winter/spring), so the true holiday effect is probably even stronger.

#### MSTL decomposition (`figures/mstl_decomposition.png`)
| Component | Share of variation |
|---|---|
| Yearly (`seasonal_365`) | **61.7 %** |
| Weekly (`seasonal_7`) | **27.8 %** |
| Residual | 6.7 % |
| Trend | 3.4 % |

- Weekly amplitude ≈ +10 / −28 GWh; yearly amplitude ≈ ±35–40 GWh.

#### Top-10 residuals (what the calendar cannot explain)
| Date | Residual (GWh) | Day | What it is |
|---|---|---|---|
| 2020-04-13 | −31.5 | Mon | Easter Monday |
| 2011-04-25 | −30.8 | Mon | Easter Monday |
| 2009-04-13 | −30.5 | Mon | Easter Monday |
| 2015-05-14 | −30.3 | Thu | Ascension |
| 2019-04-22 | −28.5 | Mon | Easter Monday |
| 2022-04-15 | −28.5 | Fri | Good Friday |
| 2017-04-14 | −27.8 | Fri | Good Friday |
| 2013-05-09 | −27.8 | Thu | Ascension |
| 2021-04-02 | −27.7 | Fri | Good Friday |
| 2022-04-02 | **+27.5** | Sat | Cold day (1.95 °C, unusual for April) |

- 9/10 = **moving holidays**; the 10th = an unusual cold day.

#### Residual vs temperature (`figures/residual_vs_temp_anomaly.png`)
| Measure | Correlation |
|---|---|
| Residual vs raw temperature, all days | −0.19 |
| Residual vs **temperature anomaly**, holidays excluded | **−0.559** |

- Colder than normal → positive residual (more consumption than the calendar predicts); warmer than normal → negative residual.
- Slope ≈ −1.5 GWh per °C of anomaly (average of winter, where it matters, and summer, where it barely does → HDD again).
- **Key sentence for the presentation:** *"The calendar explains about 90 % of the variation. Of what remains, the largest errors come from moving holidays (Easter, Ascension), and the rest correlates strongly with temperature anomalies (r = −0.56). This justifies adding holidays and temperature to the models."*

### Stationarity results (notebook 04)

#### Rolling statistics (`figures/rolling_mean_std.png`)
- **30-day mean:** yearly wave, ~125–135 GWh (summer) → 180–195 (winter) → mean not constant.
- **365-day mean:** trend as in exploration (~155–160 → 2020 dip ~149 → rebound → ~145 from 2023).
- **30-day std:** usually 12–16 GWh (weekday/weekend gap); spikes to 20–24 once a year at **Christmas / New Year**; slightly lower lows after 2020 (~10–11).
- **365-day std:** stable, 21–24 GWh → no variance-stabilising transformation needed.

#### ACF / PACF of the raw series (`figures/acf_pacf_raw.png`)
- ACF short lags: lag 1 ≈ 0.80; peaks at 7 (0.90), 14 (0.83), 21 (0.79) … 56 (0.60); troughs at weekend lags; never close to 0 by lag 60 → **non-stationary**.
- PACF: lag 1 ≈ 0.80, lags 6 (0.59), 7 (0.53), 8 (−0.63); negative spikes at 15, 22, 29, 36, 43, 50 (7k+1) → seasonal structure s = 7.
- ACF long lags: crosses 0 at ~105, minimum ≈ −0.55 at lag 180–190 (opposite seasons), back to 0 at ~265, maximum ≈ 0.8 at **lag 364** (= 52 weeks, same weekday). Weekly comb visible throughout.

#### Stationarity tests
| Series | ADF stat | ADF p | KPSS stat | KPSS p | ADF says | KPSS says | std (GWh) |
|---|---|---|---|---|---|---|---|
| raw | −4.71 | 0.0001 | 0.65 | 0.018 | stationary | **non-stationary** | 23.1 |
| weekly diff (D=1, s=7) | −15.43 | 0.000 | 0.01 | ≥ 0.10 | stationary | stationary | 10.4 |
| weekly + first diff (D=1, d=1) | −27.06 | 0.000 | 0.01 | ≥ 0.10 | stationary | stationary | 7.6 |

- Raw: ADF and KPSS disagree → mean-reverting around a seasonal level that is not constant → difference.
- ADF chose 33–34 lags (AIC) → strong weekly structure.
- KPSS p is capped at 0.01 / 0.10 (0.100 means ≥ 0.10).
- Weekly differencing leaves **paired spikes** (±40–55 GWh) one week apart around holidays (holiday vs normal day, then normal day vs holiday) and clusters at Christmas / New Year → holidays must enter as an exogenous variable.

#### ACF / PACF after differencing (`figures/acf_pacf_differenced.png`)
- **Weekly difference:** ACF 0.73, 0.54, 0.42, 0.23, 0.14, ≈0 by lag 6 (≈ 0.73^k) + PACF single spike at lag 1 (0.74) → **AR(1)**. Lag 7 ACF ≈ −0.17, small at 14/21/28 → **seasonal MA(1)**. PACF positive spikes at 8, 15, 22, 29 (7k+1) = interaction AR(1) × seasonal MA. Small leftover: negative ACF lags 8–20, positive ~35–42 (slow yearly / holiday effects).
- **Weekly + first difference:** ACF ≈ −0.14 at lags 1–2, −0.45 at lag 7; PACF negative at 7, 14, 21… fading slowly → structure created by the extra difference → d = 1 rejected.
- **Candidate: SARIMA(1,0,0)(0,1,1)₇.**

#### Split (`figures/train_val_test_split.png`)
| Period | Days | Mean GWh/day | Mean temp (°C) |
|---|---|---|---|
| train 2009–2022 | 5,113 | 155.3 | 11.2 |
| (2019–2022 only) | | 152.6 | |
| validation 2023 | 365 | 146.5 | 12.4 |
| test 2024–2025 | 731 | 146.2 | 11.8 |

- Gap train → test ≈ 9 GWh/day (−6 %); vs 2019–22 ≈ 6.4 GWh (−4 %).
- Test only 0.6 °C warmer than train → ~1 GWh explained by temperature (−1.5 GWh/°C) → **~8 GWh/day structural**.
- Validation ≈ test level → 2023 is representative of the test period.

---

## 11. Lessons learned (method)

- Inspect the raw data before cleaning (sheets, columns, units row, first and last rows).
- **Diagnose before fixing:** find which files are affected and why.
- **Never drop duplicates blindly:** check what they are.
- Give date formats **explicitly** to avoid day/month confusion.
- A check only counts if it **could have failed** when the hypothesis is wrong.
- Real-world data changes format over time without warning (text dates from 2021, start labels in 2025).
- A notebook must run **top to bottom without errors**; cells that modify data are not safe to re-run.
- Always sanity-check orders of magnitude (units).
- Explain extremes before deciding they are outliers.
- Save intermediate results to CSV so slow steps (17 Excel files) never need to be repeated.
- Understand **one** file completely before writing a loop over many.
- Use **functions** for repeated steps: write once, fix bugs in one place.
- A smaller file is not automatically a problem: check whether it affects **your** period.
- Before averaging several sources, check they **move together** (correlation).
- Know the domain: Swiss holidays are cantonal, so a national list is incomplete.
- A CSV stores only text: restore types on reading (`index_col`, `parse_dates`).
- After every join, check for NaN (rows that did not match).
- A strong correlation does not mean a straight line: always **plot** the relationship.
- Never use two y-axes on one chart; stack two plots with a shared x-axis.
- A rolling mean over a full period (365 days) removes the seasonality and reveals the trend; `center=True` avoids a time lag.
- Exclude special days (holidays) when computing "normal" profiles.
- Think about **confounders**: a weak correlation can hide a strong relationship (−0.19 → −0.56 after removing holidays and the normal seasonal temperature).
- The residual of a decomposition is the most informative part: it shows what extra variables a model needs.
- Each modelling choice should be **justified by a finding in the data**.
- Use **two** stationarity tests with opposite null hypotheses (ADF, KPSS); their disagreement is informative.
- Difference as **little** as possible; check ACF/PACF after each step – extra differencing creates artificial negative correlations.
- A lower std after differencing does not prove the difference was needed: Var(Δx) = 2σ²(1−ρ₁) falls whenever ρ₁ > 0.5.
- Read ACF/PACF on the **stationary** series, not the raw one; put x-ticks on seasonal lags (every 7).
- For a yearly lag on daily data with a weekly cycle, use **364** (same weekday).
- Quantify a structural break (level gap, part explained by temperature) before deciding how to handle it.
- Git: save files before `git add`; check `git status` before every commit; never commit raw data, environments or checkpoints.

---

## 12. Output files

| File | Content |
|---|---|
| `data/processed/swissgrid_15min_raw.csv` | 596,064 rows: timestamp (fixed, end-of-interval), consumption_kwh, source_file |
| `data/processed/swissgrid_daily.csv` | 6,209 rows: date, consumption_gwh (24-h corrected), n_values |
| `notebooks/01_cleaning.ipynb` | Full cleaning notebook |
| `data/processed/temperature_daily.csv` | 6,209 rows: date, SMA, BER, GVE, LUG, temp_ch (°C) |
| `data/processed/dataset_daily.csv` | **Final dataset**, 6,209 × 6: consumption_gwh, temp_ch, holiday_share, is_holiday, weekday, month |
| `figures/consumption_vs_temperature.png` | Scatter consumption vs temperature (weekdays vs weekends) |
| `notebooks/02_temperature.ipynb` | Temperature, holidays and final dataset notebook |
| `notebooks/03_exploration.ipynb` | Exploration notebook (section 2) |
| `figures/yearly_consumption_temperature.png` | Yearly TWh and yearly °C (two stacked plots) |
| `figures/trend_rolling365.png` | Daily consumption + 365-day rolling mean |
| `figures/weekday_profile.png` | Average consumption per weekday (holidays excluded) |
| `figures/monthly_boxplot.png` | Daily consumption by month |
| `figures/mstl_decomposition.png` | MSTL: observed, trend, weekly, yearly, residual |
| `figures/residual_vs_temp_anomaly.png` | MSTL residual vs temperature anomaly (holidays excluded) |
| `notebooks/04_stationarity.ipynb` | Stationarity notebook (section 3) |
| `figures/rolling_mean_std.png` | 30- and 365-day rolling mean and std |
| `figures/acf_pacf_raw.png` | ACF (lags 60, 400) and PACF (lags 60) of the raw series |
| `figures/differencing.png` | Raw, weekly difference, weekly + first difference |
| `figures/acf_pacf_differenced.png` | ACF/PACF of the two differenced series (lags 42) |
| `figures/train_val_test_split.png` | Split with 365-day mean |
| `notebooks/05_features.ipynb` | Feature engineering notebook |
| `figures/hdd_base_choice.png` | R² vs HDD base temperature (best 16.5 °C) |
| `figures/fourier_yearly_fit.png` | Yearly cycle from 4 Fourier pairs (fit on train) |
| `data/processed/dataset_features.csv` | **Feature dataset**, 6,209 × 22 (see decision 30) |
| `notebooks/06_baselines_holtwinters.ipynb` | Baselines + Holt-Winters (section 4) |
| `notebooks/07_sarima.ipynb` | SARIMA / SARIMAX (section 5) |
| `figures/sarimax_hdd_winter_zoom.png` | Test winter 2024–25, with vs without temperature |
| `notebooks/08_lstm.ipynb` | LSTM (section 6) |
| `figures/lstm_training_curves.png` | LSTM train / validation loss |
| `results/scores.csv` | All model scores (model, period, MAE, RMSE, MAPE) – appended by every modelling notebook |
| `figures/baselines_val_zoom.png`, `figures/holtwinters_val_zoom.png`, `figures/holtwinters_residuals.png` | Section 4 figures |
| `.gitignore`, `requirements.txt`, `LICENSE`, `GETTING_STARTED.md` | Repository files |

---

## 13. Consolidated cleaning code (clean version of notebook 01)

```python
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- load the 17 Swissgrid files ---
files = sorted(Path("../data/raw/swissgrid").glob("EnergieUebersichtCH-*.xls*"))
parts = []
for f in files:
    part = pd.read_excel(f, sheet_name="Zeitreihen0h15", usecols=[0, 1],
                         skiprows=[1], engine="calamine")
    part.columns = ["timestamp", "consumption_kwh"]
    part["source_file"] = f.name
    parts.append(part)
raw = pd.concat(parts, ignore_index=True)          # do NOT sort (DST duplicates)

# --- fix text timestamps (2021–2025) ---
is_text = raw["timestamp"].map(lambda x: isinstance(x, str))
raw.loc[is_text, "timestamp"] = pd.to_datetime(
    raw.loc[is_text, "timestamp"], format="%d.%m.%Y %H:%M")
raw["timestamp"] = pd.to_datetime(raw["timestamp"])

# --- align 2025 (start-of-interval) to end-of-interval ---
is_2025 = raw["source_file"] == "EnergieUebersichtCH-2025.xlsx"
raw.loc[is_2025, "timestamp"] += pd.Timedelta(minutes=15)

# --- check: expect 17 × +1h15 and 17 × −45 min ---
print(raw["timestamp"].diff().value_counts())
raw.to_csv("../data/processed/swissgrid_15min_raw.csv", index=False)

# --- daily aggregation with 24-hour correction ---
df15 = raw.copy()
df15["date"] = (df15["timestamp"] - pd.Timedelta(minutes=15)).dt.normalize()
daily = df15.groupby("date").agg(
    n_values=("consumption_kwh", "size"),
    mean_kwh=("consumption_kwh", "mean"),
)
daily["consumption_gwh"] = daily["mean_kwh"] * 96 / 1e6

# --- checks ---
full_range = pd.date_range("2009-01-01", "2025-12-31", freq="D")
print(len(daily), daily["n_values"].value_counts(), len(full_range.difference(daily.index)))

daily[["consumption_gwh", "n_values"]].to_csv("../data/processed/swissgrid_daily.csv")
```

### Consolidated code – notebook 02 (temperature, holidays, final dataset)

```python
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import holidays

METEO = Path("../data/raw/meteo")
full_range = pd.date_range("2009-01-01", "2025-12-31", freq="D")

# --- temperature: 4 stations side by side ---
def load_station(code):
    """Return the daily mean temperature (2009-2025) of one station as a Series."""
    df = pd.read_csv(METEO / f"ogd-smn_{code}_d_historical.csv", sep=";",
                     usecols=["reference_timestamp", "tre200d0"])
    df["date"] = pd.to_datetime(df["reference_timestamp"], format="%d.%m.%Y %H:%M")
    df = df[df["date"].between("2009-01-01", "2025-12-31")]
    return df.set_index("date")["tre200d0"].rename(code.upper())

temps = pd.concat([load_station(c) for c in ["sma", "ber", "gve", "lug"]], axis=1)
print(len(full_range.difference(temps.index)), temps.isna().sum())   # expect 0 / 0
print(temps.corr().round(3))
temps["temp_ch"] = temps[["SMA", "BER", "GVE", "LUG"]].mean(axis=1)
temps.to_csv("../data/processed/temperature_daily.csv", index_label="date")

# --- holidays: count cantons ---
cantons = [c for c in holidays.Switzerland.subdivisions if len(c) == 2]   # 26 cantons
holiday_count = pd.Series(0, index=full_range)
for c in cantons:
    days = holidays.Switzerland(years=range(2009, 2026), subdiv=c)
    holiday_count += full_range.isin(pd.to_datetime(list(days.keys())))
holidays_df = pd.DataFrame({"holiday_share": holiday_count / len(cantons)})
holidays_df["is_holiday"] = holidays_df["holiday_share"] >= 0.5

# --- final dataset ---
cons = pd.read_csv("../data/processed/swissgrid_daily.csv", index_col="date", parse_dates=True)
dataset = cons[["consumption_gwh"]].join(temps["temp_ch"]).join(holidays_df)
dataset["weekday"] = dataset.index.day_of_week   # 0 = Monday
dataset["month"] = dataset.index.month
print(dataset.shape, dataset.isna().sum().sum())   # expect (6209, 6) and 0

# --- key figure ---
work = dataset["weekday"] < 5
fig, ax = plt.subplots(figsize=(9, 5))
ax.scatter(dataset.loc[work, "temp_ch"], dataset.loc[work, "consumption_gwh"], s=3, alpha=0.4, label="Mon–Fri")
ax.scatter(dataset.loc[~work, "temp_ch"], dataset.loc[~work, "consumption_gwh"], s=3, alpha=0.4, label="Sat–Sun")
ax.set_xlabel("Mean temperature, 4 stations (°C)"); ax.set_ylabel("Consumption (GWh/day)")
ax.set_title("Daily electricity consumption vs temperature (2009–2025)"); ax.legend()
fig.savefig("../figures/consumption_vs_temperature.png", dpi=150, bbox_inches="tight")
print("correlation:", dataset["consumption_gwh"].corr(dataset["temp_ch"]).round(3))   # -0.745

dataset.to_csv("../data/processed/dataset_daily.csv", index_label="date")
```

### Consolidated code – notebook 03 (exploration)

```python
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import MSTL

df = pd.read_csv("../data/processed/dataset_daily.csv", index_col="date", parse_dates=True)
FIG = "../figures/"

# --- yearly totals (two stacked plots, no dual axis) ---
yearly = df.groupby(df.index.year).agg(consumption_twh=("consumption_gwh", "sum"),
                                       temp_mean=("temp_ch", "mean"))
yearly["consumption_twh"] /= 1000
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
ax1.plot(yearly.index, yearly["consumption_twh"], marker="o"); ax1.set_ylabel("TWh / year")
ax1.set_title("Yearly electricity consumption, Switzerland")
ax2.plot(yearly.index, yearly["temp_mean"], marker="o", color="tab:red"); ax2.set_ylabel("°C")
ax2.set_title("Yearly mean temperature (4 stations)")
ax2.set_xticks(yearly.index); ax2.tick_params(axis="x", rotation=45)
fig.tight_layout(); fig.savefig(FIG + "yearly_consumption_temperature.png", dpi=150, bbox_inches="tight")

# --- trend: 365-day centred rolling mean ---
trend = df["consumption_gwh"].rolling(365, center=True).mean()
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(df.index, df["consumption_gwh"], lw=0.5, color="lightgray"); ax.plot(trend.index, trend, lw=2)
ax.set_ylabel("GWh / day"); ax.set_title("Daily consumption (gray) and 365-day rolling mean (trend)")
fig.savefig(FIG + "trend_rolling365.png", dpi=150, bbox_inches="tight")

# --- weekly profile (holidays excluded) ---
normal = ~df["is_holiday"]
week = df[normal].groupby("weekday")["consumption_gwh"].mean()
week.index = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
print(((week / week.iloc[:5].mean() - 1) * 100).round(1))
ax = week.plot(kind="bar", figsize=(7, 3.5), rot=0); ax.set_ylabel("GWh / day")
ax.set_title("Average consumption by weekday (holidays excluded)")
plt.savefig(FIG + "weekday_profile.png", dpi=150, bbox_inches="tight")

# --- monthly boxplot ---
fig, ax = plt.subplots(figsize=(11, 4))
df.boxplot(column="consumption_gwh", by="month", ax=ax, grid=False)
ax.set_title("Daily consumption by month (2009–2025)"); ax.set_xlabel("month"); ax.set_ylabel("GWh / day")
fig.suptitle(""); fig.savefig(FIG + "monthly_boxplot.png", dpi=150, bbox_inches="tight")

# --- holiday effect ---
wk = df["weekday"] < 5
for label, m in [("normal weekday", wk & normal), ("weekday holiday", wk & ~normal),
                 ("Saturday", (df["weekday"] == 5) & normal), ("Sunday", (df["weekday"] == 6) & normal)]:
    print(label, df.loc[m, "consumption_gwh"].mean().round(1))

# --- MSTL decomposition ---
y = df["consumption_gwh"]
res = MSTL(y, periods=(7, 365)).fit()
fig = res.plot(); fig.set_size_inches(14, 10); fig.tight_layout()
fig.savefig(FIG + "mstl_decomposition.png", dpi=150, bbox_inches="tight")
comp = pd.DataFrame({"trend": res.trend, "weekly": res.seasonal["seasonal_7"],
                     "yearly": res.seasonal["seasonal_365"], "residual": res.resid})
print((comp.var() / y.var() * 100).round(1))
top = comp["residual"].abs().nlargest(10).index
print(pd.DataFrame({"residual": comp.loc[top, "residual"].round(1), "weekday": top.day_name(),
                    "temp_ch": df.loc[top, "temp_ch"], "is_holiday": df.loc[top, "is_holiday"]}))

# --- residual vs temperature anomaly (holidays excluded) ---
temp_normal = df.groupby(df.index.day_of_year)["temp_ch"].transform("mean")
df["temp_anomaly"] = df["temp_ch"] - temp_normal
mask = ~df["is_holiday"]
print(comp["residual"].corr(df["temp_ch"]).round(3))                                 # -0.19
print(comp.loc[mask, "residual"].corr(df.loc[mask, "temp_anomaly"]).round(3))       # -0.559
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(df.loc[mask, "temp_anomaly"], comp.loc[mask, "residual"], s=3, alpha=0.3)
ax.axhline(0, color="gray", lw=0.8); ax.axvline(0, color="gray", lw=0.8)
ax.set_xlabel("Temperature anomaly (°C vs normal for that day)"); ax.set_ylabel("MSTL residual (GWh)")
ax.set_title("What the calendar can't explain vs unusual weather")
fig.savefig(FIG + "residual_vs_temp_anomaly.png", dpi=150, bbox_inches="tight")
```

### Consolidated code – notebook 04 (stationarity)

```python
import warnings
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller, kpss

FIG = "../figures/"
df = pd.read_csv("../data/processed/dataset_daily.csv", index_col="date", parse_dates=True)
df = df.asfreq("D")
y = df["consumption_gwh"]
print(y.index.freq, len(y), y.isna().sum())          # <Day> 6209 0

# --- rolling mean / std ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
ax1.plot(y.index, y, lw=0.4, color="lightgray", label="daily")
for w, c in [(30, "tab:blue"), (365, "tab:red")]:
    ax1.plot(y.rolling(w, center=True).mean(), lw=1.5, color=c, label=f"{w}-day mean")
    ax2.plot(y.rolling(w, center=True).std(), lw=1.5, color=c, label=f"{w}-day std")
ax1.set_ylabel("GWh / day"); ax1.set_title("Rolling mean"); ax1.legend(loc="upper right")
ax2.set_ylabel("GWh / day"); ax2.set_title("Rolling standard deviation"); ax2.legend(loc="upper right")
fig.tight_layout(); fig.savefig(FIG + "rolling_mean_std.png", dpi=150, bbox_inches="tight")

# --- ACF / PACF raw ---
fig, axes = plt.subplots(3, 1, figsize=(14, 11))
plot_acf(y, lags=60, ax=axes[0]); axes[0].set_title("ACF – raw series, lags 0–60 (weekly pattern)")
plot_pacf(y, lags=60, ax=axes[1], method="ywm"); axes[1].set_title("PACF – raw series, lags 0–60")
plot_acf(y, lags=400, ax=axes[2], marker=None); axes[2].set_title("ACF – raw series, lags 0–400 (yearly pattern)")
for ax in axes: ax.set_xlabel("lag (days)")
fig.tight_layout(); fig.savefig(FIG + "acf_pacf_raw.png", dpi=150, bbox_inches="tight")

# --- ADF + KPSS ---
def stationarity_tests(series, name):
    """Run ADF and KPSS on a series and return the results as one row."""
    s = series.dropna()
    adf_stat, adf_p, adf_lags, *_ = adfuller(s, autolag="AIC", result_object=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")          # KPSS p capped at 0.01 / 0.10
        kpss_stat, kpss_p, *_ = kpss(s, regression="c", nlags="auto")
    return pd.Series({
        "ADF stat": round(adf_stat, 2), "ADF p": round(adf_p, 4), "ADF lags": adf_lags,
        "KPSS stat": round(kpss_stat, 2), "KPSS p": round(kpss_p, 4),
        "ADF says": "stationary" if adf_p < 0.05 else "non-stationary",
        "KPSS says": "non-stationary" if kpss_p < 0.05 else "stationary",
    }, name=name)

# --- differencing ---
y_d7 = y.diff(7)              # weekly difference
y_d7_d1 = y_d7.diff(1)        # + first difference
results = pd.DataFrame([stationarity_tests(y, "raw"),
                        stationarity_tests(y_d7, "weekly diff (D=1, s=7)"),
                        stationarity_tests(y_d7_d1, "weekly + first diff (D=1, d=1)")])
results["std (GWh)"] = [y.std(), y_d7.std(), y_d7_d1.std()]
print(results.round(3))

fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
for ax, s, title in zip(axes, [y, y_d7, y_d7_d1],
                        ["Raw series", "Weekly difference  y(t) − y(t−7)", "Weekly + first difference"]):
    ax.plot(s.index, s, lw=0.4); ax.axhline(0, color="gray", lw=0.8)
    ax.set_title(title); ax.set_ylabel("GWh")
fig.tight_layout(); fig.savefig(FIG + "differencing.png", dpi=150, bbox_inches="tight")

# --- ACF / PACF differenced ---
fig, axes = plt.subplots(2, 2, figsize=(15, 8))
plot_acf(y_d7.dropna(), lags=42, ax=axes[0, 0]); axes[0, 0].set_title("ACF – weekly difference")
plot_pacf(y_d7.dropna(), lags=42, ax=axes[1, 0], method="ywm"); axes[1, 0].set_title("PACF – weekly difference")
plot_acf(y_d7_d1.dropna(), lags=42, ax=axes[0, 1]); axes[0, 1].set_title("ACF – weekly + first difference")
plot_pacf(y_d7_d1.dropna(), lags=42, ax=axes[1, 1], method="ywm"); axes[1, 1].set_title("PACF – weekly + first difference")
for ax in axes.flat:
    ax.set_xticks(range(0, 43, 7)); ax.set_xlabel("lag (days)")
fig.tight_layout(); fig.savefig(FIG + "acf_pacf_differenced.png", dpi=150, bbox_inches="tight")

# --- train / validation / test split ---
split = {"train": ("2009-01-01", "2022-12-31"),
         "validation": ("2023-01-01", "2023-12-31"),
         "test": ("2024-01-01", "2025-12-31")}
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(y.index, y, lw=0.4, color="lightgray")
ax.plot(y.rolling(365, center=True).mean(), lw=2, color="black", label="365-day mean")
ax.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"), color="tab:orange", alpha=0.2, label="validation")
ax.axvspan(pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31"), color="tab:red", alpha=0.2, label="test")
ax.set_ylabel("GWh / day"); ax.legend(loc="upper right")
ax.set_title("Train (2009–2022) / validation (2023) / test (2024–2025)")
fig.savefig(FIG + "train_val_test_split.png", dpi=150, bbox_inches="tight")
summary = pd.DataFrame({name: {"days": len(y[a:b]), "mean GWh": y[a:b].mean(),
                               "mean temp (°C)": df["temp_ch"][a:b].mean()}
                        for name, (a, b) in split.items()}).T.round(1)
print("mean 2019–2022:", y["2019":"2022"].mean().round(1))
print(summary)
```

---

## 14. Next steps

Data preparation, exploration and stationarity (sections 1–3) are **complete**. Next:

### Feature engineering – `notebooks/05_features.ipynb` ✅ (Danyjoe, 21 Nov – done; items below all built)
- HDD = max(0, T_base − T): choose T_base (~16–18 °C) from the consumption-vs-temperature scatter (try 16, 17, 18; pick the best fit on train).
- Possibly CDD = max(0, T − T_cool) for the small summer cooling effect (> ~22 °C).
- Christmas-period variable (24 Dec – 2 Jan), bridge days (Friday after Ascension, Monday/Friday next to holidays).
- Lags **t−1, t−7, t−364** and rolling means (for regression / LSTM).
- Fourier terms for the yearly cycle (sin/cos of 2πk·t/365.25, k = 1…K).
- Save `data/processed/dataset_features.csv`.

### Baselines + smoothing – `notebooks/06_baselines_holtwinters.ipynb` (Danyjoe, presentation section 4 – taken over from Youssef on 21 Nov)
1. Helper: split function + metrics function (MAE, RMSE, MAPE) reused by every model.
2. Baselines on validation 2023: naive (y(t−1)), seasonal naive (y(t−7)), yearly naive (y(t−364)).
3. Holt-Winters / ETS with weekly seasonality (s = 7), additive; compare variants (damped trend or not).
4. Same evaluation on test after refitting on 2009–2023.
5. Residual check (ACF of residuals, Ljung-Box).

### Then
SARIMA(1,0,0)(0,1,1)₇ + neighbours (AIC) → + Fourier terms → SARIMAX (HDD + holidays + Christmas) → LSTM → comparison table on the same test period → report.

### Notes for the report / presentation
- Swiss control block ≠ Swiss territory (< 2 % deviation).
- Swissgrid format changes over the years (text dates from 2021, start labels in 2025) and how they were handled.
- DST handling and the 24-hour correction.
- Extremes checked and explained (February 2012 cold wave, summer Sundays).
- COVID effect visible from mid-March 2020, but confounded with temperature.
- Temperature = simple mean of 4 stations (correlations 0.93–0.99); improvement: population-weighted mean.
- Swiss holidays are cantonal → `holiday_share` over 26 cantons.
- Key figure: consumption vs temperature (hockey stick, two bands, correlation −0.745) → motivates HDD.
- Citation required for temperature data: "Source: MeteoSwiss".
- Yearly consumption mirrors yearly temperature (2010 coldest = highest), but 2023–25 low regardless → structural decline.
- Weekly profile: Sat −13 %, Sun −20 %; weekday holiday ≈ Sunday.
- MSTL: calendar ≈ 90 % of variation (yearly 61.7 %, weekly 27.8 %).
- Largest residuals = moving holidays (Easter, Ascension); fixed holidays are absorbed by the yearly cycle.
- Residual vs temperature anomaly r = −0.56 (after removing confounders; raw −0.19).
- Risk for the test period: 2022–23 level shift (−9 GWh/day, ~8 structural) and how each model family handles it.
- Suggested figures for section 2: consumption vs temperature, yearly consumption/temperature, weekday profile, monthly boxplot, MSTL decomposition, residual vs temperature anomaly.
- **Section 6 sentence:** *"The LSTM (5-seed ensemble, with calendar and temperature) reaches 3.19 GWh on 2024–25: better than Holt-Winters and plain SARIMA, but 27 % behind SARIMAX with HDD. With a few thousand days of clearly structured data, the well-specified statistical model wins."*
- **Key result sentence:** *"On 2024–2025, day-ahead, the best model (SARIMAX with calendar, Fourier and HDD) reaches MAE 2.51 GWh (1.75 %), half the error of Holt-Winters (4.05) and a third of seasonal naive (7.75). Adding temperature alone cuts the error by 21 % (3.17 → 2.51): the weather matters."* (Caveat: observed, not forecast, temperature – with ~1 °C forecast error the gain is still 14 %, with 2 °C it disappears; lesson 29.)
- **Section 3 key sentence:** *"ADF rejects a unit root (p < 0.001), but KPSS rejects stationarity (p = 0.018): the series is mean-reverting around a seasonal level that is not constant. One weekly difference makes it stationary (both tests agree); its ACF/PACF point to SARIMA(1,0,0)(0,1,1)₇, and the yearly cycle is left to Fourier terms."*
- Suggested figures for section 3: rolling mean/std, ACF/PACF raw, differencing, ACF/PACF differenced, stationarity test table, split figure.

---

## 15. Sources

- Swissgrid – Energy data CH: https://www.swissgrid.ch/en/home/customers/topics/energy-data-ch
- Swissgrid – Load: https://www.swissgrid.ch/en/home/operation/grid-data/load.html
- Swissgrid – Transmission: https://swissgrid.ch/en/home/operation/grid-data/transmission.html
- MeteoSwiss – Automatic weather stations (open data docs): https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
- MeteoSwiss STAC collection: https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn
- MeteoSwiss – Open data: https://www.meteoswiss.admin.ch/services-and-publications/service/open-data.html
- Example notebook loading Swissgrid data: https://nbviewer.org/github/tbreitbach/edh_group_04/blob/main/egdh_group_04_notebook.ipynb
- Python `holidays` library (Swiss holidays per canton): https://pypi.org/project/holidays/
- statsmodels MSTL (multiple seasonal decomposition): https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.MSTL.html
- statsmodels ADF test: https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html
- statsmodels KPSS test: https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.kpss.html
