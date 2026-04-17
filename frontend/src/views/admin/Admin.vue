<template>
  <div class="admin-container">
    <h1>Admin Panel</h1>

    <div class="admin-tabs">
      <router-link
        v-for="tab in visibleTabs"
        :key="tab.path"
        :to="tab.path"
        :class="['tab-button', { active: isTabActive(tab.path) }]"
      >
        {{ tab.label }}
      </router-link>
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
  { path: '/admin/members', label: '👥 Mitglieder', roles: ['ADMIN', 'KASSENMITGLIED'] },
  { path: '/admin/products', label: '📦 Produkte', roles: ['ADMIN'] },
  { path: '/admin/categories', label: '🏷️ Kategorien', roles: ['ADMIN'] },
  { path: '/admin/users', label: '👤 Benutzer', roles: ['ADMIN'] },
  { path: '/admin/vouchers', label: '🎫 Gutscheine', roles: ['ADMIN'] },
  { path: '/admin/finance', label: '💰 Finanzen', roles: ['ADMIN', 'KASSENMITGLIED'] },
  { path: '/admin/settings', label: '🎨 Design', roles: ['ADMIN'] },
]

const visibleTabs = computed(() => tabs.filter(tab => tab.roles.includes(authStore.role)))

const isTabActive = (path) => route.path === path
</script>

<style scoped lang="scss">
.admin-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;

  h1 {
    color: #333;
    margin-bottom: 2rem;
  }
}

.admin-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #f0f0f0;
  flex-wrap: wrap;
}

.tab-button {
  padding: 1rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: #666;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
  display: block;

  &:hover,
  &.active {
    color: var(--app-highlight-color);
    border-bottom-color: var(--app-highlight-color);
  }
}

.tab-content {
  animation: fadeIn 0.2s;
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
