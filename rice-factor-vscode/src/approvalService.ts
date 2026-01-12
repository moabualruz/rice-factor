/**
 * Approval Service
 *
 * Handles artifact approval and diff application by calling
 * the rice-factor CLI.
 */

import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * Service for artifact approval and diff application.
 */
export class ApprovalService {
    /**
     * Approves an artifact using the rice-factor CLI.
     *
     * @param artifactId - The artifact ID to approve.
     * @returns True if approval succeeded, false otherwise.
     */
    async approveArtifact(artifactId: string): Promise<boolean> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder open');
            return false;
        }

        const rootPath = workspaceFolders[0].uri.fsPath;

        try {
            const { stdout, stderr } = await execAsync(
                `rice-factor approve ${artifactId}`,
                { cwd: rootPath }
            );

            if (stderr) {
                console.error('Approval stderr:', stderr);
            }

            console.log('Approval stdout:', stdout);
            return true;
        } catch (error) {
            if (error instanceof Error) {
                vscode.window.showErrorMessage(`Approval failed: ${error.message}`);
            }
            return false;
        }
    }

    /**
     * Applies a diff using the rice-factor CLI.
     *
     * @param artifactId - The artifact ID containing the diff.
     * @returns True if application succeeded, false otherwise.
     */
    async applyDiff(artifactId: string): Promise<boolean> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder open');
            return false;
        }

        const rootPath = workspaceFolders[0].uri.fsPath;

        // First confirm with user
        const confirm = await vscode.window.showWarningMessage(
            'Apply this diff? This will modify files in your workspace.',
            { modal: true },
            'Apply'
        );

        if (confirm !== 'Apply') {
            return false;
        }

        try {
            const { stdout, stderr } = await execAsync(
                `rice-factor apply ${artifactId}`,
                { cwd: rootPath }
            );

            if (stderr) {
                console.error('Apply stderr:', stderr);
            }

            console.log('Apply stdout:', stdout);
            return true;
        } catch (error) {
            if (error instanceof Error) {
                vscode.window.showErrorMessage(`Apply failed: ${error.message}`);
            }
            return false;
        }
    }

    /**
     * Runs a rice-factor command.
     *
     * @param command - The command to run.
     * @returns The command output.
     */
    async runCommand(command: string): Promise<string> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            throw new Error('No workspace folder open');
        }

        const rootPath = workspaceFolders[0].uri.fsPath;

        const { stdout } = await execAsync(
            `rice-factor ${command}`,
            { cwd: rootPath }
        );

        return stdout;
    }
}
