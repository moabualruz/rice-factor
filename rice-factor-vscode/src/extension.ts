/**
 * Rice-Factor VS Code Extension
 *
 * Provides artifact viewing, diff preview, and approval actions
 * for the Rice-Factor LLM-Assisted Development System.
 */

import * as vscode from 'vscode';
import { ArtifactTreeProvider } from './artifactViewer';
import { WorkflowTreeProvider } from './workflowView';
import { DiffPreviewProvider } from './diffPreview';
import { ApprovalService } from './approvalService';

let artifactTreeProvider: ArtifactTreeProvider;
let workflowTreeProvider: WorkflowTreeProvider;
let diffPreviewProvider: DiffPreviewProvider;
let approvalService: ApprovalService;

/**
 * Activates the extension.
 *
 * @param context - The extension context.
 */
export function activate(context: vscode.ExtensionContext): void {
    console.log('Rice-Factor extension activating...');

    // Initialize providers
    artifactTreeProvider = new ArtifactTreeProvider();
    workflowTreeProvider = new WorkflowTreeProvider();
    diffPreviewProvider = new DiffPreviewProvider(context);
    approvalService = new ApprovalService();

    // Register tree views
    const artifactTreeView = vscode.window.createTreeView('riceFactorArtifacts', {
        treeDataProvider: artifactTreeProvider,
        showCollapseAll: true
    });

    const workflowTreeView = vscode.window.createTreeView('riceFactorWorkflow', {
        treeDataProvider: workflowTreeProvider
    });

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('riceFactor.refreshArtifacts', () => {
            artifactTreeProvider.refresh();
            workflowTreeProvider.refresh();
            vscode.window.showInformationMessage('Rice-Factor: Artifacts refreshed');
        }),

        vscode.commands.registerCommand('riceFactor.approveArtifact', async (item: ArtifactItem) => {
            if (item) {
                const result = await approvalService.approveArtifact(item.artifactId);
                if (result) {
                    artifactTreeProvider.refresh();
                    vscode.window.showInformationMessage(`Artifact ${item.label} approved`);
                }
            }
        }),

        vscode.commands.registerCommand('riceFactor.viewDiff', async (item: ArtifactItem) => {
            if (item) {
                await diffPreviewProvider.showDiff(item.artifactId);
            }
        }),

        vscode.commands.registerCommand('riceFactor.applyDiff', async (item: ArtifactItem) => {
            if (item) {
                const result = await approvalService.applyDiff(item.artifactId);
                if (result) {
                    artifactTreeProvider.refresh();
                    vscode.window.showInformationMessage(`Diff applied for ${item.label}`);
                }
            }
        }),

        artifactTreeView,
        workflowTreeView
    );

    // Watch for artifact changes
    const artifactsWatcher = vscode.workspace.createFileSystemWatcher('**/artifacts/**/*.json');
    artifactsWatcher.onDidChange(() => artifactTreeProvider.refresh());
    artifactsWatcher.onDidCreate(() => artifactTreeProvider.refresh());
    artifactsWatcher.onDidDelete(() => artifactTreeProvider.refresh());
    context.subscriptions.push(artifactsWatcher);

    console.log('Rice-Factor extension activated');
}

/**
 * Deactivates the extension.
 */
export function deactivate(): void {
    console.log('Rice-Factor extension deactivated');
}

/**
 * Represents an artifact item in the tree view.
 */
export interface ArtifactItem extends vscode.TreeItem {
    artifactId: string;
    artifactType: string;
    status: string;
}
