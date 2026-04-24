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
          <span class="navbar-title">
            {{ appSettingsStore.settings.app_name }}
          </span>
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
              v-if="authStore.isKasseUser"
              class="btn-login"
              @click="openLoginModal"
            >
              Login
            </button>

            <button
              class="btn-logout"
              @click="logout"
            >
              Logout
            </button>
          </div>

          <span class="current-user">
            Angemeldet: {{ authStore.user?.username }}
          </span>
        </div>
      </div>
    </nav>


    <main class="main-content">
      <router-view />

      <!-- platzsparender Footer direkt im grauen Inhaltsbereich -->
      <div class="app-inline-footer">
        © by Pixel-Finanz 2026 · {{ pkg.name }} v{{ pkg.version }}
      </div>

    </main>


    <div
      v-if="showLoginModal"
      class="modal-overlay"
    >
      <div class="modal-card">
        <h3>Benutzer anmelden</h3>

        <label>
          Benutzername
          <input
            v-model="loginForm.username"
            type="text"
            class="form-input"
          >
        </label>

        <label>
          Passwort
          <input
            v-model="loginForm.password"
            type="password"
            class="form-input"
            @keyup.enter="loginFromModal"
          >
        </label>

        <p
          v-if="modalError"
          class="modal-error"
        >
          {{ modalError }}
        </p>

        <div class="modal-actions">
          <button
            class="btn-login"
            @click="loginFromModal"
          >
            Login
          </button>

          <button
            class="btn-logout"
            @click="closeLoginModal"
          >
            Abbrechen
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppSettingsStore } from '@/stores/appSettings'
import { useRouter } from 'vue-router'

import NotificationCenter from '@/components/NotificationCenter.vue'
import PwaInstallButton from '@/components/PwaInstallButton.vue'

import pkg from '../package.json'

const authStore = useAuthStore()
const appSettingsStore = useAppSettingsStore()
const router = useRouter()

const showLoginModal = ref(false)
const modalError = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

const openLoginModal = () => {
  showLoginModal.value = true
  modalError.value = ''
  loginForm.username = authStore.user?.username || ''
  loginForm.password = ''
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}

const closeLoginModal = () => {
  showLoginModal.value = false
  modalError.value = ''
  loginForm.username = ''
  loginForm.password = ''
}

const loginFromModal = async () => {
  modalError.value = ''

  const success =
    await authStore.login(
      loginForm.username,
      loginForm.password
    )

  if (!success) {
    modalError.value =
      authStore.error || 'Login fehlgeschlagen'
    return
  }

  closeLoginModal()
  router.push('/')
}

const handleBeforeUnload = () => {
  authStore.clearClientSession()
}

onMounted(() => {
  appSettingsStore.applyToDocument()
  window.addEventListener(
    'beforeunload',
    handleBeforeUnload
  )
})

onBeforeUnmount(() => {
  window.removeEventListener(
    'beforeunload',
    handleBeforeUnload
  )
})
</script>

<style scoped lang="scss">
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 100vh;
  background-color: var(--app-background-color);
  overflow: hidden;
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 1200;
  flex-shrink: 0;
  background: var(--app-banner-color);
  color: white;
  padding: 0.85rem 1rem;
  box-shadow: 0 4px 12px rgba(0,0,0,.2);
  border-bottom: 3px solid var(--app-highlight-color);

  .navbar-content{
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:1rem;
    max-width:1200px;
    margin:0 auto;
  }

  .navbar-brand{
    display:flex;
    align-items:center;
    gap:.85rem;
  }

  .navbar-title{
    color:var(--app-banner-contrast);
    font-size:clamp(1.1rem,1.8vw,1.6rem);
    font-weight:700;
  }

  .navbar-logo{
    width:min(300px,62vw);
    height:58px;
    object-fit:contain;
  }

  .navbar-menu{
    display:flex;
    flex-direction:column;
    gap:.45rem;
    align-items:flex-end;
  }

  .navbar-actions{
    display:flex;
    gap:.75rem;
    flex-wrap:wrap;
    justify-content:flex-end;
  }

  .nav-link{
    color:var(--app-banner-contrast);
    text-decoration:none;
    padding:.5rem .9rem;
    border-radius:999px;

    &:hover,
    &.router-link-active{
      background:var(--app-highlight-color);
      color:var(--app-highlight-contrast);
    }
  }

  .btn-logout{
    background:#d32f2f;
    color:#fff;
    border:none;
    padding:.5rem 1rem;
    border-radius:999px;
    cursor:pointer;
  }

  .btn-login{
    background:var(--app-highlight-color);
    color:var(--app-highlight-contrast);
    border:none;
    padding:.5rem 1rem;
    border-radius:999px;
    cursor:pointer;
  }

  .current-user{
    font-weight:600;
    font-size:.95rem;
  }
}

.main-content{
  flex:1;
  min-height:0;
  overflow-y:auto;
  padding:0 0 8px 0;
}

/* Neuer integrierter Footer */
.app-inline-footer{
  text-align:center;
  font-size:11px;
  line-height:1.2;
  opacity:.55;

  padding:6px 12px 4px;
  margin-top:8px;

  color:var(--app-text-color, #555);
  user-select:none;
}


.modal-overlay{
  position:fixed;
  inset:0;
  background:rgba(15,23,42,.55);
  display:grid;
  place-items:center;
  z-index:2000;
}

.modal-card{
  background:white;
  border-radius:16px;
  padding:1.5rem;
  width:min(92vw,420px);
  display:flex;
  flex-direction:column;
  gap:.9rem;

  h3{
    margin:0;
  }

  label{
    display:flex;
    flex-direction:column;
    gap:.35rem;
    font-weight:600;
  }
}

.form-input{
  width:100%;
  padding:.75rem;
  border:1px solid #ddd;
  border-radius:8px;
  font-size:1rem;
}

.modal-actions{
  display:flex;
  gap:.75rem;
  justify-content:flex-end;
}

.modal-error{
  margin:0;
  color:#c62828;
  font-weight:600;
}

@media (max-width:700px){

  .navbar .navbar-content{
    flex-direction:column;
    align-items:stretch;
  }

  .navbar .navbar-brand{
    justify-content:center;
  }

  .navbar .navbar-menu{
    align-items:center;
  }

  .navbar .navbar-actions{
    justify-content:center;
  }

}
</style>

