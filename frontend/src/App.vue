<template>
  <div id="app" class="app">
    <NotificationCenter />
    <nav v-if="authStore.isAuthenticated" class="navbar">
      <div class="navbar-content">
        <h1 class="navbar-title">Kassensoftware</h1>
        <div class="navbar-menu">
          <router-link to="/" class="nav-link">Kasse</router-link>
          <router-link to="/admin" class="nav-link" v-if="isAdmin">Admin</router-link>
          <button @click="logout" class="btn-logout">Logout</button>
        </div>
      </div>
    </nav>
    
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { computed } from 'vue'
import NotificationCenter from '@/components/NotificationCenter.vue'

const authStore = useAuthStore()
const router = useRouter()

const isAdmin = computed(() => authStore.user?.role === 'ADMIN')

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped lang="scss">
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.navbar {
  background-color: #1976d2;
  color: white;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  .navbar-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
  }

  .navbar-title {
    margin: 0;
    font-size: 1.5rem;
  }

  .navbar-menu {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .nav-link {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background-color 0.2s;

    &:hover {
      background-color: rgba(0, 0, 0, 0.1);
    }

    &.router-link-active {
      background-color: rgba(0, 0, 0, 0.2);
    }
  }

  .btn-logout {
    background-color: #d32f2f;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;

    &:hover {
      background-color: #c62828;
    }
  }
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

@media (max-width: 600px) {
  .navbar-content {
    flex-direction: column;
    gap: 1rem;
  }

  .navbar-menu {
    width: 100%;
    justify-content: center;
  }
}
</style>
