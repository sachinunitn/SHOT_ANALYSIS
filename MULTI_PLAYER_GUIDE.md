# Multi-Player Shot Analysis — Implementation Guide

## Overview

This guide explains how to use the new multi-player shot analysis system.
The system extends the original single-player Haaland dashboard with full
multi-player support, advanced metrics, and an interactive 5-tab Streamlit
dashboard.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Your Data

Place your CSV file (Understat format) in the project directory.

**Supported files (auto-detected):**
- `shot_data.csv` (multi-player)
- `erling_haaland_2022_understat.csv` (single-player fallback)

**Required columns:** `X`, `Y`, `result`, `player`

**Optional columns:** `date`, `h_team`, `a_team`, `xG`, `minute`, `shotType`,
`situation`, `match_id`, `h_a`, `lastAction`, `season`

### 3. Run the Dashboard

```bash
streamlit run streamlit_dashboard.py
```

---

## Module Overview

| Module | Purpose |
|--------|---------|
| `multi_player_config.py` | Centralised configuration |
| `data_processor.py` | Data loading, cleaning, feature engineering |
| `advanced_metrics.py` | Efficiency metrics, comparison, benchmarking |
| `visualizations.py` | Charts, heatmaps, radar charts, pitch maps |
| `streamlit_dashboard.py` | 5-tab interactive Streamlit app |

---

## Data Processing Pipeline

```python
from data_processor import MultiPlayerDataProcessor
from multi_player_config import get_multi_player_config

config = get_multi_player_config()
processor = MultiPlayerDataProcessor(config)

# 1. Load
df_raw = processor.load_from_csv('shot_data.csv')

# 2. Clean
df_clean = processor.preprocess(df_raw)

# 3. Engineer features
df_features = processor.add_features(df_clean)

# 4. Quality report
report = processor.data_quality_report(df_features)
print(report['player_summary'])
```

### What preprocessing does

1. Validates required columns
2. Coerces X/Y to float; auto-detects metre-scale coordinates and normalises
3. Drops rows with NULL X, Y, result, or player
4. Removes shots with out-of-range coordinates
5. Removes unknown result values
6. Standardises player/team name formatting
7. Fills missing `xG`, `minute`, `shotType`, `situation`
8. Drops duplicate shots

### Features added by `add_features`

| Column | Description |
|--------|-------------|
| `distance` | Euclidean distance to goal centre (metres) |
| `angle` | Shot angle from goal centre (degrees, 0–90) |
| `distance_bin` | Categorical: `0-5m`, `5-10m`, `10-15m`, `15-20m`, `20+m` |
| `angle_bin` | Categorical: `0-15°`, `15-30°`, `30-45°`, `45-60°+` |
| `in_penalty_box` | 1 if inside penalty box |
| `in_six_yard_box` | 1 if inside six-yard box |
| `quadrant` | `left`, `center`, or `right` |
| `in_half_space` | 1 if in half-space zone |
| `zone_label` | `6-Yard Box`, `Penalty Box`, `Half-Space`, `Outside Box` |
| `match_period` | `0-15`, `15-30`, …, `90+` |
| `home_away` | `Home` or `Away` |
| `xg_per_shot_label` | Quality band label based on xG value |

---

## Metrics

```python
from advanced_metrics import ShotMetricsCalculator, PlayerComparison

calculator = ShotMetricsCalculator(config)
comparison = PlayerComparison(config)

# All metrics for the dataset
metrics = calculator.calculate_all_metrics(df_features)

# Per-player table
per_player = calculator.per_player_metrics(df_features)

# Combined distance-angle pivot
pivot = calculator.combined_heatmap_data(df_features, metric='conversion_rate')

# Multi-player comparison
table = comparison.build_comparison_table(df_features, players=['Haaland', 'Kane'])

# Radar data (normalised 0–1)
radar = comparison.radar_data(df_features, players=['Haaland', 'Kane'])

# Rolling trend
trend = comparison.rolling_conversion_trend(df_features, 'Haaland', window=5)
```

### Available metrics

| Metric | Description |
|--------|-------------|
| `conversion_rate` | Goals / Shots × 100 |
| `xg_per_shot` | Total xG / Shots |
| `xg_difference` | Goals − xG (overperformance) |
| `ci_lower`, `ci_upper` | Wilson 95% confidence interval |
| `penalty_box_pct` | % of shots from penalty box |
| `benchmark` | Elite / Good / Average / Below Average |
| `overall_percentile` | Average percentile rank within cohort |

---

## Visualizations

```python
from visualizations import ShotVisualizer

viz = ShotVisualizer(config)

# Pitch shot map
fig = viz.plot_pitch_map(df_features, player='Erling Haaland')

# KDE density heatmap
fig = viz.plot_pitch_heatmap(df_features, show_goals_only=True)

# Distance-Angle combined heatmap
pivot = calculator.combined_heatmap_data(df_features, metric='goals')
fig = viz.plot_distance_angle_heatmap(pivot, metric='goals')

# Radar comparison
radar = comparison.radar_data(df_features)
fig = viz.plot_radar_comparison(radar)

# Scatter distance vs angle
fig = viz.plot_scatter_distance_angle(df_features, color_by='xG')

# Distribution histogram
fig = viz.plot_distribution(df_features, feature='distance', players=['Haaland'])

# Cumulative curve
cdf = calculator.cumulative_distribution(df_features, 'distance')
fig = viz.plot_cumulative_curve(cdf, 'distance')

# Rolling trend
trend = comparison.rolling_conversion_trend(df_features, 'Haaland')
fig = viz.plot_rolling_trend(trend, 'Haaland')
```

---

## Configuration

All settings live in `multi_player_config.py`.

### Change distance bins

```python
from multi_player_config import DISTANCE_BINS_CONFIG

DISTANCE_BINS_CONFIG['bins'] = [
    {'range': (0, 8),            'label': '0-8m'},
    {'range': (8, 16),           'label': '8-16m'},
    {'range': (16, float('inf')), 'label': '16+m'},
]
DISTANCE_BINS_CONFIG['order'] = ['0-8m', '8-16m', '16+m']
```

### Change angle bins

```python
from multi_player_config import ANGLE_BINS_CONFIG

ANGLE_BINS_CONFIG['bins'] = [
    {'range': (0, 20),           'label': '0-20°'},
    {'range': (20, 40),          'label': '20-40°'},
    {'range': (40, float('inf')), 'label': '40°+'},
]
ANGLE_BINS_CONFIG['order'] = ['0-20°', '20-40°', '40°+']
```

### Add a new player colour

```python
from multi_player_config import COLORS_CONFIG
COLORS_CONFIG['players'].append('#FF00FF')  # magenta
```

---

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| 📊 Overview & Comparison | KPI cards, comparison table, bar charts, radar |
| 🔍 Player Deep-Dive | Pitch map, scatter, distance/angle heatmaps, xG analysis |
| 🗺️ Zone Analysis | Pitch KDE heatmap, zone efficiency, quadrant breakdown |
| 📈 Trend Analysis | Rolling form, CDF curves, situation/period breakdown |
| 💾 Export & Data | CSV/JSON download, quality report, raw data view |

---

## Backward Compatibility

The original `shot_analysis_app.py` and `config.py` are unchanged.
Run the original single-player app at any time:

```bash
streamlit run shot_analysis_app.py
```

---

## Troubleshooting

**"No data file found"**
→ Place `shot_data.csv` or `erling_haaland_2022_understat.csv` in the app directory.

**"Missing required columns"**
→ Ensure your CSV has at minimum: `X`, `Y`, `result`, `player`.

**Charts not rendering**
→ Check that `matplotlib`, `mplsoccer`, `plotly` are installed.

**Slow dashboard**
→ Data is cached after first load. Reload the page to bust the cache if you update the CSV.
