<template>
  <div class="admin-container">
    <div class="admin-header">
      <div class="admin-header-row">
        <h1>Admin Panel</h1>
        <a
          href="https://www.paypal.com/donate/?hosted_button_id=64BS2U8G43M5U"
          target="_blank"
          rel="noopener noreferrer"
          class="admin-donate-link"
        >💛 Spenden</a>
      </div>

      <div class="admin-tabs">
        <router-link
          v-for="tab in visibleTabs"
          :key="tab.path"
          :to="tab.path"
          :class="['tab-button', { active: isTabActive(tab.path) }]"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </router-link>
      </div>
    </div>

    <div class="tab-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const tabs = [
  { path: '/admin/members', label: 'Mitglieder', icon: '👥', roles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
  { path: '/admin/users', label: 'Benutzer', icon: '👤', roles: ['TOP_ADMIN', 'ADMIN'] },
  { path: '/admin/products', label: 'Produkte', icon: '📦', roles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
  { path: '/admin/categories', label: 'Kategorien', icon: '🏷️', roles: ['TOP_ADMIN', 'ADMIN'] },
  { path: '/admin/finance', label: 'Finanzen', icon: '💰', roles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
  { path: '/admin/vouchers', label: 'Gutscheine', icon: '🎫', roles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
  { path: '/admin/config', label: 'Einstellungen', icon: '⚙️', roles: ['TOP_ADMIN', 'ADMIN'] },
]

const visibleTabs = computed(() => tabs.filter(tab => tab.roles.includes(authStore.role)))

const isTabActive = (path) => route.path === path
</script>

<style scoped lang="scss">
.admin-container {
  height: 100%;
  min-height: 0;
  padding: 0.5rem 1rem 0.75rem;
  display: flex;
  flex-direction: column;
}

.admin-header {
  flex-shrink: 0;
  padding-bottom: 0.4rem;
  background: var(--app-background-color);
}

.admin-header-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;

  h1 {
    color: #333;
    margin: 0;
    font-size: 1.35rem;
  }
}

.admin-donate-link {
  font-size: 0.78rem;
  font-weight: 600;
  color: #888;
  text-decoration: none;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.2rem 0.5rem;
  white-space: nowrap;
  transition: color 0.15s, border-color 0.15s;

  &:hover {
    color: #555;
    border-color: #bbb;
  }
}

.admin-tabs {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
}

.tab-button {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  white-space: nowrap;
  padding: 0.4rem 0.75rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #94a3b8;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  border-radius: 8px;

  &:hover {
    background: color-mix(in srgb, var(--app-banner-color) 14%, white);
    border-color: color-mix(in srgb, var(--app-banner-color) 70%, #000 25%);
    color: #334155;
  }

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

.tab-icon {
  font-size: 0.85rem;
}

.tab-content {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  animation: fadeIn 0.2s;
}

@media (max-width: 700px) {
  .admin-container {
    padding: 0.4rem 0.75rem 0.6rem;
  }

  .tab-button {
    padding: 0.35rem 0.6rem;
    font-size: 0.8rem;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
