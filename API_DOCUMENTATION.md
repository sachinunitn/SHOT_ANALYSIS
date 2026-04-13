# API Documentation

## `multi_player_config.py`

Centralised configuration for all modules.

### Functions

#### `get_multi_player_config() → dict`

Return the full configuration dictionary.

```python
config = get_multi_player_config()
```

#### `get_distance_bin_labels() → list[str]`

Return ordered distance bin labels (e.g. `['0-5m', '5-10m', …]`).

#### `get_angle_bin_labels() → list[str]`

Return ordered angle bin labels (e.g. `['0-15°', '15-30°', …]`).

#### `get_player_color(index: int) → str`

Return hex colour for player at position `index`.

#### `validate_multi_config() → bool`

Validate configuration consistency. Prints errors and returns `True` if valid.

### Key Config Sections

| Key | Description |
|-----|-------------|
| `DATA` | Pitch dimensions, goal coordinates, zone thresholds |
| `DISTANCE_BINS` | Distance bucket definitions and order |
| `ANGLE_BINS` | Angle bucket definitions and order |
| `ZONES` | Danger zone, quadrant, half-space definitions |
| `BENCHMARKS` | Elite/Good/Average/Below thresholds |
| `COLORS` | Shot results, pitch, heatmaps, player palette |
| `VISUALIZATION` | Figure sizes, colormaps per chart type |
| `STREAMLIT` | Page config, tab labels, cache TTL |
| `FEATURES` | Distance/angle/coordinate validation ranges |
| `VALIDATION` | Required/optional columns, valid values |
| `STATISTICS` | Confidence level, bootstrap, percentile bins |
| `EXPORT` | Column selection, date format |
| `ADVANCED` | Feature toggles (half-space, CDF, radar, etc.) |
| `RADAR` | 6 radar metric definitions with scales |

---

## `data_processor.py`

### Class `MultiPlayerDataProcessor`

#### `__init__(config: dict)`

Initialise with configuration from `get_multi_player_config()`.

#### `load_from_csv(filepath: str, sep: str = None) → pd.DataFrame`

Load a CSV file with auto-detected delimiter.

**Raises:** `FileNotFoundError`, `ValueError` (if < 2 columns).

#### `preprocess(df: pd.DataFrame) → pd.DataFrame`

Full cleaning pipeline:
- Validate required columns
- Coerce coordinates to float; normalise metre-scale if needed
- Drop NULL critical values
- Remove out-of-range coordinates
- Remove invalid result values
- Standardise player/team names
- Fill optional missing values (xG, minute, shotType, situation)
- Drop duplicate rows
- Add `is_goal` flag

#### `add_features(df: pd.DataFrame) → pd.DataFrame`

Add derived columns:
`distance`, `angle`, `distance_bin`, `angle_bin`, `in_penalty_box`,
`in_six_yard_box`, `quadrant`, `in_half_space`, `zone_label`,
`match_period`, `home_away`, `match_year`, `match_month`, `xg_per_shot_label`

#### `optimise_bins(df, feature, n_bins) → list[dict]`

Suggest quantile-based bin boundaries for `feature`.

#### `filter_by_player(df, player) → pd.DataFrame`
#### `filter_by_players(df, players) → pd.DataFrame`
#### `filter_by_result(df, results) → pd.DataFrame`
#### `filter_by_season(df, season) → pd.DataFrame`
#### `filter_by_date_range(df, start, end) → pd.DataFrame`

Filtering helpers.

#### `data_quality_report(df) → dict`

Return quality report with row counts, player summary, missing values,
coordinate stats, distance stats, angle stats, and processing log.

---

## `advanced_metrics.py`

### Class `ShotMetricsCalculator`

#### `__init__(config: dict)`

#### `calculate_all_metrics(df) → dict`

Return nested dict with keys:
`overall`, `by_distance`, `by_angle`, `by_shot_type`, `by_situation`,
`by_period`, `by_zone`, `xg_analysis`, `per_player`

#### `overall_metrics(df) → dict`

Keys: `shots`, `goals`, `conversion_rate`, `conversion_ci_lower`,
`conversion_ci_upper`, `total_xg`, `xg_per_shot`, `xg_difference`,
`avg_distance`, `avg_angle`, `performance_label`

#### `metrics_by_segment(df, segment_col, segment_order=None) → pd.DataFrame`

Columns: `segment_col`, `shots`, `goals`, `total_xg`, `conversion_rate`,
`xg_per_shot`, `xg_difference`, `ci_lower`, `ci_upper`, `small_sample`

#### `xg_analysis(df) → dict`

Keys: `total_xg`, `total_goals`, `xg_difference`, `overperformance_pct`,
`xg_per_shot`, `performance_label`, `xg_breakdown`

#### `per_player_metrics(df) → pd.DataFrame`

Index: player name. Columns include all `overall_metrics` keys plus
`penalty_box_pct`, `dominant_foot`.

#### `combined_heatmap_data(df, metric='goals', player=None) → pd.DataFrame`

Pivot: distance_bin rows × angle_bin columns.
Metrics: `'goals'`, `'shots'`, `'conversion_rate'`, `'xg'`

#### `cumulative_distribution(df, feature='distance', player=None) → pd.DataFrame`

Columns: `feature`, `cumulative_shots`, `cumulative_goals`,
`cumulative_conversion`

---

### Class `PlayerComparison`

#### `__init__(config: dict)`

#### `build_comparison_table(df, players=None) → pd.DataFrame`

Multi-player comparison table with percentile ranks and benchmark labels.

#### `radar_data(df, players=None) → dict[str, dict[str, float]]`

Normalised (0–1) radar values per player.
`{player: {metric_key: value, …}}`

#### `benchmark_players(df, players=None) → pd.DataFrame`

Players with `overall_percentile` and benchmark tiers.

#### `rolling_conversion_trend(df, player, window=5) → pd.DataFrame`

Columns: `date` (if available), `rolling_conversion`

#### `form_summary(df, player, n_shots=10) → dict`

Recent form metrics for last `n_shots` shots.

---

## `visualizations.py`

### Class `ShotVisualizer`

All methods return `matplotlib.figure.Figure` unless noted.

#### `plot_pitch_map(df, player=None, title=None, figsize=None)`

Shot locations on football pitch with colour-coded results.

#### `plot_pitch_heatmap(df, player=None, show_goals_only=False, figsize=None)`

KDE shot density heatmap on pitch.

#### `plot_distance_angle_heatmap(pivot_data, metric='goals', title=None, figsize=None)`

2-D heatmap: distance rows × angle columns.

#### `plot_metric_bars(segment_df, segment_col, metric, title=None, figsize=None, color)`

Horizontal bar chart for a metric by segment, with CI whiskers.

#### `plot_player_comparison_bars(comparison_df, metric, title=None, figsize=None)`

Vertical bar chart comparing players on a metric.

#### `plot_radar_comparison(radar_dict, metric_labels=None, title, figsize=None)`

Spider/radar chart comparing players on 6 normalised dimensions.

#### `plot_scatter_distance_angle(df, color_by='result', player=None, figsize=None)`

Scatter: distance on X, angle on Y, coloured by result or xG.

#### `plot_distribution(df, feature='distance', players=None, figsize=None)`

Overlaid density histograms for one or more players.

#### `plot_cumulative_curve(cdf_df, feature, player=None, figsize=None)`

Dual-axis: cumulative shots/goals (left) and conversion % (right).

#### `plot_rolling_trend(trend_df, player, window=5, figsize=None)`

Rolling conversion rate line chart with season-average reference.

#### `plot_conversion_by_distance(segment_df, figsize=None)`

1-D heatmap of conversion rate per distance bin.

#### `plot_conversion_by_angle(segment_df, figsize=None)`

1-D heatmap of conversion rate per angle bin.

#### `plot_interactive_heatmap(pivot_data, metric, title=None)`

Plotly interactive heatmap. Returns `plotly.graph_objects.Figure` or `None`.

#### `plot_interactive_scatter(df, color_by, player=None, title=None)`

Plotly interactive scatter. Returns `plotly.graph_objects.Figure` or `None`.

---

## `streamlit_dashboard.py`

### Entry point

```python
if __name__ == '__main__':
    main()
```

or via CLI:

```bash
streamlit run streamlit_dashboard.py
```

### Cached functions

#### `load_data(filepath: str) → pd.DataFrame`

`@st.cache_data` — loads, preprocesses, and feature-engineers the CSV.

#### `compute_player_metrics(df_json: str) → pd.DataFrame`

`@st.cache_data` — per-player metric table from JSON-serialised df.

### Tab renderers

| Function | Tab |
|----------|-----|
| `render_tab_overview` | 📊 Overview & Comparison |
| `render_tab_deep_dive` | 🔍 Player Deep-Dive |
| `render_tab_zones` | 🗺️ Zone Analysis |
| `render_tab_trends` | 📈 Trend Analysis |
| `render_tab_export` | 💾 Export & Data |

### `build_sidebar(df, config) → dict`

Builds sidebar filters and returns filter state dict with keys:
`players`, `seasons`, `date_range`, `results`, `shot_types`,
`situations`, `min_xg`

### `apply_filters(df, …) → pd.DataFrame`

Applies all filter state to the full dataframe.
