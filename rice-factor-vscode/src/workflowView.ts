/**
 * Workflow Tree View Provider
 *
 * Provides a tree view of workflow steps in the sidebar.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Workflow step definition.
 */
interface WorkflowStep {
    id: string;
    name: string;
    description: string;
    status: 'pending' | 'current' | 'complete';
}

/**
 * Tree data provider for workflow steps.
 */
export class WorkflowTreeProvider implements vscode.TreeDataProvider<WorkflowStepItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<WorkflowStepItem | undefined | null | void> =
        new vscode.EventEmitter<WorkflowStepItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<WorkflowStepItem | undefined | null | void> =
        this._onDidChangeTreeData.event;

    private steps: WorkflowStep[] = [
        { id: 'init', name: 'Initialize', description: 'Create .project/', status: 'pending' },
        { id: 'plan-project', name: 'Plan Project', description: 'Generate ProjectPlan', status: 'pending' },
        { id: 'scaffold', name: 'Scaffold', description: 'Create structure', status: 'pending' },
        { id: 'plan-tests', name: 'Plan Tests', description: 'Generate TestPlan', status: 'pending' },
        { id: 'lock-tests', name: 'Lock Tests', description: 'Lock TestPlan', status: 'pending' },
        { id: 'plan-impl', name: 'Plan Implementation', description: 'Generate ImplPlan', status: 'pending' },
        { id: 'implement', name: 'Implement', description: 'Generate code', status: 'pending' },
        { id: 'apply', name: 'Apply', description: 'Apply changes', status: 'pending' },
        { id: 'test', name: 'Test', description: 'Run tests', status: 'pending' },
    ];

    /**
     * Creates an instance of WorkflowTreeProvider.
     */
    constructor() {
        this.detectPhase();
    }

    /**
     * Refreshes the tree view.
     */
    refresh(): void {
        this.detectPhase();
        this._onDidChangeTreeData.fire();
    }

    /**
     * Gets tree item for display.
     */
    getTreeItem(element: WorkflowStepItem): vscode.TreeItem {
        return element;
    }

    /**
     * Gets children (workflow steps).
     */
    getChildren(): Thenable<WorkflowStepItem[]> {
        return Promise.resolve(
            this.steps.map(step => {
                const item = new WorkflowStepItem(
                    step.name,
                    step.id,
                    step.status,
                    vscode.TreeItemCollapsibleState.None
                );
                item.description = step.description;
                item.tooltip = `${step.name}: ${step.description}`;
                return item;
            })
        );
    }

    /**
     * Detects the current workflow phase based on project state.
     */
    private detectPhase(): void {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            return;
        }

        const rootPath = workspaceFolders[0].uri.fsPath;
        const projectPath = path.join(rootPath, '.project');
        const artifactsPath = path.join(rootPath, 'artifacts');

        // Reset all to pending
        this.steps.forEach(step => step.status = 'pending');

        // Check project initialization
        if (!fs.existsSync(projectPath)) {
            this.steps[0].status = 'current';
            return;
        }
        this.steps[0].status = 'complete';

        // Check for artifacts
        if (!fs.existsSync(artifactsPath)) {
            this.steps[1].status = 'current';
            return;
        }

        // Check for ProjectPlan
        const projectPlanPath = path.join(artifactsPath, 'project_plan');
        if (fs.existsSync(projectPlanPath) && this.hasApprovedArtifact(projectPlanPath)) {
            this.steps[1].status = 'complete';
        } else {
            this.steps[1].status = 'current';
            return;
        }

        // Check for ScaffoldPlan
        const scaffoldPlanPath = path.join(artifactsPath, 'scaffold_plan');
        if (fs.existsSync(scaffoldPlanPath) && this.hasApprovedArtifact(scaffoldPlanPath)) {
            this.steps[2].status = 'complete';
        } else {
            this.steps[2].status = 'current';
            return;
        }

        // Check for TestPlan
        const testPlanPath = path.join(artifactsPath, 'test_plan');
        if (fs.existsSync(testPlanPath)) {
            if (this.hasLockedArtifact(testPlanPath)) {
                this.steps[3].status = 'complete';
                this.steps[4].status = 'complete';
            } else if (this.hasApprovedArtifact(testPlanPath)) {
                this.steps[3].status = 'complete';
                this.steps[4].status = 'current';
                return;
            } else {
                this.steps[3].status = 'current';
                return;
            }
        } else {
            this.steps[3].status = 'current';
            return;
        }

        // Implementation phase
        this.steps[5].status = 'current';
    }

    /**
     * Checks if a directory has an approved artifact.
     */
    private hasApprovedArtifact(dirPath: string): boolean {
        try {
            const files = fs.readdirSync(dirPath).filter(f => f.endsWith('.json'));
            for (const file of files) {
                const content = fs.readFileSync(path.join(dirPath, file), 'utf-8');
                const artifact = JSON.parse(content);
                if (artifact.status === 'APPROVED' || artifact.status === 'LOCKED') {
                    return true;
                }
            }
        } catch {
            // Ignore errors
        }
        return false;
    }

    /**
     * Checks if a directory has a locked artifact.
     */
    private hasLockedArtifact(dirPath: string): boolean {
        try {
            const files = fs.readdirSync(dirPath).filter(f => f.endsWith('.json'));
            for (const file of files) {
                const content = fs.readFileSync(path.join(dirPath, file), 'utf-8');
                const artifact = JSON.parse(content);
                if (artifact.status === 'LOCKED') {
                    return true;
                }
            }
        } catch {
            // Ignore errors
        }
        return false;
    }
}

/**
 * Represents a workflow step in the tree view.
 */
export class WorkflowStepItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly stepId: string,
        public readonly status: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.iconPath = new vscode.ThemeIcon(this.getIconName());
    }

    private getIconName(): string {
        switch (this.status) {
            case 'complete':
                return 'pass';
            case 'current':
                return 'arrow-right';
            default:
                return 'circle-outline';
        }
    }
}
