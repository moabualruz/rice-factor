<script setup lang="ts">
import { ref } from "vue";
import { executeCommand, type CommandResponse } from "@/api/commands";

const commandInput = ref("");
const executing = ref(false);
const history = ref<CommandResponse[]>([]);
const error = ref<string | null>(null);

// Common commands for quick access
const quickCommands = [
  { label: "Check Version", args: "--version" },
  { label: "System Info", args: "info" },
  { label: "Plan Status", args: "plan project --dry-run" },
  { label: "List Agents", args: "agents list" },
  { label: "Validate Project", args: "validate" },
];

async function runCommand(cmdString: string) {
  if (!cmdString.trim()) return;

  executing.value = true;
  error.value = null;

  // Clean args: split by space but respect quotes
  // Simple split for now, robust parsing requires regex or library
  // Just splitting by space is risky for "quoted args".
  // Let's assume user inputs args without complex quoting or we handle basic splitting.
  // Regex to match quoted strings (double or single) or non-whitespace sequences
  const args =
    cmdString.match(/[^\s"']+|"([^"]*)"|'([^']*)'/g)?.map((s) => {
      if (s.startsWith('"') && s.endsWith('"')) {
        return s.slice(1, -1);
      }
      if (s.startsWith("'") && s.endsWith("'")) {
        return s.slice(1, -1);
      }
      return s;
    }) || [];

  try {
    const response = await executeCommand({ args });
    history.value.unshift(response);
  } catch (e: any) {
    error.value = e.message;
  } finally {
    executing.value = false;
    commandInput.value = ""; // Clear input
  }
}

function runQuick(argsStr: string) {
  commandInput.value = argsStr; // Fill input
  runCommand(argsStr);
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-white">Advanced Command Control</h1>

    <!-- Command Input -->
    <div class="card">
      <form @submit.prevent="runCommand(commandInput)" class="flex gap-2">
        <div class="relative flex-grow">
          <span class="absolute left-3 top-2.5 text-gray-500 font-mono"
            >$ rice-factor</span
          >
          <input
            v-model="commandInput"
            type="text"
            class="w-full bg-rf-bg-dark text-white font-mono pl-28 pr-4 py-2 rounded border border-rf-secondary focus:border-rf-success outline-none"
            placeholder="enter command args (e.g., plan project --dry-run)"
            :disabled="executing"
          />
        </div>
        <button
          type="submit"
          class="btn-primary whitespace-nowrap"
          :disabled="executing || !commandInput"
        >
          {{ executing ? "Running..." : "Run" }}
        </button>
      </form>

      <!-- Quick Commands -->
      <div class="mt-4 flex flex-wrap gap-2">
        <button
          v-for="cmd in quickCommands"
          :key="cmd.label"
          class="px-3 py-1 bg-rf-secondary/20 hover:bg-rf-secondary/40 text-xs text-gray-300 rounded border border-rf-secondary/50 transition-colors"
          @click="runQuick(cmd.args)"
          :disabled="executing"
        >
          {{ cmd.label }}
        </button>
      </div>

      <div v-if="error" class="mt-4 text-red-500 text-sm">
        Error: {{ error }}
      </div>
    </div>

    <!-- Output History -->
    <div class="space-y-4">
      <div
        v-for="(item, index) in history"
        :key="index"
        class="card overflow-hidden"
      >
        <div
          class="flex justify-between items-center mb-2 text-xs font-mono border-b border-rf-secondary/30 pb-2"
        >
          <span class="text-gray-400">$ {{ item.command }}</span>
          <span
            :class="item.exit_code === 0 ? 'text-green-500' : 'text-red-500'"
          >
            Exit: {{ item.exit_code }}
          </span>
        </div>

        <pre
          v-if="item.stdout"
          class="text-xs font-mono text-gray-300 whitespace-pre-wrap"
          >{{ item.stdout }}</pre
        >
        <pre
          v-if="item.stderr"
          class="text-xs font-mono text-red-300 border-t border-red-900/30 mt-2 pt-2 whitespace-pre-wrap"
          >{{ item.stderr }}</pre
        >
        <div
          v-if="!item.stdout && !item.stderr"
          class="text-xs italic text-gray-600"
        >
          (No output)
        </div>
      </div>

      <div v-if="history.length === 0" class="text-center text-gray-500 py-12">
        No commands executed in this session.
      </div>
    </div>
  </div>
</template>
