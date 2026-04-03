# ⚽ Advanced Shot Analysis Dashboard

A comprehensive Streamlit web application for analyzing football shot data from Understat with advanced visualizations using mplsoccer.

## Features

### 📊 Core Functionality
- **Shot Map Visualization**: Football pitch with color-coded shots using mplsoccer
- **Distance Analysis**: Shots grouped by distance bins with conversion rates
  - 0–6 meters
  - 6–12 meters
  - 12–18 meters
  - 18–24 meters
  - 24+ meters
- **Angle Analysis**: Shots grouped by angle relative to goal
  - 0–10°, 10–20°, 20–30°, 30–40°, 40–50°, 50–60°
- **Combined 2D Heatmap**: Goals visualized by distance-angle combinations
- **Interactive Filters**: Player, team, match, and shot result filters

### 🎨 Visualizations
- Pitch shot map with color-coded outcomes (Goals, Missed, Saved, Blocked)
- Conversion rate heatmaps by distance and angle
- 2D goal density heatmap
- Detailed shot statistics tables

### 🔧 Technical Features
- Modular, well-documented Python code
- Efficient pandas operations with caching
- Responsive layout optimized for analysis
- Data-driven insights and statistics

## Installation

### 1. Prerequisites
- Python 3.7+
- pip package manager

### 2. Clone/Download Project
```bash
# Navigate to your project directory
cd shot-analysis-dashboard
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Alternatively, install packages individually:
```bash
pip install streamlit pandas numpy matplotlib mplsoccer scipy
```

## Usage

### 1. Prepare Your Data
- Place your Understat CSV file in the same directory as `shot_analysis_app.py`
- Expected filename: `erling_haaland_2022_understat.csv`
- If using a different filename, update line 244 in the script

### 2. Run the App
```bash
streamlit run shot_analysis_app.py
```

The app will open in your default browser at `http://localhost:8501`

### 3. Using the Dashboard

#### Filters (Sidebar)
- **Player**: Select which player's shots to analyze
- **Team**: Filter by team(s)
- **Match**: Select specific matches (or leave empty for all)
- **Shot Result**: Choose shot outcomes to include
  - Goal
  - MissedShots
  - SavedShot
  - BlockedShot

#### Main Dashboard
1. **Left Panel**: Shot map on the football pitch
2. **Center Panel**: Distance-based analysis with conversion rates
3. **Right Panel**: Angle-based analysis with conversion rates
4. **Bottom**: Combined 2D heatmap showing goal distribution
5. **Footer**: Expandable detailed shot data table

## Data Requirements

Your CSV must contain these columns:
```
- X: Shot X coordinate (0-1, normalized)
- Y: Shot Y coordinate (0-1, normalized)
- result: Shot outcome (Goal, MissedShots, SavedShot, BlockedShot, etc.)
- player: Player name
- h_team: Home team name
- a_team: Away team name
- match_id: Unique match identifier
- date: Match date
- xG: Expected goals value
- (Optional) Other descriptive fields
```

## Code Structure

### Main Sections

1. **Utility Functions** (Lines 26-86)
   - `calculate_distance()`: Computes distance from shot to goal
   - `calculate_angle()`: Computes angle relative to goal
   - `bin_distance()`, `bin_angle()`: Categorize metrics into bins

2. **Data Processing** (Lines 88-124)
   - `load_and_process_data()`: Loads CSV and computes metrics
   - Cached for performance

3. **Analysis Functions** (Lines 126-182)
   - `get_distance_analysis()`: Aggregates by distance
   - `get_angle_analysis()`: Aggregates by angle
   - `get_combined_analysis()`: Creates 2D distance-angle matrix

4. **Visualization Functions** (Lines 184-320)
   - `plot_pitch_with_shots()`: mplsoccer pitch visualization
   - `plot_distance_heatmap()`: Distance conversion heatmap
   - `plot_angle_heatmap()`: Angle conversion heatmap
   - `plot_combined_heatmap()`: 2D goal density heatmap

5. **Streamlit App** (Lines 322-460)
   - `main()`: App layout and interactivity
   - Sidebar filters
   - 3-column layout for comprehensive analysis

## Key Calculations

### Distance Formula
```
Distance = √[(x_meters - goal_x)² + (y_meters - goal_y)²]
```
- Coordinates converted from normalized (0-1) to meters
- Standard pitch: 105m × 68m
- Goal center: (105, 34)

### Angle Formula
```
Angle = arctan(|y_meters - goal_y_meters| / (distance_to_goal))
```
- Angle in degrees, 0° = perpendicular to goal
- Accounts for horizontal distance from center

## Customization

### Change Bin Ranges
Edit the `bin_distance()` and `bin_angle()` functions:
```python
def bin_distance(distance):
    if distance < 5:
        return '0-5m'
    # ... add more conditions
```

### Modify Pitch Appearance
Edit the `plot_pitch_with_shots()` function:
```python
pitch = Pitch(
    pitch_type='normalizedyardstogoal',  # Change pitch type
    pitch_color='#22844e',                # Change color
    line_color='white'                    # Change line color
)
```

### Change Color Scheme
Modify colors in visualization functions:
- Goals: `color='red'`
- Missed: `color='yellow'`
- Saved: `color='orange'`
- Blocked: `color='gray'`

## Troubleshooting

### "ModuleNotFoundError"
Install missing packages:
```bash
pip install -r requirements.txt
```

### File Not Found Error
Ensure your CSV file is in the same directory as the script and named correctly:
```python
df = load_and_process_data('your_file.csv')
```

### Visualization Issues
- Check mplsoccer installation: `pip install --upgrade mplsoccer`
- Ensure matplotlib backend is configured correctly
- Clear cache: `streamlit cache clear`

## Performance Tips

1. **Filter Data**: Use sidebar filters to reduce computation
2. **Caching**: Data is cached automatically with `@st.cache_data`
3. **Match Limits**: Pre-select matches instead of loading all
4. **Large Datasets**: Consider sampling data for initial analysis

## Dependencies Explained

| Package | Purpose |
|---------|---------|
| **streamlit** | Web app framework |
| **pandas** | Data manipulation and analysis |
| **numpy** | Numerical computations |
| **matplotlib** | Visualization backend |
| **mplsoccer** | Football pitch visualization |
| **scipy** | Scientific computing utilities |

## Example Workflow

1. Launch the app
2. Use sidebar to select a player (e.g., "Erling Haaland")
3. Choose teams, matches, and shot results
4. Observe pitch map and statistics
5. Analyze distance-based conversion rates
6. Review angle-based insights
7. Examine combined heatmap for patterns
8. Export data or take screenshots as needed

## Advanced Usage

### Adding New Metrics
Add to `load_and_process_data()`:
```python
df['new_metric'] = df.apply(lambda row: calculate_new_metric(row), axis=1)
```

### Custom Filters
Add to sidebar in `main()`:
```python
selected_situation = st.sidebar.multiselect('Situation', df['situation'].unique())
```

### Export Analysis
Add to the app:
```python
csv = filtered_df.to_csv(index=False)
st.download_button('Download Data', csv, 'shots.csv')
```

## License

This project is provided as-is for educational and analytical purposes.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify data format
3. Ensure all dependencies are installed
4. Review the detailed code comments

---

**Created**: 2024
**Last Updated**: 2026
**Technologies**: Python, Streamlit, mplsoccer, pandas, matplotlib
