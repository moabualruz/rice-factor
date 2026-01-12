# Web Interface Workflows

Learn how to perform common tasks using the Web UI.

## Workflow 1: Approving a Project Plan

1.  Run `rice-factor plan project` in your terminal (or trigger it via the UI if configured).
2.  Open the Web Interface and navigate to **Artifacts**.
3.  Locate the new `ProjectPlan` (it will be in `DRAFT` status).
4.  Click to open it.
5.  Review the JSON content to ensure requirements are met.
6.  Click the **Approve** button in the top right.
7.  The status changes to `APPROVED`, unlocking the next steps (like Scaffolding).

## Workflow 2: Reviewing Implementation Code

1.  After running `rice-factor impl ...`, a diff is generated.
2.  Navigate to **Diffs** in the sidebar.
3.  Select the pending diff.
4.  Use the split view to compare the changes.
5.  If the code looks correct and meets the `ImplementationPlan`:
    - Click **Approve**.
    - Click **Apply** to write the changes to disk.
6.  If there are issues:
    - Click **Reject**.
    - The task is sent back to the planning queue (or you can manually intervene).

## Workflow 3: Monitoring Progress

1.  Keep the **Dashboard** open on a second monitor.
2.  The **Activity Feed** updates in real-time as the CLI or Agents perform work.
3.  Use this to track long-running multi-agent tasks or batch operations.
