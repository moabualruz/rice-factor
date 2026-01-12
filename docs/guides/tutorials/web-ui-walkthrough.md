# Web UI Walkthrough

This tutorial guides you through a complete development cycle using the Rice-Factor Web Interface alongside the CLI.

## Prerequisites

- Rice-Factor installed
- A project initialized (`rice-factor init`)

## Step 1: Start the Server

```bash
cd my-project
rice-factor web serve
```

Open your browser to `http://127.0.0.1:8000`.

## Step 2: Explore the Dashboard

You should see your project name and the current phase (likely `PLANNING` or `INIT`). The activity feed will show the `init` command you just ran.

## Step 3: Generate a Plan via CLI

Keep the server running. In a new terminal:

```bash
rice-factor plan project
```

Watch the Web UI Dashboard. You will see a new activity entry appear instantly: "Generated ProjectPlan".

## Step 4: Approve via Web UI

1.  Click **Approvals** or **Artifacts** in the sidebar.
2.  You will see the new `ProjectPlan` waiting for approval.
3.  Click it to review the details.
4.  Click **Approve**.

Go back to your terminal. If you try to run `rice-factor scaffold`, it will now succeed because the plan is approved.

## Step 5: Test Locking

1.  Generate a test plan: `rice-factor plan tests`.
2.  In the Web UI, find the `TestPlan`.
3.  Approve it.
4.  You will now see a **LOCK** button.
5.  Click **LOCK**. A confirmation modal appears. Confirm it.
6.  The artifact is now immutable.

## Conclusion

The Web Interface enables a hybrid workflow: use the CLI for heavy execution and the Web UI for high-bandwidth review and approval.
