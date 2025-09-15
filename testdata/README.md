# Test Data Directory

## Purpose
This directory contains **only essential test cases** that users can immediately understand and connect with.

## Contents

### 🎯 Primary Test Data (For User Demos)
- **streamlined_scenarios/** - 4 essential scenarios (31 files total)
  - Family burst mode photography (8 photos → 2 keepers)
  - Celebrity photo variations (6 sources → 1 best + AI flagged)
  - Travel landmark attempts (5 shots → 2 different times)
  - AI enhancement detection (4 photos → 3 flagged)

### 🔧 Functional Test Data (For Development)
- **test1_basic_duplicates/** - Simple exact duplicate detection
- **test2_smart_duplicates/** - Smart duplicate detection with variations
- **test3_mixed_files/** - Multiple file types (images, videos, documents)
- **test4_large_collection/** - Performance testing with larger dataset

## Quick Start
1. **For user demos**: Use `streamlined_scenarios/`
2. **For development**: Use `test1-4/` directories
3. **Total review time**: 5-10 minutes (streamlined) + 10 minutes (functional)

## Removed Directories
The following synthetic data directories were removed for being overwhelming/not user-relatable:
- ai_enhancement_detection (254 files)
- birthday_party_event (168 files)
- enhanced_family_beach_day (82 files)
- family_beach_day (127 files)
- paris_vacation (89 files)
- smartphone_burst_modes (286 files)

**Total removed**: 946+ synthetic files that required technical knowledge to interpret.
