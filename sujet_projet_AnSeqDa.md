# Projet AnSeqDa – Analysis of Sequential Data

## Sujet

**Analyse et prévision de la consommation électrique en Suisse (2009–2025)**

Analyse de la série temporelle de la consommation électrique de la Suisse (tendance, saisonnalités journalière/hebdomadaire/annuelle, ruptures COVID 2020 et crise énergétique 2022), puis prédiction de la consommation future.

**Question de recherche :** peut-on prédire précisément la consommation électrique suisse, et dans quelle mesure la météo (température) améliore-t-elle la prévision ?

---

## Plan de travail

### 0. Cadrage (semaine 1)
- **Horizon principal :** consommation journalière, prévision sur plusieurs semaines/mois.
  - Extensions possibles : prévision horaire (J+1), tendance mensuelle long terme.
- **Découpage :** entraînement 2009–2022, validation 2023, test 2024 – mi-2025.
  - Ne pas utiliser les mois les plus récents (données Swissgrid définitives seulement après ~6 mois).
- **Métriques :** MAE, RMSE, MAPE.

### 1. Collecte des données
- **Swissgrid :** fichiers annuels « EnergieÜbersichtCH » 2009–2025.
  - Utiliser la colonne de consommation des utilisateurs finaux (« Summe endverbrauchte Energie Regelblock Schweiz ») plutôt que la consommation totale, qui inclut le pompage-turbinage (dépend des prix, pas de la demande).
- **MétéoSuisse :** température moyenne journalière de quelques stations représentatives (Zurich, Berne, Genève, Lugano), moyennées.
- **Jours fériés suisses :** librairie Python `holidays`.

### 2. Nettoyage et préparation
- Fusionner les fichiers annuels en une seule série, vérifier la continuité des timestamps.
- Gérer les changements d'heure (jours à 92 ou 100 quarts d'heure au lieu de 96).
- Détecter valeurs manquantes et outliers.
- Agréger de 15 min en horaire et journalier ; convertir kWh → GWh.

### 3. Analyse exploratoire
- Série complète et tendance annuelle.
- Profils saisonniers : journée type, semaine type, boxplots par mois et par jour de la semaine.
- Statistiques descriptives et distribution.
- Décomposition STL (tendance, saisonnalité, résidu).
- Consommation vs température (forme en U/L : chauffage en hiver).
- Identification des ruptures : COVID 2020, économies d'énergie hiver 2022–23, fêtes de fin d'année.

### 4. Autocorrélation et stationnarité
- ACF / PACF (saisonnalité hebdomadaire lag 7, annuelle).
- Moyenne et écart-type glissants.
- Tests ADF et KPSS ; différenciation si nécessaire.

### 5. Feature engineering
- Variables calendaires : jour de la semaine, mois, jours fériés, ponts.
- Degrés-jours de chauffage (HDD) à partir de la température.
- Lags (t−1, t−7, t−365) et moyennes glissantes.

### 6. Modélisation (du plus simple au plus complexe)
1. **Baselines :** naïf et naïf saisonnier (même jour semaine/année précédente). Tous les modèles doivent faire mieux.
2. **Smoothing :** Holt-Winters (triple exponential smoothing) / ETS.
3. **ARIMA :** SARIMA (saisonnalité hebdomadaire s = 7 + termes de Fourier pour l'annuel), puis **SARIMAX** avec température (HDD) et jours fériés comme variables exogènes.
4. **LSTM :** avec température et variables calendaires en entrée.
5. *Optionnel si le temps le permet :* Prophet, LightGBM/XGBoost.

### 7. Évaluation
- Comparaison de tous les modèles sur la même période de test 2024–2025 (MAE, RMSE, MAPE).
- Validation croisée walk-forward (rolling origin).
- Diagnostics des résidus : test de Ljung-Box, autocorrélation des résidus.
- Intervalles de prédiction.
- Limite à mentionner : utiliser la température *observée* sur la période de test est optimiste ; en pratique, on n'aurait que des *prévisions* météo.

### 8. Interprétation et rapport
- Quel modèle gagne, et de combien la température améliore la prévision ?
- Où le modèle échoue (jours fériés, COVID, crise 2022) ?
- Conclusions et limites.

---

## Structure de la présentation (alignée sur le cours)
1. Présentation des données
2. Exploration des données
3. Autocorrélation et stationnarité
4. Prévision avec smoothing
5. Prévision avec ARIMA (SARIMA / SARIMAX)
6. Prévision avec LSTM
7. Comparaison des modèles et conclusion

---

## Outils
Python : `pandas`, `matplotlib` / `seaborn`, `statsmodels` (STL, SARIMAX, tests), `pmdarima` (auto-ARIMA), `scikit-learn`, `tensorflow`/`keras` ou `pytorch` (LSTM), notebooks Jupyter.

---

## Planning indicatif (~8 semaines)

| Semaine | Travail |
|---|---|
| 1 | Cadrage et collecte des données |
| 2 | Nettoyage et préparation |
| 3 | Analyse exploratoire, autocorrélation, stationnarité |
| 4 | Feature engineering et baselines |
| 5 | Smoothing et SARIMA / SARIMAX |
| 6 | LSTM |
| 7 | Évaluation et comparaison |
| 8 | Rapport et présentation |

---

## Sources

- Swissgrid – Energy data CH (téléchargement des données) : https://www.swissgrid.ch/en/home/customers/topics/energy-data-ch
- Swissgrid – Consommation (load) : https://www.swissgrid.ch/en/home/operation/grid-data/load.html
- Swissgrid – Transmission (import/export) : https://swissgrid.ch/en/home/operation/grid-data/transmission.html
- MétéoSuisse – Données climatiques : https://www.meteoswiss.admin.ch
- Exemple de notebook chargeant les données Swissgrid : https://nbviewer.org/github/tbreitbach/edh_group_04/blob/main/egdh_group_04_notebook.ipynb
