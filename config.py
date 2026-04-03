"""
Configuration File for Shot Analysis Dashboard
===============================================

This file contains all customizable parameters.
Modify these settings to customize the app without changing main code.

Usage:
    from config import CONFIG, COLORS, BINS
"""

# ============================================================================
# DATA CONFIGURATION
# ============================================================================

DATA = {
    'csv_file': 'erling_haaland_2022_understat.csv',
    'pitch_length': 105,  # meters
    'pitch_width': 68,    # meters
    'goal_x': 1.0,        # normalized coordinate (attacking direction)
    'goal_y': 0.5,        # normalized coordinate (center)
}

# ============================================================================
# DISTANCE BINS CONFIGURATION
# ============================================================================

DISTANCE_BINS = {
    'bins': [
        {'range': (0, 6), 'label': '0-6m'},
        {'range': (6, 12), 'label': '6-12m'},
        {'range': (12, 18), 'label': '12-18m'},
        {'range': (18, 24), 'label': '18-24m'},
        {'range': (24, float('inf')), 'label': '24+m'},
    ],
    'order': ['0-6m', '6-12m', '12-18m', '18-24m', '24+m'],
}

# ============================================================================
# ANGLE BINS CONFIGURATION
# ============================================================================

ANGLE_BINS = {
    'bins': [
        {'range': (0, 10), 'label': '0-10°'},
        {'range': (10, 20), 'label': '10-20°'},
        {'range': (20, 30), 'label': '20-30°'},
        {'range': (30, 40), 'label': '30-40°'},
        {'range': (40, 50), 'label': '40-50°'},
        {'range': (50, 60), 'label': '50-60°'},
    ],
    'order': ['0-10°', '10-20°', '20-30°', '30-40°', '40-50°', '50-60°'],
}

# ============================================================================
# COLOR SCHEME
# ============================================================================

COLORS = {
    'goal': '#FF4444',              # Red
    'missed': '#FFFF44',            # Yellow
    'saved': '#FF9944',             # Orange
    'blocked': '#CCCCCC',           # Gray
    'pitch': '#22844e',             # Grass green
    'lines': 'white',               # Line color
    'heatmap_high': '#FF0000',      # Red for high conversion
    'heatmap_low': '#00FF00',       # Green for low conversion
}

# ============================================================================
# VISUALIZATION SETTINGS
# ============================================================================

VISUALIZATION = {
    'pitch_visualization': {
        'figsize': (10, 7),
        'pitch_type': 'normalizedyardstogoal',
        'linewidth': 1.5,
        'goal_marker_size': 150,
        'shot_marker_size': 100,
        'shot_alpha': 0.6,
        'goal_alpha': 0.9,
        'edge_linewidth': 0.5,
        'edge_color': 'black',
    },
    'heatmap': {
        'figsize': (12, 6),
        'colormap': 'YlOrRd',
        'cbar_label': 'Goals',
    },
    'distance_heatmap': {
        'figsize': (8, 3),
        'colormap': 'RdYlGn',
        'vmin': 0,
        'vmax': 100,
    },
    'angle_heatmap': {
        'figsize': (10, 3),
        'colormap': 'RdYlGn',
        'vmin': 0,
        'vmax': 100,
    },
}

# ============================================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================================

STREAMLIT = {
    'page_title': 'Shot Analysis Dashboard',
    'page_icon': '⚽',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded',
}

# ============================================================================
# DEFAULT FILTER VALUES
# ============================================================================

DEFAULTS = {
    'default_player_index': 0,  # Index in sorted player list
    'default_matches_to_show': 5,  # Number of matches to pre-select
    'show_all_results': True,  # Show all shot types by default
}

# ============================================================================
# METRIC THRESHOLDS & BENCHMARKS
# ============================================================================

BENCHMARKS = {
    'conversion_rate': {
        'elite': {'min': 15, 'max': 100},
        'good': {'min': 10, 'max': 15},
        'average': {'min': 5, 'max': 10},
        'below_average': {'min': 0, 'max': 5},
    },
    'distance_elite_conversion': {
        '0-6m': 50,
        '6-12m': 25,
        '12-18m': 10,
        '18-24m': 5,
        '24+m': 2,
    },
    'minimum_shots_for_analysis': 5,  # Avoid over-interpretation of small samples
}

# ============================================================================
# TEXT & LABELS
# ============================================================================

LABELS = {
    'app_title': '⚽ Advanced Shot Analysis Dashboard',
    'app_subtitle': '*Powered by Understat data & mplsoccer visualization*',
    'section_filters': '🎯 Filters',
    'section_shot_map': '🎯 Shot Map',
    'section_distance': '📏 Distance Analysis',
    'section_angle': '📐 Angle Analysis',
    'section_combined': '🔥 Combined Distance-Angle Heatmap (Goals)',
    'section_detailed': '📋 View Detailed Shot Data',
    'summary_header': '📊 Summary',
    'summary_shots': 'Shots',
    'summary_goals': 'Goals',
    'summary_conversion': 'Conversion',
}

# ============================================================================
# ADVANCED OPTIONS
# ============================================================================

ADVANCED = {
    'enable_data_caching': True,  # Cache data after first load
    'cache_ttl': None,  # None = cache indefinitely
    'show_expanded_stats': True,  # Show min/max in analysis
    'show_detailed_table': True,  # Show expandable data table
    'auto_refresh': False,  # Auto-refresh data on file change
    'debug_mode': False,  # Print debug information
}

# ============================================================================
# EXPORT SETTINGS
# ============================================================================

EXPORT = {
    'csv_delimiter': ',',
    'include_all_columns': True,
    'exclude_columns': [],  # Columns to exclude from export
    'date_format': '%Y-%m-%d',
}

# ============================================================================
# VALIDATION RULES
# ============================================================================

VALIDATION = {
    'required_columns': ['X', 'Y', 'result', 'player', 'match_id'],
    'optional_columns': ['date', 'h_team', 'a_team', 'xG', 'minute', 'shotType'],
    'valid_results': ['Goal', 'MissedShots', 'SavedShot', 'BlockedShot'],
    'x_range': (0, 1),
    'y_range': (0, 1),
}

# ============================================================================
# UI/UX SETTINGS
# ============================================================================

UI = {
    'column_gap': 'medium',  # streamlit gap size: 'small', 'medium', 'large'
    'column_widths': (1.2, 1.2, 1.0),  # Relative column widths
    'table_hide_index': True,
    'table_use_container_width': True,
    'show_summary_stats': True,
}

# ============================================================================
# FONT & STYLING
# ============================================================================

STYLE = {
    'title_fontsize': 14,
    'title_fontweight': 'bold',
    'title_pad': 20,
    'subtitle_fontsize': 12,
    'label_fontsize': 10,
    'annotation_fontweight': 'bold',
    'legend_framealpha': 0.9,
    'legend_loc': 'upper left',
}

# ============================================================================
# ANALYSIS PARAMETERS
# ============================================================================

ANALYSIS = {
    'minimum_shots_per_bin': 1,  # Don't filter out bins with few shots
    'show_percentage_decimals': 1,  # Decimal places for percentages
    'xg_decimals': 2,  # Decimal places for xG values
    'distance_decimals': 2,  # Decimal places for distance
    'angle_decimals': 1,  # Decimal places for angle
}

# ============================================================================
# FUNCTION: Get Configuration
# ============================================================================

def get_config():
    """Return complete configuration dictionary."""
    return {
        'DATA': DATA,
        'DISTANCE_BINS': DISTANCE_BINS,
        'ANGLE_BINS': ANGLE_BINS,
        'COLORS': COLORS,
        'VISUALIZATION': VISUALIZATION,
        'STREAMLIT': STREAMLIT,
        'DEFAULTS': DEFAULTS,
        'BENCHMARKS': BENCHMARKS,
        'LABELS': LABELS,
        'ADVANCED': ADVANCED,
        'EXPORT': EXPORT,
        'VALIDATION': VALIDATION,
        'UI': UI,
        'STYLE': STYLE,
        'ANALYSIS': ANALYSIS,
    }


# ============================================================================
# EXAMPLES OF CUSTOMIZATION
# ============================================================================

"""
EXAMPLE 1: Change distance bins
    DISTANCE_BINS['bins'] = [
        {'range': (0, 8), 'label': '0-8m'},
        {'range': (8, 16), 'label': '8-16m'},
        {'range': (16, 24), 'label': '16-24m'},
        {'range': (24, float('inf')), 'label': '24+m'},
    ]
    DISTANCE_BINS['order'] = ['0-8m', '8-16m', '16-24m', '24+m']

EXAMPLE 2: Change pitch color
    COLORS['pitch'] = '#1a4d2e'  # Darker green
    COLORS['lines'] = '#CCCCCC'  # Gray lines

EXAMPLE 3: Change figure size
    VISUALIZATION['pitch_visualization']['figsize'] = (12, 8)

EXAMPLE 4: Disable caching
    ADVANCED['enable_data_caching'] = False

EXAMPLE 5: Change data file
    DATA['csv_file'] = 'my_data.csv'

EXAMPLE 6: Custom column colors
    COLORS['goal'] = '#00AA00'  # Green goals
    COLORS['missed'] = '#AA0000'  # Red misses
"""

# ============================================================================
# VALIDATION FUNCTION
# ============================================================================

def validate_config():
    """
    Validate configuration consistency.
    
    Returns:
    --------
    bool
        True if configuration is valid
    """
    # Check distance bins
    if len(DISTANCE_BINS['bins']) != len(DISTANCE_BINS['order']):
        print("ERROR: Distance bins and order mismatch")
        return False
    
    # Check angle bins
    if len(ANGLE_BINS['bins']) != len(ANGLE_BINS['order']):
        print("ERROR: Angle bins and order mismatch")
        return False
    
    # Check colors
    required_colors = ['goal', 'missed', 'saved', 'blocked', 'pitch', 'lines']
    for color in required_colors:
        if color not in COLORS:
            print(f"WARNING: Missing color '{color}'")
    
    return True


if __name__ == "__main__":
    # Test configuration
    if validate_config():
        print("✅ Configuration is valid")
        config = get_config()
        print(f"✅ Loaded {len(config)} configuration sections")
    else:
        print("❌ Configuration validation failed")
