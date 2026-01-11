# F18-04: Batch Operations - Tasks

## Tasks
### T18-04-01: Create BatchProcessor Service
- [ ] Define BatchOperation model (operation_type, artifact_ids, options)
- [ ] Implement BatchProcessor with transaction support
- [ ] Add rollback capability on partial failures

### T18-04-02: Implement Batch Approval
- [ ] Approve multiple artifacts in single operation
- [ ] Validate all artifacts before approving any
- [ ] Generate batch approval audit entry

### T18-04-03: Implement Batch Rejection
- [ ] Reject multiple artifacts with shared reason
- [ ] Support individual rejection reasons
- [ ] Generate batch rejection audit entry

### T18-04-04: Implement Orchestrator Component (GAP-SPEC-005)
- [ ] Create LifecycleOrchestrator service
- [ ] Drive lifecycle phases programmatically (plan → approve → execute)
- [ ] Support phase-driven batch execution
- [ ] Implement phase transition hooks
- [ ] Add orchestrator state persistence for resume

### T18-04-05: Add CLI Batch Commands
- [ ] `rice-factor batch approve <pattern>` command
- [ ] `rice-factor batch reject <pattern>` command
- [ ] `rice-factor orchestrate <phase>` command
- [ ] Progress reporting for batch operations

### T18-04-06: Unit Tests
- [ ] Test BatchProcessor with multiple artifacts
- [ ] Test rollback on partial failures
- [ ] Test LifecycleOrchestrator state transitions
- [ ] Test CLI batch commands

## Estimated Test Count: ~10

## Implementation Notes

### Orchestrator Phases
```
Phase 0: Init (questionnaire, context)
Phase 1: Plan (generate ProjectPlan, ArchitecturePlan)
Phase 2: Scaffold (generate ScaffoldPlan, create files)
Phase 3: Test (generate TestPlan, lock)
Phase 4: Implement (generate ImplementationPlans)
Phase 5: Execute (apply diffs)
Phase 6: Validate (run tests, lint)
Phase 7: Refactor (optional)
```

### References
- GAP-SPEC-005: Orchestrator component for lifecycle phases
- Spec reference: 03 3.1 (Artifact Builder design)
