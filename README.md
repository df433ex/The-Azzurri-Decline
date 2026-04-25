# Has Inequality Killed the Azzurri?
### A Data Story of Serie A's Decline

*Diego Fasano, BEE2041 — University of Exeter, 2025/26*

---

## Read the blog here:

**[https://df433ex.github.io/The_Azzurri_Decline/]**

---

## The question

Italy failed to qualify for the 2018, 2022 and 2026 FIFA World Cups. The first such failures since 1958. The popular explanation is structural: Serie A's openness to foreign players has crowded out Italian talent and concentrated wealth in a few clubs, leaving the national team with a thinner pool to draw from. 

This project tests that explanation against the data, trying to prove or dispruve tha popular explanation.

## In a few words: What does the data actually show?

Unfortunately for the Itlian public, and therefore myself, the headline finding is **negative**: in this dataset, Serie A's foreign-player share does not predict Italy's tournament performance, and Serie A's Gini coefficient is roughly mid-pack among Europe's top leagues — not the outlier the popular narrative would predict.

That doesn't make the structural concerns wrong, but it does mean the simple "open league = losing nation" story isn't supported by the relatively small sample we have. The blog walks through two complementary lenses — **wealth concentration** (Gini across leagues) and **foreign-player share** (Serie A vs peers) — and lands on an interesting conclusion: *Italy's Serie A is no more concentrated than its peers, its foreigner share is middle-of-the-pack, and neither predicts Italy's tournament fate in the small sample we have.* So not the wanted answer, but very much the needed answer.

## What's in ther project:
| Notebook | What it does |
|----------|--------------|
| `notebooks/01_scraping.ipynb` | Scrapes Transfermarkt for squad market values + nationalities (10 leagues, 2006-2026), plus Italy national-team squads for 8 tournaments |
| `notebooks/02_cleaning.ipynb` | SQL + Python pipeline: aggregates to league-season level, computes Gini per league-season, joins Italy squads to leagues |
| `notebooks/03_eda.ipynb`      | 6 figures: cross-league Gini, foreign %, Italy results timeline, Italy squad-depth strip plot, league size vs concentration scatter, Italy squad-value bars |
| `notebooks/04_modelling.ipynb` | 3 OLS regressions on Italy's tournament performance + a panel regression of Gini on foreign % across 10 leagues |

## Project structure

```
.
├── README.md                               
├── PROJECT_PLAN.md                         <- This has been exluded from the final submission.
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/
│   │   ├── league_club_data.csv            <- club-season values, 10 leagues × ~20 seasons
│   │   ├── italy_squad_selections.csv      <- player names + market values, 10 Italy tournaments/qualifiers
│   │   └── italy_results.csv               <- Italy at WC + Euro, 1980-2024
│   └── clean/
│       ├── league_season.csv               <- 197 rows: league-season aggregates incl. Gini
│       ├── italy_squad_clean.csv           <- player-tournament with within-squad value ranking
│       ├── italy_final.csv                 <- one row per Italy tournament w/ squad aggregates
│       └── modelling_dataset.csv           <- exact rows fed to the regressions
├── notebooks/                              <- (see table above)
├── src/
│   └── helpers.py                          <- gini(), parse_market_value(), safe_get(), etc. to help with python.
└── output/
    ├── figures/
    │   ├── fig1_gini_leagues.png           <- Gini across 10 leagues, 2006-25 (Italy highlighted)
    │   ├── fig2_foreign_pct.png            <- % foreign players, all leagues
    │   ├── fig3_italy_results.png          <- Italy timeline 1980-2024
    │   ├── fig4_squad_depth.png            <- strip plot of player market values within each Italy squad
    │   ├── fig5_scatter_gini_value.png     <- league size vs concentration, 2025-26
    │   ├── fig6_italy_squad_value.png      <- Italy's squad value at each tournament
    ├── model1_summary.txt                  <- performance ~ Serie A foreign %
    ├── model2_summary.txt                  <- performance ~ Italy squad value (placebo)
    ├── model3_summary.txt                  <- performance ~ Serie A foreign % gap
    └── panel_summary.txt                   <- summary of the regressions
```

## Data

| Dataset | Source | Coverage | Method |
|---------|--------|----------|--------|
| Club squad values + foreigner counts | Transfermarkt | 10 leagues × 20 seasons (2006-2025) | Web scraping (`requests` + `BeautifulSoup`) |
| Italy squad selections | Transfermarkt kader pages | 8 tournaments + 2 qualifier squads (2006-2024) | Web scraping (player names + market values) |
| Italy international results | Wikipedia (manual) | 1980-2024 | Hand-coded from match records |

The 10 leagues are England, Spain, Germany, Italy, France, Portugal, Netherlands, Belgium, Turkey, Czechia — the top of the UEFA country coefficient ranking.

### Known data limitations

It is important to document these are they are large:

1. **League data starts 2006.** Earlier seasons aren't in the scraped dataset as too much data is lacking from online resources. The modelling N is 9 tournaments (2008-2024), which is way too small to prove causal reletionships.
2. **Performance score is ordinal but treated as continuous.** A round of 16 isn't twice as good as a group-stage exit. Robustness check would be ideal, but with N=9 it would be impossible.
3. **Tournament squads are observed at the player/value level only.** We scrape player names and market values from Transfermarkt's kader pages, not club affiliations. So the analysis focuses on squad-value concentration and depth rather than where Italian players earn their living, this is because reliably scraping information on the country the players played in, or the club, is difficult without scraping websites that openly resist scraping methods.

## Methodology in one paragraph

I built a country-season panel from Transfermarkt by scraping each league's "Vereine" page for every season 2006-07 through 2025-26 (10 leagues × 20 seasons = 200 league-season rows) and a player-tournament panel from Italy's national team kader pages. SQL (in-memory SQLite) handles the set-based work: group-bys, joins, window functions for ranking players within squads. Python handles the numerical work: Gini coefficients, regressions. We then estimate three OLS regressions of Italy's tournament performance score on:
(i) Serie A foreign-player share;
(ii) Italy's own squad market value (a placebo);
(iii) the gap between Serie A's foreign share and the average of the other 9 leagues. 
Standard errors are HC1 robust. Finally, a panel OLS of Gini on foreign player share across all 10 leagues, with country and year fixed effects and standard errors clustered at the country level.

## How to reproduce

```bash
git clone <repo-url>
cd "Data Science Project"

python -m venv venv
source venv/bin/activate            # macOS / Linux
# venv\Scripts\activate              # Windows

pip install -r requirements.txt

# Run notebooks in order:
jupyter notebook notebooks/01_scraping.ipynb
jupyter notebook notebooks/02_cleaning.ipynb
jupyter notebook notebooks/03_eda.ipynb
jupyter notebook notebooks/04_modelling.ipynb
```

> Raw CSVs are committed in `data/raw/` so step 1 can be skipped. Transfermarkt sometimes 429-blocks automated requests, so re-running the scraper isn't required for the analysis to be reproducible from raw → clean → figures.

## Author

Diego Fasano, BEE2041, University of Exeter, 2025-26.
