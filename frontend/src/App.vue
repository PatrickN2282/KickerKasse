<template>
  <div
    id="app"
    class="app"
  >
    <NotificationCenter />
    <nav
      v-if="authStore.isAuthenticated"
      class="navbar"
    >
      <div class="navbar-content">
        <div class="navbar-brand">
          <img
            :src="appSettingsStore.logoUrl"
            :alt="appSettingsStore.settings.app_name"
            class="navbar-logo"
          >
          <span class="navbar-title">{{ appSettingsStore.settings.app_name }}</span>
        </div>
        <div class="navbar-menu">
          <div class="navbar-actions">
            <router-link
              to="/"
              class="nav-link"
            >
              Kasse
            </router-link>
            <router-link
              v-if="authStore.canAccessAdminPanel"
              to="/admin"
              class="nav-link"
            >
              Admin
            </router-link>
            <PwaInstallButton />
            <button
              class="btn-logout"
              @click="logout"
            >
              Logout
            </button>
          </div>
          <span class="current-user">Angemeldet: {{ authStore.user?.username }}</span>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppSettingsStore } from '@/stores/appSettings'
import { useRouter } from 'vue-router'
import NotificationCenter from '@/components/NotificationCenter.vue'
import PwaInstallButton from '@/components/PwaInstallButton.vue'

const authStore = useAuthStore()
const appSettingsStore = useAppSettingsStore()
const router = useRouter()

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  appSettingsStore.applyToDocument()
})
</script>

<style scoped lang="scss">
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--app-background-color);
}

.navbar {
  background: var(--app-banner-color);
  color: white;
  padding: 0.85rem 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  border-bottom: 3px solid var(--app-highlight-color);

  .navbar-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .navbar-brand {
    display: flex;
    align-items: center;
    gap: 0.85rem;
  }

  .navbar-title {
    color: var(--app-banner-contrast);
    font-size: clamp(1.1rem, 1.8vw, 1.6rem);
    font-weight: 700;
    line-height: 1.2;
  }

  .navbar-logo {
    width: min(300px, 62vw);
    height: 58px;
    object-fit: contain;
  }

  .navbar-menu {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    align-items: flex-end;
  }

  .navbar-actions {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .nav-link {
    color: var(--app-banner-contrast);
    text-decoration: none;
    padding: 0.5rem 0.9rem;
    border-radius: 999px;
    transition: all 0.2s;

    &:hover,
    &.router-link-active {
      background-color: var(--app-highlight-color);
      color: var(--app-highlight-contrast);
    }
  }

  .btn-logout {
    background-color: #d32f2f;
    color: #fff;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 999px;
    cursor: pointer;
  }

  .current-user {
    color: var(--app-banner-contrast);
    font-weight: 600;
    font-size: 0.95rem;
  }
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

@media (max-width: 700px) {
  .navbar .navbar-content {
    flex-direction: column;
    align-items: stretch;
  }

  .navbar .navbar-brand {
    justify-content: center;
    text-align: center;
  }

  .navbar .navbar-menu {
    align-items: center;
  }

  .navbar .navbar-actions {
    justify-content: center;
  }
}
</style>
