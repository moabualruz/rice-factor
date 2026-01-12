/**
 * Diff Preview Provider
 *
 * Provides diff preview functionality using VS Code's diff editor.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Implementation plan payload structure.
 */
interface ImplementationPlan {
    id: string;
    artifact_type: string;
    status: string;
    payload: {
        target_file: string;
        diff_content?: string;
        original_content?: string;
        modified_content?: string;
    };
}

/**
 * Provides diff preview functionality.
 */
export class DiffPreviewProvider {
    private context: vscode.ExtensionContext;

    /**
     * Creates an instance of DiffPreviewProvider.
     *
     * @param context - The extension context.
     */
    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    /**
     * Shows a diff for an artifact.
     *
     * @param artifactId - The artifact ID to show diff for.
     */
    async showDiff(artifactId: string): Promise<void> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder open');
            return;
        }

        const rootPath = workspaceFolders[0].uri.fsPath;

        // Find the artifact
        const artifact = await this.findArtifact(rootPath, artifactId);
        if (!artifact) {
            vscode.window.showErrorMessage(`Artifact ${artifactId} not found`);
            return;
        }

        const payload = artifact.payload;
        if (!payload.target_file) {
            vscode.window.showErrorMessage('Artifact has no target file');
            return;
        }

        const targetPath = path.join(rootPath, payload.target_file);

        // Get original content
        let originalContent = '';
        if (fs.existsSync(targetPath)) {
            originalContent = fs.readFileSync(targetPath, 'utf-8');
        } else if (payload.original_content) {
            originalContent = payload.original_content;
        }

        // Get modified content
        let modifiedContent = '';
        if (payload.modified_content) {
            modifiedContent = payload.modified_content;
        } else if (payload.diff_content) {
            // Apply diff to get modified content
            modifiedContent = this.applyDiff(originalContent, payload.diff_content);
        } else {
            vscode.window.showErrorMessage('Artifact has no diff or modified content');
            return;
        }

        // Create virtual documents for diff
        const originalUri = vscode.Uri.parse(`rice-factor-original:${payload.target_file}`);
        const modifiedUri = vscode.Uri.parse(`rice-factor-modified:${payload.target_file}`);

        // Register content providers
        const originalProvider = new (class implements vscode.TextDocumentContentProvider {
            provideTextDocumentContent(): string {
                return originalContent;
            }
        })();

        const modifiedProvider = new (class implements vscode.TextDocumentContentProvider {
            provideTextDocumentContent(): string {
                return modifiedContent;
            }
        })();

        this.context.subscriptions.push(
            vscode.workspace.registerTextDocumentContentProvider('rice-factor-original', originalProvider),
            vscode.workspace.registerTextDocumentContentProvider('rice-factor-modified', modifiedProvider)
        );

        // Show diff
        await vscode.commands.executeCommand(
            'vscode.diff',
            originalUri,
            modifiedUri,
            `Diff: ${payload.target_file} (${artifact.status})`
        );
    }

    /**
     * Finds an artifact by ID.
     *
     * @param rootPath - The workspace root path.
     * @param artifactId - The artifact ID to find.
     * @returns The artifact if found, undefined otherwise.
     */
    private async findArtifact(rootPath: string, artifactId: string): Promise<ImplementationPlan | undefined> {
        const artifactsPath = path.join(rootPath, 'artifacts');
        if (!fs.existsSync(artifactsPath)) {
            return undefined;
        }

        // Search all artifact type directories
        const types = fs.readdirSync(artifactsPath, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory())
            .map(dirent => dirent.name);

        for (const type of types) {
            const typePath = path.join(artifactsPath, type);
            const files = fs.readdirSync(typePath).filter(f => f.endsWith('.json'));

            for (const file of files) {
                try {
                    const filePath = path.join(typePath, file);
                    const content = fs.readFileSync(filePath, 'utf-8');
                    const artifact = JSON.parse(content) as ImplementationPlan;
                    if (artifact.id === artifactId) {
                        return artifact;
                    }
                } catch {
                    // Ignore parse errors
                }
            }
        }

        return undefined;
    }

    /**
     * Applies a unified diff to content.
     *
     * This is a simplified implementation - in production,
     * you would use a proper diff library.
     *
     * @param original - The original content.
     * @param diff - The unified diff.
     * @returns The modified content.
     */
    private applyDiff(original: string, diff: string): string {
        // Simple implementation - just return original for now
        // In production, use a diff library like 'diff' or 'jsdiff'
        const lines = original.split('\n');
        const diffLines = diff.split('\n');
        const result: string[] = [];

        let lineIndex = 0;
        for (const diffLine of diffLines) {
            if (diffLine.startsWith('+++') || diffLine.startsWith('---') || diffLine.startsWith('@@')) {
                continue;
            }
            if (diffLine.startsWith('+')) {
                result.push(diffLine.substring(1));
            } else if (diffLine.startsWith('-')) {
                lineIndex++;
            } else if (diffLine.startsWith(' ')) {
                result.push(diffLine.substring(1));
                lineIndex++;
            } else {
                // Context line without prefix
                if (lineIndex < lines.length) {
                    result.push(lines[lineIndex]);
                    lineIndex++;
                }
            }
        }

        // Add remaining lines
        while (lineIndex < lines.length) {
            result.push(lines[lineIndex]);
            lineIndex++;
        }

        return result.join('\n');
    }
}
