# F14-07: Capability Auto-Detection - Tasks

---

## Tasks

### T14-07-01: Create CapabilityDetector Class
- [x] Files: `rice_factor/adapters/refactoring/capability_detector.py`
- [x] Created `CapabilityDetector` class with caching
- [x] Created `ToolAvailability` and `LanguageCapability` dataclasses

### T14-07-02: Implement Python Package Detection
- [x] Files: `rice_factor/adapters/refactoring/capability_detector.py`
- [x] Implemented `_check_python_package()` using `importlib.metadata`
- [x] Added `_detect_rope()` for Python Rope detection

### T14-07-03: Implement CLI Tool Detection
- [x] Files: `rice_factor/adapters/refactoring/capability_detector.py`
- [x] Implemented `_check_command()` using `shutil.which`
- [x] Implemented `_check_command_version()` for version extraction
- [x] Added detection for: gopls, rust-analyzer, dotnet

### T14-07-04: Implement Ruby Gem Detection
- [x] Files: `rice_factor/adapters/refactoring/capability_detector.py`
- [x] Implemented `_check_ruby_gem()` using `gem list`
- [x] Added `_detect_ruby_parser()` method

### T14-07-05: Implement PHP/Composer Detection
- [x] Files: `rice_factor/adapters/refactoring/capability_detector.py`
- [x] Implemented `_check_php_package()` using `composer show`
- [x] Added `_detect_rector()` method

### T14-07-06: Implement npm Package Detection
- [x] Files: `rice_factor/adapters/refactoring/capability_detector.py`
- [x] Implemented `_check_npm_package()` using `npm list -g`
- [x] Added `_detect_jscodeshift()` method
- [x] Updated jscodeshift operations to include `extract_interface` and `enforce_dependency`

### T14-07-07: Add CLI Command `rice-factor capabilities`
- [x] Files: `rice_factor/entrypoints/cli/commands/capabilities.py`
- [x] Created `capabilities` command with options:
  - `--refresh` / `-r`: Refresh cached detection
  - `--tools` / `-t`: Show only tools table
  - `--languages` / `-l`: Show only languages table
  - `--json` / `-j`: JSON output format
- [x] Added to main CLI in `rice_factor/entrypoints/cli/main.py`

### T14-07-08: Unit Tests for Capability Detector
- [x] Files: `tests/unit/adapters/refactoring/test_capability_detector.py`
- [x] 25 tests for CapabilityDetector class (pre-existing)
- [x] Files: `tests/unit/entrypoints/cli/commands/test_capabilities.py`
- [x] 8 tests for capabilities CLI command (new)

---

## Actual Test Count: 8 new tests (33 total for capability detection)

## Test Baseline: 2643 → 2651 tests

---

## Summary

Completed F14-07: Capability Auto-Detection:
- **CapabilityDetector**: Comprehensive detection for 8 refactoring tools
- **CLI Command**: `rice-factor capabilities` with table and JSON output
- **Detection methods**: Python packages, CLI tools, Ruby gems, PHP/Composer, npm
- **Language mapping**: 12 languages mapped to their adapters
- **Operations tracking**: rename, move, extract_interface, enforce_dependency
