# Quick Start Guide - Shot Analysis Dashboard

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Place Your Data
Ensure your CSV file is in the same directory as `shot_analysis_app.py`

### Step 3: Run the App
```bash
streamlit run shot_analysis_app.py
```

---

## 📊 Common Use Cases

### Use Case 1: Analyze Player Performance
1. Open the app
2. Select player from sidebar
3. View pitch map and statistics
4. Check distance/angle conversion rates
5. Identify weak zones

**What to look for:**
- High conversion zones (red on heatmaps)
- Distance bins with low efficiency
- Angles where player struggles

---

### Use Case 2: Compare Shots Across Matches
1. Use Match filter to select multiple games
2. Observe changes in location preferences
3. Track consistency across different opponents

---

### Use Case 3: Analyze Shot Types
1. Filter by Shot Result to focus on:
   - Goals only
   - Missed shots
   - Saved shots
2. Compare location patterns for each type

---

### Use Case 4: Study Goal-Scoring Patterns
1. Filter for "Goal" result only
2. Look at combined heatmap
3. Identify most dangerous zones
4. Note distance-angle combinations that lead to goals

---

## 🎯 Key Metrics Explained

### Conversion Rate
- **Formula**: (Goals / Total Shots) × 100
- **Example**: 10 goals from 40 shots = 25% conversion rate
- **Interpretation**: Higher is better

### Distance Calculation
- **From**: Shot location coordinates
- **To**: Goal center (105m, 34m on standard pitch)
- **Method**: Euclidean distance
- **Unit**: Meters

### Angle Calculation
- **Definition**: Angle from perpendicular to goal line
- **Range**: 0-90 degrees (0° = straight on, 90° = wide)
- **Impact**: Narrower angles typically have higher conversion

---

## 📈 Interpreting Heatmaps

### Distance Heatmap
```
0-6m    6-12m   12-18m  18-24m  24+m
[40%]   [25%]   [15%]   [8%]    [2%]
```
- **Red** = High conversion (>30%)
- **Yellow** = Medium conversion (10-30%)
- **Green** = Low conversion (<10%)

### Angle Heatmap
```
0-10°   10-20°  20-30°  30-40°  40-50°  50-60°
[35%]   [28%]   [18%]   [12%]   [5%]    [2%]
```
- Typically decreases as angle increases
- Narrow angles more dangerous

### Combined Heatmap
- X-axis: Angle bins
- Y-axis: Distance bins
- Color intensity: Number of goals
- Brightest area = Most goals scored

---

## 🔧 Customization Examples

### Change Distance Bins
Edit `bin_distance()` function in `shot_analysis_app.py`:
```python
def bin_distance(distance):
    if distance < 8:
        return '0-8m'
    elif distance < 16:
        return '8-16m'
    # ... more bins
```

### Add New Filter
In `main()` function, add to sidebar:
```python
selected_situation = st.sidebar.multiselect(
    'Game Situation',
    df['situation'].unique(),
    default=df['situation'].unique()
)

# Then apply in filter:
filtered_df = filtered_df[filtered_df['situation'].isin(selected_situation)]
```

### Change Pitch Color
In `plot_pitch_with_shots()`:
```python
pitch = Pitch(
    pitch_color='#1a4d2e',    # Darker green
    line_color='white'
)
```

### Add xG Analysis
After getting filtered_df:
```python
total_xg = filtered_df['xG'].sum()
goals = filtered_df['is_goal'].sum()
st.metric('Expected Goals (xG)', round(total_xg, 2))
st.metric('Actual Goals', goals)
st.metric('Over/Under xG', round(goals - total_xg, 2))
```

---

## ❓ FAQ

### Q: How do I change the data file?
**A**: Update line 244 in `shot_analysis_app.py`:
```python
df = load_and_process_data('your_file.csv')
```

### Q: Can I use data from other sources?
**A**: Yes! Ensure your CSV has columns: X, Y, result, player, match_id
Run `validate_data()` from utils.py to check format.

### Q: How do I export the analysis?
**A**: Use the "View Detailed Shot Data" expander and right-click to save.
Or add this to the app:
```python
csv = filtered_df.to_csv(index=False)
st.download_button('Download', csv, 'shots.csv')
```

### Q: Can I modify the bins?
**A**: Yes! Edit `bin_distance()` and `bin_angle()` functions.
You may also need to update ordering lists in analysis functions.

### Q: Why is my visualization empty?
**A**: Check if:
1. Data is filtered correctly
2. CSV has valid X, Y coordinates (0-1)
3. Player/match selection has shots

### Q: How do I improve performance?
**A**: 
1. Use filters to reduce data size
2. Clear Streamlit cache: `streamlit cache clear`
3. Limit number of matches

### Q: Can I add more visualizations?
**A**: Yes! Add new plotting functions and call them in `main()`:
```python
def plot_my_viz(df):
    fig, ax = plt.subplots()
    # ... create plot
    return fig

# In main():
st.pyplot(plot_my_viz(filtered_df))
```

---

## 🐛 Troubleshooting

### Error: "No module named 'mplsoccer'"
```bash
pip install mplsoccer
```

### Error: "FileNotFoundError"
- Check CSV filename matches exactly
- Ensure file is in same directory as script
- Verify file is not corrupted

### Error: "KeyError: 'X'"
- Column name might be different case or spelled differently
- Check CSV headers with: `pd.read_csv('file.csv').head()`
- Update column references if needed

### Pitch visualization not appearing
- Check internet connection (mplsoccer may download resources)
- Try: `pip install --upgrade mplsoccer`
- Ensure matplotlib backend is working

### Slow performance
- Reduce number of matches selected
- Filter to fewer players
- Clear cache: `streamlit cache clear`
- Check system RAM availability

---

## 📚 Advanced Tips

### 1. Combine Filters
Use multiple filters for targeted analysis:
- Player: "Erling Haaland"
- Team: "Manchester City"
- Match: Select 3-4 recent matches
- Result: "Goal" only

### 2. Identify Trends
Compare 2-3 matches to see if:
- Player is moving further/closer for shots
- Angles of shots are changing
- Conversion rates improving/declining

### 3. Benchmark Analysis
- Note conversion rate for your player
- Compare with typical ranges:
  - Elite strikers: 15-25%
  - Good forwards: 10-15%
  - Average: 5-10%

### 4. Use in Tactical Analysis
- Identify strengths (high conversion zones)
- Identify weaknesses (low conversion zones)
- Tailor team tactics accordingly

### 5. Combine with Other Metrics
- Cross-reference with xG
- Note which assists lead to goals
- Track shot type effectiveness

---

## 📖 Additional Resources

### Understanding Expected Goals (xG)
- xG per shot indicates quality
- Sum of xG shows expected goal tally
- Compare actual goals to xG to assess luck

### Football Pitch Dimensions
- Standard: 105m × 68m
- Penalty area: 40.32m × 16.5m
- Goal box: 18.32m × 5.5m
- Coordinates normalized 0-1 in Understat data

### Conversion Rate Benchmarks
```
Distance        Elite     Good     Average
0-6m           50-70%    40-50%   30-40%
6-12m          20-30%    15-20%   10-15%
12-18m         5-15%     3-10%    1-5%
18-24m         2-5%      1-3%     0-2%
24+m           <2%       <1%      <1%
```

---

## 🎓 Learning Path

1. **Beginner**: Just run the app, explore filters
2. **Intermediate**: Read code comments, understand calculations
3. **Advanced**: Modify bin ranges, add new metrics, create custom plots
4. **Expert**: Build additional analysis modules using utils.py

---

## 💡 Pro Tips

✅ **Do:**
- Start with all data, then filter down
- Use specific match ranges for insights
- Compare multiple players for benchmarking
- Take screenshots of interesting findings
- Document your analysis

❌ **Don't:**
- Over-interpret small sample sizes (<5 shots)
- Forget to account for opponent quality
- Ignore context (injury, fatigue, tactics)
- Rely solely on location-based analysis

---

## 🔗 Data Sources

**Understat** (understat.com)
- Premier League data
- European competition data
- Player-level shot records
- Expected goals (xG) values

---

## Support & Contributing

Found an issue? Suggestions?
1. Check troubleshooting section
2. Verify data format with `validate_data()`
3. Review code comments for implementation details

---

**Version**: 1.0.0
**Last Updated**: 2026
**Compatible With**: Python 3.7+
