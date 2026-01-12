/**
 * Artifact Tree View Provider
 *
 * Provides a tree view of artifacts in the sidebar.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { ArtifactItem } from './extension';

/**
 * Artifact data structure.
 */
interface Artifact {
    id: string;
    artifact_type: string;
    status: string;
    version: number;
    created_at: string;
    payload: Record<string, unknown>;
}

/**
 * Tree data provider for artifacts.
 */
export class ArtifactTreeProvider implements vscode.TreeDataProvider<ArtifactTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ArtifactTreeItem | undefined | null | void> =
        new vscode.EventEmitter<ArtifactTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ArtifactTreeItem | undefined | null | void> =
        this._onDidChangeTreeData.event;

    private artifacts: Map<string, Artifact[]> = new Map();

    /**
     * Creates an instance of ArtifactTreeProvider.
     */
    constructor() {
        this.loadArtifacts();
    }

    /**
     * Refreshes the tree view.
     */
    refresh(): void {
        this.loadArtifacts();
        this._onDidChangeTreeData.fire();
    }

    /**
     * Gets tree item for display.
     */
    getTreeItem(element: ArtifactTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * Gets children for a tree item.
     */
    getChildren(element?: ArtifactTreeItem): Thenable<ArtifactTreeItem[]> {
        if (!element) {
            // Root level - show artifact types
            const types = Array.from(this.artifacts.keys());
            return Promise.resolve(
                types.map(type => new ArtifactTreeItem(
                    type,
                    '',
                    type,
                    'unknown',
                    vscode.TreeItemCollapsibleState.Collapsed
                ))
            );
        } else if (element.collapsibleState === vscode.TreeItemCollapsibleState.Collapsed) {
            // Type level - show artifacts of this type
            const artifacts = this.artifacts.get(element.label as string) || [];
            return Promise.resolve(
                artifacts.map(artifact => {
                    const item = new ArtifactTreeItem(
                        artifact.id.substring(0, 8) + '...',
                        artifact.id,
                        artifact.artifact_type,
                        artifact.status,
                        vscode.TreeItemCollapsibleState.None
                    );
                    item.description = `[${artifact.status}]`;
                    item.tooltip = `ID: ${artifact.id}\nStatus: ${artifact.status}\nVersion: ${artifact.version}`;
                    item.contextValue = `artifact-${artifact.status.toLowerCase()}`;
                    return item;
                })
            );
        }
        return Promise.resolve([]);
    }

    /**
     * Loads artifacts from the workspace.
     */
    private loadArtifacts(): void {
        this.artifacts.clear();

        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            return;
        }

        const artifactsPath = path.join(workspaceFolders[0].uri.fsPath, 'artifacts');
        if (!fs.existsSync(artifactsPath)) {
            return;
        }

        // Read all subdirectories (artifact types)
        const types = fs.readdirSync(artifactsPath, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory())
            .map(dirent => dirent.name);

        for (const type of types) {
            const typePath = path.join(artifactsPath, type);
            const files = fs.readdirSync(typePath)
                .filter(file => file.endsWith('.json'));

            const artifacts: Artifact[] = [];
            for (const file of files) {
                try {
                    const filePath = path.join(typePath, file);
                    const content = fs.readFileSync(filePath, 'utf-8');
                    const artifact = JSON.parse(content) as Artifact;
                    artifacts.push(artifact);
                } catch (error) {
                    console.error(`Failed to parse artifact ${file}:`, error);
                }
            }

            if (artifacts.length > 0) {
                this.artifacts.set(type, artifacts);
            }
        }
    }
}

/**
 * Represents an item in the artifact tree view.
 */
export class ArtifactTreeItem extends vscode.TreeItem implements ArtifactItem {
    constructor(
        public readonly label: string,
        public readonly artifactId: string,
        public readonly artifactType: string,
        public readonly status: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
    }

    iconPath = new vscode.ThemeIcon(this.getIconName());

    private getIconName(): string {
        switch (this.status.toLowerCase()) {
            case 'draft':
                return 'file';
            case 'approved':
                return 'check';
            case 'locked':
                return 'lock';
            default:
                return 'file';
        }
    }
}
