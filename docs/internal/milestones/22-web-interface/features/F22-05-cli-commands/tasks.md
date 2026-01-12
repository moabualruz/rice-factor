# F22-05: CLI Commands - Tasks

## Overview
Add CLI commands for starting the web server and building the frontend.

## Tasks

### T22-05-01: Create web command module
- [x] Create `rice_factor/entrypoints/cli/commands/web.py`
- [x] Add Typer app with help text
- [x] Register in main CLI

### T22-05-02: Implement serve command
- [x] Add `serve` command with port/host options
- [x] Integrate uvicorn for server startup
- [x] Add --reload flag for development
- [x] Handle missing web dependencies gracefully

### T22-05-03: Implement build command
- [x] Add `build` command
- [x] Locate frontend directory
- [x] Run npm build subprocess
- [x] Add --outdir option for custom output

### T22-05-04: Add dependency checks
- [x] Check for uvicorn availability
- [x] Check for npm/node availability for build
- [x] Provide helpful error messages

### T22-05-05: Write tests
- [x] Test serve command registration
- [x] Test build command registration
- [x] Test missing dependency handling
- [x] Test option parsing

## Estimated Test Count: ~8 (Actual: 11)

## Status: COMPLETE
