<template>
  <div class="admin-container">
    <div class="admin-header">
      <h1>Admin Panel</h1>

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
  { path: '/admin/products', label: 'Produkte', icon: '📦', roles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
  { path: '/admin/categories', label: 'Kategorien', icon: '🏷️', roles: ['TOP_ADMIN', 'ADMIN'] },
  { path: '/admin/users', label: 'Benutzer', icon: '👤', roles: ['TOP_ADMIN', 'ADMIN'] },
  { path: '/admin/vouchers', label: 'Gutscheine', icon: '🎫', roles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
  { path: '/admin/finance', label: 'Finanzen', icon: '💰', roles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
  { path: '/admin/corrections', label: 'Konto-Korrektur', icon: '🧾', roles: ['TOP_ADMIN', 'ADMIN'] },
  { path: '/admin/settings', label: 'Design', icon: '🎨', roles: ['TOP_ADMIN', 'ADMIN'] },
  { path: '/admin/data-maintenance', label: 'Datenpflege', icon: '🧹', roles: ['TOP_ADMIN', 'ADMIN'] },
  { path: '/admin/ext-settings', label: 'Ext. Settings', icon: '⚙️', roles: ['TOP_ADMIN'] },
]

const visibleTabs = computed(() => tabs.filter(tab => tab.roles.includes(authStore.role)))

const isTabActive = (path) => route.path === path
</script>

<style scoped lang="scss">
.admin-container {
  height: 100%;
  min-height: 0;
  padding: 1rem 1.25rem 1.25rem;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

.admin-header {
  flex-shrink: 0;
  padding-bottom: 0.75rem;
  background: var(--app-background-color);

  h1 {
    color: #333;
    margin-bottom: 1rem;
  }
}

.admin-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
}

.tab-button {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  white-space: nowrap;
  padding: 0.55rem 0.9rem;
  background: color-mix(in srgb, var(--app-banner-color) 14%, white);
  border: 1px solid color-mix(in srgb, var(--app-banner-color) 70%, #000 25%);
  color: #334155;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  border-radius: 8px;

  &:hover,
  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

.tab-icon {
  font-size: 0.95rem;
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
    padding: 0.85rem 0.9rem 1rem;
  }

  .tab-button {
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
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
