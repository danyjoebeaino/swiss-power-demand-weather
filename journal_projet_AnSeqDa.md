# Project log – AnSeqDa (Analysis of Sequential Data)

*Record of everything decided, done and found so far. Last update: 9 November 2026 – data preparation and exploration complete; next step = section 3 (autocorrelation & stationarity).*

---

## 0. Handover – where we are and how to resume

### Status at a glance
| Presentation section | Status | Notebook |
|---|---|---|
| 1. Data presentation | ✅ material ready (sources, cleaning, problems solved) | `01_cleaning.ipynb`, `02_temperature.ipynb` |
| 2. Exploration | ✅ complete | `03_exploration.ipynb` |
| 3. Autocorrelation & stationarity | ⏭ **next – not started** | `04_stationarity.ipynb` (to create) |
| 4. Smoothing (Holt-Winters) | ⬜ | – |
| 5. ARIMA (SARIMA / SARIMAX) | ⬜ | – |
| 6. LSTM | ⬜ | – |
| 7. Comparison & conclusion | ⬜ | – |

### What you need to resume
- **One file is enough to continue:** `data/processed/dataset_daily.csv` (6,209 days × 6 columns, no missing values). Every new notebook starts from it.
- Raw data (~450 MB) is only needed to re-run notebooks 01–02; it can be re-downloaded (see section 5).
- Environment: see section 4 (venv + `pip install ... statsmodels`).
- Note: the column `temp_anomaly` is computed inside `03_exploration.ipynb` only (not saved in the CSV). Recompute it if needed (code in section 13).

### The 5 things to know before modelling
1. **Calendar explains ~90 % of the variation** (MSTL: yearly 61.7 %, weekly 27.8 %, trend 3.4 %, residual 6.7 %) → seasonal models (s = 7, plus yearly cycle) are the base.
2. **Largest unexplained errors = moving holidays** (Easter Monday, Good Friday, Ascension: ≈ −30 GWh) → holiday variable is essential; a weekday holiday ≈ a Sunday (130.6 vs 130.3 GWh).
3. **Temperature anomalies explain the rest** (r = −0.56 with the MSTL residual, holidays excluded) → temperature as HDD (non-linear, hockey stick).
4. **Structural break 2022–23:** consumption dropped from ~58 TWh (2010–13) to ~53.4 TWh (2023–25) and did not recover → ⚠️ models trained on 2009–2022 risk **over-predicting** the 2024–25 test period. Must be handled (see problem 21).
5. **Open feature-engineering items:** HDD base temperature (~16–18 °C), Christmas-period variable, bridge days.

### Immediate next step
Create `notebooks/04_stationarity.ipynb` → plan in section 14.

---

## 1. Project overview

- **Course:** TSM-AnSeqDa – Project in Analysis of Sequential Data (MSE, HES-SO)
- **Subject:** *Analyse et prévision de la consommation électrique en Suisse (2009–2025)*
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
- Split: train 2009–2022, validation 2023, test 2024 – mid-2025 (most recent months are provisional at Swissgrid: reliable only after ~6 months).
- Metrics: MAE, RMSE, MAPE.

### 1. Data collection ✅
### 2. Cleaning and preparation ✅ (Swissgrid, MeteoSwiss, holidays, final dataset)
### 3. Exploratory analysis ✅
- Yearly totals vs yearly temperature; long-term trend (365-day rolling mean).
- Weekly profile (holidays excluded); monthly boxplot; holiday effect.
- MSTL decomposition (periods 7 and 365); variance shares; largest residuals.
- Residual vs temperature anomaly.
- Consumption vs temperature (hockey stick) – done in notebook 02.

### 4. Autocorrelation and stationarity
- ACF / PACF (weekly lag 7, yearly); rolling mean / std; ADF and KPSS tests; differencing if needed.

### 5. Feature engineering
- Calendar: weekday, month, holidays, bridge days.
- Heating degree days (HDD) from temperature.
- Lags (t−1, t−7, t−365) and rolling means.

### 6. Modelling (simple → complex)
1. Baselines: naive, seasonal naive.
2. Smoothing: Holt-Winters / ETS.
3. SARIMA (s = 7 + Fourier terms), then SARIMAX with HDD and holidays.
4. LSTM with temperature and calendar inputs.
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
- `01_cleaning.ipynb` – Swissgrid cleaning and daily aggregation ✅
- `02_temperature.ipynb` – MeteoSwiss cleaning, holidays, merge into the final dataset ✅
- `03_exploration.ipynb` – exploration (section 2 of the presentation) ✅
- `04_stationarity.ipynb` – autocorrelation and stationarity (section 3) ⏭
- later notebooks – feature engineering and models (each starts from `dataset_daily.csv`)

---

## 4. Environment setup

```bash
# folder structure (created inside Projet/)
mkdir -p data/{raw/{swissgrid,meteo},processed} notebooks figures

# virtual environment + packages (Ubuntu does not allow pip into system Python)
python3 -m venv .venv
source .venv/bin/activate
pip install pandas xlrd openpyxl python-calamine matplotlib jupyter holidays statsmodels
jupyter notebook
```

```bash
# start a work session
cd "/run/media/odin/New Volume/Switzerland/HES-SO/sem1/TSM-AnSeqDa/Projet"
source .venv/bin/activate
jupyter notebook
# stop: save (Ctrl+S) -> File > Shut Down (or Ctrl+C in the terminal) -> deactivate
```

- Python 3.14, pandas 3.0.
- `xlrd` reads old `.xls`, `openpyxl` reads `.xlsx`; `python-calamine` reads both and is ~3× faster (used for the final loading loop).

```
Projet/
├── data/
│   ├── raw/swissgrid/      17 Excel files (2009–2025), 428 MB
│   ├── raw/meteo/          MeteoSwiss daily files, 22 MB
│   └── processed/          cleaned CSV files
├── figures/
├── notebooks/01_cleaning.ipynb
└── sujet_projet_AnSeqDa.md
```

---

## 5. Data collection

### Swissgrid
- Page: "Energy data CH" → section **"Energy Statistic Switzerland"** (one file per year).
- Downloaded 2009–2025: `.xls` for 2009–2019, `.xlsx` for 2020–2025. 2026 skipped (incomplete, not yet reliable).
- Ignored: "Control Area Balance" and "Total System Imbalance" (real-time balancing data, not consumption).
- Note for the report: the Swiss control block does not match Swiss territory exactly (includes Liechtenstein and small areas in France/Germany, excludes some Swiss grids around Laufenburg); deviation < 2 %.
- Data are published ~15 working days after month end and considered reliable after 6 months.

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
| 18 | 24 Dec, 31 Dec and the Christmas–New Year period are not official holidays but consumption is low (companies closed) | Not captured by the holiday variable | **Open** – planned for feature engineering: "Christmas period" variable (24 Dec – 2 Jan) and bridge days (Friday after Ascension) |
| 19 | Consumption vs temperature is not linear (flat above ~18 °C) | Heating stops above ~16–18 °C; a straight line would under-predict summer | **Planned** – heating degree days HDD = max(0, T_base − T) |
| 20 | Residual vs temperature correlation looked weak (−0.19) | Two confounders: holidays dominate the residual (±30 GWh), and the yearly cycle already contains the *normal* seasonal temperature | Excluded holidays and used the **temperature anomaly** (temp − normal for that day of year) → −0.559 |
| 21 | Consumption level dropped in 2022–23 and stayed low; test period (2024–25) is below most training data | Structural break (energy crisis, saving campaign, possibly rooftop solar) | **Open** – options: weight recent years more, model the trend/level explicitly, re-check the train/validation/test split; use validation year 2023 to detect over-prediction |
| 22 | Fixed-date holidays (Christmas, 1 August) do not appear among the largest residuals, moving ones do | The yearly cycle learns fixed dates automatically (spikes visible in `seasonal_365`); Easter/Ascension move by up to a month | Holiday variable needed mainly for **moving** holidays; keep it for all |
| 23 | Two measures with different units on one chart (consumption and temperature per year) | A dual y-axis chart can make lines look related or not depending on the scaling | Used **two stacked plots with a shared x-axis** |
| 24 | `fig.suptitle` duplicate title on pandas boxplot | pandas adds an automatic "Boxplot grouped by…" title | `fig.suptitle("")` |

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

---

## 14. Next steps

Data preparation (plan steps 1–2) and exploration (step 3) are **complete**. Next:

### Step 4 – Autocorrelation and stationarity (`notebooks/04_stationarity.ipynb`, presentation section 3)
Start from `dataset_daily.csv`, series `consumption_gwh`. Planned cells:
1. **Rolling mean and rolling std** (e.g. 30-day and 365-day windows) → visual check: does the level/variance change over time?
2. **ACF and PACF** of the raw series (`statsmodels.graphics.tsaplots.plot_acf / plot_pacf`): short lags (up to ~60) to see the weekly pattern (peaks at 7, 14, 21…) and long lags (up to ~400) to see the yearly cycle (~365).
3. **Stationarity tests** on the raw series: **ADF** (H0 = non-stationary) and **KPSS** (H0 = stationary) – use both, they complement each other.
4. **Differencing:** weekly difference `y − y.shift(7)` (seasonal, D = 1, s = 7), then if needed a first difference (d = 1); re-run ACF/PACF and ADF/KPSS after each step.
5. Read the ACF/PACF of the differenced series to propose **SARIMA (p, d, q)(P, D, Q)₇** orders.
6. Write down the decision on the **train / validation / test split** given the 2022–23 structural break (problem 21).

### Step 5 – Feature engineering
- HDD = max(0, T_base − T): choose T_base (~16–18 °C) from the consumption-vs-temperature scatter.
- Christmas-period variable (24 Dec – 2 Jan), bridge days (Friday after Ascension).
- Lags (t−1, t−7, t−365) and rolling means for the LSTM.

### Step 6 onwards
Baselines (naive, seasonal naive) → Holt-Winters → SARIMA → SARIMAX (HDD + holidays) → LSTM → evaluation on the same test period (MAE, RMSE, MAPE) → report.

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
- Risk for the test period: 2022–23 level shift.
- Suggested figures for section 2: consumption vs temperature, yearly consumption/temperature, weekday profile, monthly boxplot, MSTL decomposition, residual vs temperature anomaly.

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
