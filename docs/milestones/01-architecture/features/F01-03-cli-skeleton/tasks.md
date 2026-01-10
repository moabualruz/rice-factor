# Feature: F01-03 CLI Skeleton

## Status: Pending

## Description
Create the basic CLI structure using Typer with placeholder commands.

## Tasks
- [ ] Create `rice_factor/entrypoints/cli/main.py` with Typer app
- [ ] Create placeholder command files in `commands/`:
  - [ ] `init.py` - rice-factor init
  - [ ] `plan.py` - rice-factor plan <type>
  - [ ] `scaffold.py` - rice-factor scaffold
  - [ ] `impl.py` - rice-factor impl <file>
  - [ ] `apply.py` - rice-factor apply
  - [ ] `test.py` - rice-factor test
  - [ ] `approve.py` - rice-factor approve <artifact>
  - [ ] `lock.py` - rice-factor lock <artifact>
  - [ ] `refactor.py` - rice-factor refactor <goal>
  - [ ] `validate.py` - rice-factor validate
  - [ ] `resume.py` - rice-factor resume
- [ ] Wire all commands to main app
- [ ] Add `--help` documentation for each command
- [ ] Add `--version` flag to main app
- [ ] Add `--dry-run` flag where applicable

## Acceptance Criteria
- `rice-factor --help` shows all commands
- Each command responds to `--help`
- Commands print "Not implemented" placeholder messages

## Progress Log
| Date | Update |
|------|--------|
| 2026-01-10 | Created task file |
