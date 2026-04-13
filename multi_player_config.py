"""
Multi-Player Shot Analysis Configuration
=========================================

Centralized configuration for all multi-player shot analysis modules.
Supports multiple datasets/players, configurable bins, benchmark percentiles,
color palettes, and export settings.

Usage:
    from multi_player_config import get_multi_player_config, MULTI_CONFIG
"""

# ============================================================================
# DATA CONFIGURATION
# ============================================================================

DATA_CONFIG = {
    'default_csv_file': 'shot_data.csv',
    'fallback_csv_file': 'erling_haaland_2022_understat.csv',
    'pitch_length': 105,    # meters
    'pitch_width': 68,      # meters
    'goal_x': 1.0,          # normalized coordinate (attacking direction)
    'goal_y': 0.5,          # normalized coordinate (center)
    'goal_width': 7.32,     # meters (actual goal width)
    'goal_height': 2.44,    # meters (actual goal height)
    'penalty_spot_x': 0.882,  # normalized (~11m from goal line)
    'penalty_box_x': 0.835,   # normalized (~18-yard box edge)
    'penalty_box_y_min': 0.21,
    'penalty_box_y_max': 0.79,
    'six_yard_box_x': 0.943,  # normalized (~6-yard box edge)
    'six_yard_box_y_min': 0.37,
    'six_yard_box_y_max': 0.63,
}

# ============================================================================
# DISTANCE BINS (statistically justified)
# ============================================================================

DISTANCE_BINS_CONFIG = {
    'bins': [
        {'range': (0, 5),            'label': '0-5m',   'danger': 'extreme'},
        {'range': (5, 10),           'label': '5-10m',  'danger': 'high'},
        {'range': (10, 15),          'label': '10-15m', 'danger': 'medium'},
        {'range': (15, 20),          'label': '15-20m', 'danger': 'low'},
        {'range': (20, float('inf')), 'label': '20+m',  'danger': 'very_low'},
    ],
    'order': ['0-5m', '5-10m', '10-15m', '15-20m', '20+m'],
    'danger_colors': {
        'extreme':  '#FF0000',
        'high':     '#FF6600',
        'medium':   '#FFAA00',
        'low':      '#FFDD00',
        'very_low': '#00CC00',
    },
    'optimization': {
        'min_shots_per_bin': 5,
        'auto_merge_threshold': 3,
        'use_quantile_bins': False,
        'n_quantile_bins': 5,
    },
}

# ============================================================================
# ANGLE BINS (refined by shot density analysis)
# ============================================================================

ANGLE_BINS_CONFIG = {
    'bins': [
        {'range': (0, 15),           'label': '0-15°',  'quality': 'central'},
        {'range': (15, 30),          'label': '15-30°', 'quality': 'good'},
        {'range': (30, 45),          'label': '30-45°', 'quality': 'moderate'},
        {'range': (45, float('inf')), 'label': '45-60°+', 'quality': 'wide'},
    ],
    'order': ['0-15°', '15-30°', '30-45°', '45-60°+'],
    'quality_colors': {
        'central':  '#FF0000',
        'good':     '#FF8800',
        'moderate': '#FFDD00',
        'wide':     '#00CC00',
    },
    'optimization': {
        'min_shots_per_bin': 5,
        'auto_merge_threshold': 3,
        'use_quantile_bins': False,
    },
}

# ============================================================================
# COMBINED DISTANCE-ANGLE ZONES
# ============================================================================

ZONE_CONFIG = {
    'danger_zones': {
        'six_yard_box': {
            'x_min': 0.943,
            'x_max': 1.0,
            'y_min': 0.37,
            'y_max': 0.63,
            'label': '6-Yard Box',
            'color': '#FF0000',
        },
        'penalty_box_central': {
            'x_min': 0.835,
            'x_max': 0.943,
            'y_min': 0.3,
            'y_max': 0.7,
            'label': 'Central Penalty Box',
            'color': '#FF6600',
        },
        'half_spaces': {
            'x_min': 0.7,
            'x_max': 0.835,
            'y_min': 0.2,
            'y_max': 0.8,
            'label': 'Half-Spaces',
            'color': '#FFAA00',
        },
    },
    'quadrants': {
        'left':   {'y_min': 0.0,  'y_max': 0.35, 'label': 'Left'},
        'center': {'y_min': 0.35, 'y_max': 0.65, 'label': 'Center'},
        'right':  {'y_min': 0.65, 'y_max': 1.0,  'label': 'Right'},
    },
    'half_spaces': {
        'left_half':  {'y_min': 0.2,  'y_max': 0.4,  'label': 'Left Half-Space'},
        'right_half': {'y_min': 0.6,  'y_max': 0.8,  'label': 'Right Half-Space'},
    },
}

# ============================================================================
# BENCHMARK PERCENTILES
# ============================================================================

BENCHMARKS_CONFIG = {
    'conversion_rate': {
        'elite':         {'min': 15, 'max': 100,   'label': '⭐ Elite',        'color': '#FFD700'},
        'good':          {'min': 10, 'max': 15,    'label': '✅ Good',          'color': '#00CC00'},
        'average':       {'min': 5,  'max': 10,    'label': '📊 Average',       'color': '#FFAA00'},
        'below_average': {'min': 0,  'max': 5,     'label': '⬇ Below Average', 'color': '#FF4444'},
    },
    'xg_performance': {
        'elite_overperformer':    {'min': 3,   'max': float('inf'), 'label': 'Elite Overperformer'},
        'overperformer':          {'min': 1,   'max': 3,            'label': 'Overperformer'},
        'average_performer':      {'min': -1,  'max': 1,            'label': 'Average Performer'},
        'underperformer':         {'min': -3,  'max': -1,           'label': 'Underperformer'},
        'heavy_underperformer':   {'min': float('-inf'), 'max': -3, 'label': 'Heavy Underperformer'},
    },
    'distance_benchmarks': {
        '0-5m':  {'elite_conversion': 60, 'good_conversion': 40, 'avg_conversion': 25},
        '5-10m': {'elite_conversion': 35, 'good_conversion': 20, 'avg_conversion': 12},
        '10-15m': {'elite_conversion': 15, 'good_conversion': 10, 'avg_conversion': 6},
        '15-20m': {'elite_conversion': 8,  'good_conversion': 5,  'avg_conversion': 3},
        '20+m':  {'elite_conversion': 4,  'good_conversion': 2,  'avg_conversion': 1},
    },
    'minimum_shots_for_analysis': 5,
    'minimum_shots_for_percentile': 20,
}

# ============================================================================
# COLOR PALETTES FOR MULTI-PLAYER COMPARISON
# ============================================================================

COLORS_CONFIG = {
    # Shot result colors
    'shot_results': {
        'Goal':        '#FF4444',
        'MissedShots': '#FFFF44',
        'SavedShot':   '#FF9944',
        'BlockedShot': '#CCCCCC',
    },

    # Pitch colors
    'pitch': {
        'surface': '#22844e',
        'lines':   'white',
        'markings': '#FFFFFF',
    },

    # Heatmap colormaps
    'heatmaps': {
        'conversion':  'RdYlGn',
        'goals':       'YlOrRd',
        'xg':          'Blues',
        'density':     'plasma',
        'diverging':   'RdBu',
    },

    # Multi-player palette (up to 10 players)
    'players': [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#bcbd22',  # Yellow-Green
        '#17becf',  # Cyan
    ],

    # Radar chart
    'radar': {
        'background':    'rgba(255, 255, 255, 0.9)',
        'grid_color':    'rgba(128, 128, 128, 0.3)',
        'fill_opacity':  0.25,
        'line_width':    2,
    },

    # Performance badges
    'badges': {
        'elite':         '#FFD700',
        'good':          '#00CC00',
        'average':       '#FFAA00',
        'below_average': '#FF4444',
    },
}

# ============================================================================
# VISUALIZATION SETTINGS
# ============================================================================

VISUALIZATION_CONFIG = {
    'pitch': {
        'figsize':           (12, 8),
        'half_pitch_figsize': (10, 7),
        'pitch_type':        'uefa',
        'linewidth':         1.5,
        'shot_marker_size':  100,
        'goal_marker_size':  150,
        'shot_alpha':        0.6,
        'goal_alpha':        0.9,
        'edge_linewidth':    0.5,
        'edge_color':        'black',
    },
    'heatmap': {
        'figsize':     (14, 8),
        'colormap':    'YlOrRd',
        'cbar_label':  'Goals',
        'annot':       True,
        'fmt':         'd',
        'linewidths':  0.5,
    },
    'radar': {
        'figsize': (10, 10),
        'n_categories': 6,
    },
    'scatter': {
        'figsize': (12, 8),
        'alpha':   0.6,
        'size':    80,
    },
    'histogram': {
        'figsize': (12, 6),
        'bins':    20,
        'alpha':   0.7,
    },
    'comparison': {
        'figsize': (14, 6),
    },
    'trend': {
        'figsize':     (14, 6),
        'rolling_window': 5,
    },
}

# ============================================================================
# STREAMLIT DASHBOARD SETTINGS
# ============================================================================

STREAMLIT_CONFIG = {
    'page_title':            'Multi-Player Shot Analysis Dashboard',
    'page_icon':             '⚽',
    'layout':                'wide',
    'initial_sidebar_state': 'expanded',
    'tabs': [
        '📊 Overview & Comparison',
        '🔍 Player Deep-Dive',
        '🗺️ Zone Analysis',
        '📈 Trend Analysis',
        '💾 Export & Data',
    ],
    'cache_ttl':     3600,   # seconds
    'max_players_comparison': 5,
    'default_rolling_window': 5,
    'min_sample_size_toggle': True,
    'default_min_shots':      5,
}

# ============================================================================
# FEATURE ENGINEERING SETTINGS
# ============================================================================

FEATURES_CONFIG = {
    'distance': {
        'unit':            'meters',
        'pitch_length':    105,
        'pitch_width':     68,
        'max_valid_dist':  80,  # discard shots beyond this distance
        'min_valid_dist':  0.5, # discard shots impossibly close
    },
    'angle': {
        'unit':            'degrees',
        'max_valid_angle': 90,
        'min_valid_angle': 0,
    },
    'coordinates': {
        'x_min':    0.0,
        'x_max':    1.0,
        'y_min':    0.0,
        'y_max':    1.0,
        'outlier_threshold_std': 3.0,
    },
    'temporal': {
        'season_start_month': 8,  # August
        'period_bins':        [0, 15, 30, 45, 60, 75, 90, 120],
        'period_labels':      ['0-15', '15-30', '30-45', '45-60', '60-75', '75-90', '90+'],
    },
}

# ============================================================================
# DATA VALIDATION RULES
# ============================================================================

VALIDATION_CONFIG = {
    'required_columns':    ['X', 'Y', 'result', 'player'],
    'optional_columns':    ['date', 'h_team', 'a_team', 'xG', 'minute',
                            'shotType', 'situation', 'match_id', 'h_a',
                            'lastAction', 'season', 'player_id'],
    'valid_results':       {'Goal', 'MissedShots', 'SavedShot', 'BlockedShot',
                            'ShotOnPost', 'OwnGoal'},
    'valid_shot_types':    {'RightFoot', 'LeftFoot', 'Head', 'OtherBodyPart'},
    'valid_situations':    {'OpenPlay', 'FromCorner', 'DirectFreekick',
                            'SetPiece', 'Penalty'},
    'x_range':             (0.0, 1.0),
    'y_range':             (0.0, 1.0),
    'xg_range':            (0.0, 1.0),
    'minute_range':        (0, 120),
    'season_range':        (2010, 2030),
    'fill_missing_xg':     True,
    'default_xg':          0.05,
    'name_standardization': True,
}

# ============================================================================
# STATISTICAL PARAMETERS
# ============================================================================

STATISTICS_CONFIG = {
    'confidence_level':        0.95,
    'bootstrap_iterations':    1000,
    'min_sample_ci':           5,       # minimum sample for CI calculation
    'percentile_bins':         [10, 25, 50, 75, 90],
    'outlier_z_threshold':     3.0,
    'smoothing_bandwidth':     'scott', # KDE bandwidth method
    'trend_smoothing_window':  5,
    'cumulative_bins':         50,
}

# ============================================================================
# EXPORT SETTINGS
# ============================================================================

EXPORT_CONFIG = {
    'csv_delimiter':      ',',
    'date_format':        '%Y-%m-%d',
    'include_features':   True,
    'include_bins':       True,
    'float_precision':    3,
    'export_columns': [
        'player', 'date', 'h_team', 'a_team', 'result', 'xG',
        'X', 'Y', 'distance', 'angle', 'distance_bin', 'angle_bin',
        'shotType', 'situation', 'minute', 'season',
    ],
    'summary_template': {
        'player':          '',
        'total_shots':     0,
        'total_goals':     0,
        'conversion_rate': 0.0,
        'total_xg':        0.0,
        'xg_difference':   0.0,
        'avg_distance':    0.0,
        'avg_angle':       0.0,
        'export_date':     '',
    },
}

# ============================================================================
# ADVANCED ANALYSIS OPTIONS
# ============================================================================

ADVANCED_CONFIG = {
    'enable_half_space_analysis': True,
    'enable_quadrant_analysis':   True,
    'enable_pressure_context':    False,  # requires additional data
    'enable_defensive_analysis':  False,  # requires defensive data
    'enable_temporal_analysis':   True,
    'enable_home_away_split':     True,
    'enable_shot_type_analysis':  True,
    'enable_assist_analysis':     True,
    'enable_situation_analysis':  True,
    'enable_cdf_analysis':        True,
    'enable_radar_charts':        True,
    'enable_benchmarking':        True,
    'enable_confidence_intervals': True,
    'debug_mode':                 False,
    'verbose_logging':            False,
}

# ============================================================================
# RADAR CHART METRICS (6 key dimensions)
# ============================================================================

RADAR_METRICS = {
    'metrics': [
        {
            'key':   'conversion_rate',
            'label': 'Conversion\nRate',
            'scale': (0, 30),
            'higher_is_better': True,
        },
        {
            'key':   'xg_per_shot',
            'label': 'xG per\nShot',
            'scale': (0, 0.3),
            'higher_is_better': True,
        },
        {
            'key':   'xg_overperformance',
            'label': 'xG Over-\nperformance',
            'scale': (-10, 10),
            'higher_is_better': True,
        },
        {
            'key':   'penalty_box_pct',
            'label': 'Box Shot\n%',
            'scale': (0, 100),
            'higher_is_better': True,
        },
        {
            'key':   'avg_shot_quality',
            'label': 'Avg Shot\nQuality',
            'scale': (0, 1),
            'higher_is_better': True,
        },
        {
            'key':   'shot_volume',
            'label': 'Shot\nVolume',
            'scale': (0, 200),
            'higher_is_better': True,
        },
    ],
}

# ============================================================================
# SHOT TYPE LABELS
# ============================================================================

SHOT_TYPE_LABELS = {
    'RightFoot':     '🦶 Right Foot',
    'LeftFoot':      '🦵 Left Foot',
    'Head':          '🗣️ Header',
    'OtherBodyPart': '🤸 Other',
}

SITUATION_LABELS = {
    'OpenPlay':        '⚽ Open Play',
    'FromCorner':      '🏃 Corner',
    'DirectFreekick':  '🎯 Free Kick',
    'SetPiece':        '📌 Set Piece',
    'Penalty':         '🥅 Penalty',
}

RESULT_LABELS = {
    'Goal':        '⚽ Goal',
    'MissedShots': '❌ Missed',
    'SavedShot':   '🧤 Saved',
    'BlockedShot': '🛡️ Blocked',
}

# ============================================================================
# COMPLETE CONFIGURATION DICTIONARY
# ============================================================================

MULTI_CONFIG = {
    'DATA':          DATA_CONFIG,
    'DISTANCE_BINS': DISTANCE_BINS_CONFIG,
    'ANGLE_BINS':    ANGLE_BINS_CONFIG,
    'ZONES':         ZONE_CONFIG,
    'BENCHMARKS':    BENCHMARKS_CONFIG,
    'COLORS':        COLORS_CONFIG,
    'VISUALIZATION': VISUALIZATION_CONFIG,
    'STREAMLIT':     STREAMLIT_CONFIG,
    'FEATURES':      FEATURES_CONFIG,
    'VALIDATION':    VALIDATION_CONFIG,
    'STATISTICS':    STATISTICS_CONFIG,
    'EXPORT':        EXPORT_CONFIG,
    'ADVANCED':      ADVANCED_CONFIG,
    'RADAR':         RADAR_METRICS,
    'LABELS': {
        'SHOT_TYPES': SHOT_TYPE_LABELS,
        'SITUATIONS': SITUATION_LABELS,
        'RESULTS':    RESULT_LABELS,
    },
}


# ============================================================================
# CONFIGURATION ACCESS FUNCTIONS
# ============================================================================

def get_multi_player_config() -> dict:
    """
    Return the complete multi-player configuration dictionary.

    Returns
    -------
    dict
        Full configuration with all sections.
    """
    return MULTI_CONFIG


def get_distance_bin_labels() -> list:
    """Return ordered list of distance bin labels."""
    return DISTANCE_BINS_CONFIG['order']


def get_angle_bin_labels() -> list:
    """Return ordered list of angle bin labels."""
    return ANGLE_BINS_CONFIG['order']


def get_player_color(index: int) -> str:
    """
    Return a color for the player at the given index.

    Parameters
    ----------
    index : int
        Zero-based player index.

    Returns
    -------
    str
        Hex color string.
    """
    palette = COLORS_CONFIG['players']
    return palette[index % len(palette)]


def validate_multi_config() -> bool:
    """
    Validate the multi-player configuration for consistency.

    Returns
    -------
    bool
        True if configuration is valid.
    """
    valid = True

    # Check distance bins
    if len(DISTANCE_BINS_CONFIG['bins']) != len(DISTANCE_BINS_CONFIG['order']):
        print("ERROR: Distance bins and order length mismatch")
        valid = False

    # Check angle bins
    if len(ANGLE_BINS_CONFIG['bins']) != len(ANGLE_BINS_CONFIG['order']):
        print("ERROR: Angle bins and order length mismatch")
        valid = False

    # Check player colors
    if len(COLORS_CONFIG['players']) < 2:
        print("WARNING: At least 2 player colors recommended")

    # Check radar metrics
    if len(RADAR_METRICS['metrics']) < 3:
        print("WARNING: At least 3 radar metrics recommended")

    if valid:
        print("✅ Multi-player configuration is valid")
    return valid


if __name__ == '__main__':
    validate_multi_config()
    config = get_multi_player_config()
    print(f"✅ Loaded {len(config)} configuration sections")
    print(f"   Distance bins: {get_distance_bin_labels()}")
    print(f"   Angle bins:    {get_angle_bin_labels()}")
    print(f"   Player colors: {len(COLORS_CONFIG['players'])} defined")
