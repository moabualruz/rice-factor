<script setup lang="ts">
import { computed } from "vue";
import { useRoute, RouterLink } from "vue-router";

const route = useRoute();

interface NavItem {
  name: string;
  path: string;
  icon: string;
}

const navItems: NavItem[] = [
  { name: "Dashboard", path: "/", icon: "dashboard" },
  { name: "Artifacts", path: "/artifacts", icon: "artifacts" },
  { name: "Diff Review", path: "/diffs", icon: "diff" },
  { name: "Approvals", path: "/approvals", icon: "approvals" },
  { name: "History", path: "/history", icon: "history" },
  { name: "Configuration", path: "/configuration", icon: "settings" },
  { name: "Terminal", path: "/commands", icon: "terminal" },
];

function isActive(path: string): boolean {
  if (path === "/") {
    return route.path === "/";
  }
  return route.path.startsWith(path);
}
</script>

<template>
  <aside
    class="w-56 bg-rf-bg-light border-r border-rf-secondary/30 min-h-[calc(100vh-56px)]"
  >
    <nav class="p-4">
      <ul class="space-y-2">
        <li v-for="item in navItems" :key="item.path">
          <RouterLink
            :to="item.path"
            :class="[
              'flex items-center px-4 py-2 rounded-lg transition-colors duration-200',
              isActive(item.path)
                ? 'bg-rf-primary text-white'
                : 'text-gray-300 hover:bg-rf-bg-dark hover:text-white',
            ]"
          >
            <span class="mr-3 text-lg">
              <template v-if="item.icon === 'dashboard'">&#9783;</template>
              <template v-else-if="item.icon === 'artifacts'"
                >&#128230;</template
              >
              <template v-else-if="item.icon === 'diff'">&#8801;</template>
              <template v-else-if="item.icon === 'approvals'"
                >&#10003;</template
              >
              <template v-else-if="item.icon === 'history'">&#128337;</template>
              <template v-else-if="item.icon === 'settings'">&#9881;</template>
              <template v-else-if="item.icon === 'terminal'"
                >&#128187;</template
              >
            </span>
            {{ item.name }}
          </RouterLink>
        </li>
      </ul>
    </nav>
  </aside>
</template>
