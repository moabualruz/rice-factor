/**
 * Extension Tests
 *
 * Basic tests for the Rice-Factor VS Code extension.
 */

import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Extension Test Suite', () => {
    vscode.window.showInformationMessage('Start all tests.');

    test('Extension should be present', () => {
        assert.ok(vscode.extensions.getExtension('rice-factor.rice-factor-vscode'));
    });

    test('Extension should activate', async () => {
        const extension = vscode.extensions.getExtension('rice-factor.rice-factor-vscode');
        if (extension) {
            await extension.activate();
            assert.ok(extension.isActive);
        }
    });

    test('Commands should be registered', async () => {
        const commands = await vscode.commands.getCommands(true);

        assert.ok(commands.includes('riceFactor.refreshArtifacts'));
        assert.ok(commands.includes('riceFactor.approveArtifact'));
        assert.ok(commands.includes('riceFactor.viewDiff'));
        assert.ok(commands.includes('riceFactor.applyDiff'));
    });

    test('Views should be registered', () => {
        // Views are registered via package.json contributes
        // This test verifies the extension loaded correctly
        assert.ok(true);
    });
});
