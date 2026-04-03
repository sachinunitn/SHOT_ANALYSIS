"""
Setup Validation Script
=======================

Run this script BEFORE running the Streamlit app to verify all dependencies
and data are correctly configured.

Usage:
    python validate_setup.py
"""

import sys
import os
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def print_success(text):
    """Print success message."""
    print(f"✅ {text}")


def print_error(text):
    """Print error message."""
    print(f"❌ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"⚠️  {text}")


def check_python_version():
    """Check Python version."""
    print_header("1. PYTHON VERSION")
    
    version = sys.version_info
    required_version = (3, 7)
    
    if version >= required_version:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} found, need 3.7+")
        return False


def check_modules():
    """Check all required modules."""
    print_header("2. REQUIRED MODULES")
    
    required_modules = {
        'pandas': 'Data manipulation',
        'numpy': 'Numerical computing',
        'matplotlib': 'Visualization backend',
        'streamlit': 'Web app framework',
        'mplsoccer': 'Football pitch visualization',
        'scipy': 'Scientific computing',
    }
    
    all_installed = True
    
    for module_name, description in required_modules.items():
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'version unknown')
            print_success(f"{module_name:15} {version:15} ({description})")
        except ImportError:
            print_error(f"{module_name:15} NOT INSTALLED - {description}")
            all_installed = False
    
    return all_installed


def check_data_file():
    """Check for Understat data file."""
    print_header("3. DATA FILE")
    
    data_file = 'erling_haaland_2022_understat.csv'
    
    if os.path.exists(data_file):
        size_mb = os.path.getsize(data_file) / (1024 * 1024)
        print_success(f"Found: {data_file} ({size_mb:.2f} MB)")
        
        # Try to read and validate
        try:
            import pandas as pd
            df = pd.read_csv(data_file)
            print_success(f"File readable: {len(df)} rows, {len(df.columns)} columns")
            
            # Check required columns
            required_cols = ['X', 'Y', 'result', 'player', 'match_id']
            missing = [col for col in required_cols if col not in df.columns]
            
            if missing:
                print_warning(f"Missing columns: {', '.join(missing)}")
                return False
            else:
                print_success(f"All required columns present")
                
                # Data validation
                print("\n  Data Quality Check:")
                print(f"    - Shots: {len(df)}")
                print(f"    - Players: {df['player'].nunique()}")
                print(f"    - Matches: {df['match_id'].nunique()}")
                print(f"    - X range: {df['X'].min():.3f} - {df['X'].max():.3f}")
                print(f"    - Y range: {df['Y'].min():.3f} - {df['Y'].max():.3f}")
                print(f"    - Shot results: {df['result'].nunique()}")
                
                return True
        
        except Exception as e:
            print_error(f"Error reading file: {e}")
            return False
    else:
        print_error(f"Data file not found: {data_file}")
        print_warning(f"Place '{data_file}' in the same directory as shot_analysis_app.py")
        return False


def check_script_files():
    """Check for required script files."""
    print_header("4. SCRIPT FILES")
    
    required_files = {
        'shot_analysis_app.py': 'Main Streamlit application',
        'requirements.txt': 'Python dependencies',
        'utils.py': 'Utility functions',
        'README.md': 'Documentation',
        'QUICKSTART.md': 'Quick start guide',
    }
    
    all_present = True
    
    for filename, description in required_files.items():
        if os.path.exists(filename):
            size_kb = os.path.getsize(filename) / 1024
            print_success(f"{filename:25} ({description}) - {size_kb:.1f} KB")
        else:
            print_warning(f"{filename:25} NOT FOUND - {description}")
            all_present = all_present and (filename in ['utils.py'])  # Make utils optional
    
    return all_present


def validate_imports():
    """Test actual imports used in the app."""
    print_header("5. IMPORT VALIDATION")
    
    try:
        import pandas as pd
        print_success("pandas imported successfully")
    except Exception as e:
        print_error(f"Failed to import pandas: {e}")
        return False
    
    try:
        import numpy as np
        print_success("numpy imported successfully")
    except Exception as e:
        print_error(f"Failed to import numpy: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        print_success("matplotlib imported successfully")
    except Exception as e:
        print_error(f"Failed to import matplotlib: {e}")
        return False
    
    try:
        from mplsoccer import Pitch
        print_success("mplsoccer imported successfully")
    except Exception as e:
        print_error(f"Failed to import mplsoccer: {e}")
        return False
    
    try:
        import streamlit as st
        print_success("streamlit imported successfully")
    except Exception as e:
        print_error(f"Failed to import streamlit: {e}")
        return False
    
    try:
        import scipy
        print_success("scipy imported successfully")
    except Exception as e:
        print_error(f"Failed to import scipy: {e}")
        return False
    
    return True


def test_data_processing():
    """Test basic data processing."""
    print_header("6. DATA PROCESSING TEST")
    
    try:
        import pandas as pd
        import numpy as np
        
        # Load data
        df = pd.read_csv('erling_haaland_2022_understat.csv')
        print_success("Data loaded successfully")
        
        # Test distance calculation
        def calc_distance(x, y):
            x_m = x * 105
            y_m = y * 68
            return np.sqrt((x_m - 105)**2 + (y_m - 34)**2)
        
        distances = df[['X', 'Y']].apply(lambda row: calc_distance(row['X'], row['Y']), axis=1)
        print_success(f"Distance calculation works - Range: {distances.min():.1f}m - {distances.max():.1f}m")
        
        # Test angle calculation
        def calc_angle(x, y):
            x_m = x * 105
            y_m = y * 68
            dist_to_goal = (1 - x) * 105
            angle = np.degrees(np.arctan(np.abs(y_m - 34) / (dist_to_goal + 1e-6)))
            return angle
        
        angles = df[['X', 'Y']].apply(lambda row: calc_angle(row['X'], row['Y']), axis=1)
        print_success(f"Angle calculation works - Range: {angles.min():.1f}° - {angles.max():.1f}°")
        
        # Test binning
        def bin_distance(distance):
            if distance < 6:
                return '0-6m'
            elif distance < 12:
                return '6-12m'
            elif distance < 18:
                return '12-18m'
            elif distance < 24:
                return '18-24m'
            else:
                return '24+m'
        
        bins = distances.apply(bin_distance)
        print_success(f"Binning works - Distribution: {bins.value_counts().to_dict()}")
        
        return True
    
    except Exception as e:
        print_error(f"Data processing test failed: {e}")
        return False


def print_summary(checks):
    """Print summary of all checks."""
    print_header("VALIDATION SUMMARY")
    
    passed = sum(checks.values())
    total = len(checks)
    
    print(f"\nResults: {passed}/{total} checks passed\n")
    
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
    
    print()
    
    if all(checks.values()):
        print_success("ALL CHECKS PASSED!")
        print("\nYou're ready to run:")
        print("  streamlit run shot_analysis_app.py")
        return True
    else:
        print_error("SOME CHECKS FAILED")
        print("\nPlease fix the issues above before running the app.")
        print("\nCommon fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Ensure CSV file is in the same directory")
        print("  3. Check Python version: python --version")
        return False


def main():
    """Run all validation checks."""
    print("\n" + "="*60)
    print("  SHOT ANALYSIS DASHBOARD - SETUP VALIDATION")
    print("="*60)
    
    checks = {}
    
    # Run all checks
    checks['Python Version'] = check_python_version()
    checks['Required Modules'] = check_modules()
    checks['Data File'] = check_data_file()
    checks['Script Files'] = check_script_files()
    checks['Import Validation'] = validate_imports()
    checks['Data Processing'] = test_data_processing()
    
    # Print summary
    success = print_summary(checks)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
