# Feature: F07-08 Integration Tests

## Status: Pending

## Description

Create a comprehensive end-to-end integration test suite that validates all MVP exit criteria (EC-001 through EC-007). Tests cover the complete happy path workflow from init to refactor, as well as all safety violation scenarios.

## Requirements Reference

- EC-001 through EC-007: MVP Exit Criteria
- M07-S-001 through M07-S-005: Safety Requirements
- raw/Phase-01-mvp.md: Section 11 (exit criteria)
- raw/Item-01-mvp-example-walkthrough-end-to-end.md: Complete walkthrough
- design.md: Section 7 (Testing Strategy)

## Tasks

### Test Fixtures
- [ ] Create `tests/integration/conftest.py`
  - [ ] `mvp_project` fixture - minimal project structure
  - [ ] `mock_llm` fixture - mock LLM responses
  - [ ] `temp_repo` fixture - git-enabled temp directory
  - [ ] `approved_project_plan` fixture
  - [ ] `locked_test_plan` fixture

### Happy Path Tests
- [ ] Create `tests/integration/test_e2e_workflow.py`
  - [ ] `test_e2e_init_creates_structure` (EC-001)
  - [ ] `test_e2e_init_to_scaffold` (EC-002)
  - [ ] `test_e2e_test_lock` (EC-003)
  - [ ] `test_e2e_implementation_cycle` (EC-004)
  - [ ] `test_e2e_refactor_dry_run` (EC-005)
  - [ ] `test_e2e_no_manual_cleanup` (EC-006)
  - [ ] `test_e2e_full_workflow` (all criteria)

### Audit Trail Tests
- [ ] Create `tests/integration/test_audit_trail.py`
  - [ ] `test_audit_trail_init` (EC-007)
  - [ ] `test_audit_trail_plan`
  - [ ] `test_audit_trail_scaffold`
  - [ ] `test_audit_trail_lock`
  - [ ] `test_audit_trail_impl`
  - [ ] `test_audit_trail_apply`
  - [ ] `test_audit_trail_test`
  - [ ] `test_audit_trail_complete`

### Safety Violation Tests
- [ ] Create `tests/integration/test_safety_violations.py`
  - [ ] `test_fail_on_test_modification` (M07-E-001)
  - [ ] `test_fail_on_missing_artifact` (M07-E-002)
  - [ ] `test_fail_on_invalid_json` (M07-E-003)
  - [ ] `test_fail_on_unauthorized_diff` (M07-E-004)
  - [ ] `test_fail_on_schema_violation` (M07-E-005)
  - [ ] `test_fail_on_wrong_phase`

### Phase Transition Tests
- [ ] Create `tests/integration/test_phase_transitions.py`
  - [ ] `test_phase_uninit_to_init`
  - [ ] `test_phase_init_to_planning`
  - [ ] `test_phase_planning_to_scaffolded`
  - [ ] `test_phase_scaffolded_to_test_locked`
  - [ ] `test_phase_blocks_invalid_transitions`

### LLM Integration Tests
- [ ] Create `tests/integration/test_llm_integration.py`
  - [ ] `test_llm_generates_project_plan`
  - [ ] `test_llm_generates_scaffold_plan`
  - [ ] `test_llm_generates_test_plan`
  - [ ] `test_llm_generates_implementation_plan`
  - [ ] `test_llm_generates_diff`
  - [ ] `test_llm_generates_refactor_plan`

### Error Recovery Tests
- [ ] Create `tests/integration/test_error_recovery.py`
  - [ ] `test_recovery_guidance_displayed`
  - [ ] `test_resume_suggests_next_action`
  - [ ] `test_override_allows_manual_fix`

### Test Runner Integration
- [ ] Add pytest markers for integration tests
  - [ ] `@pytest.mark.integration` marker
  - [ ] `@pytest.mark.e2e` marker for full workflow
  - [ ] `@pytest.mark.slow` marker for long tests
  - [ ] Configure pytest.ini for marker handling

### CI Integration
- [ ] Add integration test configuration
  - [ ] Separate integration tests from unit tests
  - [ ] Configure test timeout for E2E tests
  - [ ] Add test coverage reporting

## Acceptance Criteria

- [ ] All 7 exit criteria (EC-001 through EC-007) have passing tests
- [ ] All 5 safety violation scenarios have tests
- [ ] Audit trail completeness is verified
- [ ] Phase transitions are tested
- [ ] Error recovery guidance is tested
- [ ] Tests can run in CI environment
- [ ] Test coverage > 80% for integration paths
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `tests/integration/conftest.py` | CREATE | Test fixtures |
| `tests/integration/test_e2e_workflow.py` | CREATE | Happy path E2E tests |
| `tests/integration/test_audit_trail.py` | CREATE | Audit trail tests |
| `tests/integration/test_safety_violations.py` | CREATE | Safety violation tests |
| `tests/integration/test_phase_transitions.py` | CREATE | Phase transition tests |
| `tests/integration/test_llm_integration.py` | CREATE | LLM integration tests |
| `tests/integration/test_error_recovery.py` | CREATE | Error recovery tests |
| `pytest.ini` | UPDATE | Add integration test markers |

## Dependencies

- F07-01 through F07-07: All features must be implemented

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
