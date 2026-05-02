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

        <!-- Spalte 1: Logo -->
        <div class="navbar-col navbar-col--logo">
          <img
            :src="appSettingsStore.logoUrl"
            :alt="appSettingsStore.settings.app_name"
            class="navbar-logo"
          >
        </div>

        <!-- Spalte 2: Titel -->
        <div class="navbar-col navbar-col--title">
          <span class="navbar-title">
            {{ appSettingsStore.settings.app_name }}
          </span>
        </div>

        <!-- Spalte 3: Navigation + User-Aktionen -->
        <div class="navbar-col navbar-col--actions">
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

          <!-- Logout-Button mit eingebettetem Username -->
          <button
            class="btn-logout"
            @click="logout"
          >
            <span class="btn-logout__user">{{ authStore.user?.username }}</span>
            <span class="btn-logout__label">Logout</span>
          </button>
        </div>

      </div>
    </nav>


    <main class="main-content">
      <router-view />
    </main>


    <div class="app-inline-footer">
      {{ pkg.name }} v{{ pkg.version }} · © by Pixel-Finanz 2026
    </div>


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
            <span class="btn-logout__label">Abbrechen</span>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>


<script setup>
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppSettingsStore } from '@/stores/appSettings'
import { useRouter } from 'vue-router'

import NotificationCenter from '@/components/NotificationCenter.vue'
import PwaInstallButton from '@/components/PwaInstallButton.vue'

import pkg from '../package.json'
import { KASSE_LAYOUT_REFRESH_INTERVAL_MS, KASSE_LAYOUT_STORAGE_KEY, SESSION_RELOAD_FLAG_KEY } from '@/constants'

const authStore = useAuthStore()
const appSettingsStore = useAppSettingsStore()
const router = useRouter()

const showLoginModal = ref(false)
const modalError = ref('')
const layoutRefreshIntervalId = ref(null)
const refreshInFlight = ref(false)

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

  const success = await authStore.login(
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
  sessionStorage.setItem(SESSION_RELOAD_FLAG_KEY, '1')
  authStore.clearClientSession()
}

const syncLayoutStorage = (layout) => {
  if (layout) {
    localStorage.setItem(KASSE_LAYOUT_STORAGE_KEY, layout)
    return
  }
  localStorage.removeItem(KASSE_LAYOUT_STORAGE_KEY)
}

const refreshPublicSettings = async () => {
  if (!authStore.isAuthenticated) return
  if (refreshInFlight.value) return

  refreshInFlight.value = true
  try {
    await appSettingsStore.loadPublicSettings()
  } catch (error) {
    console.error('[App] Failed to refresh public app settings:', error)
  } finally {
    refreshInFlight.value = false
  }
}

const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    refreshPublicSettings()
  }
}

watch(
  () => appSettingsStore.settings.kasse_layout,
  (layout) => {
    syncLayoutStorage(layout)
  },
  { immediate: true }
)

onMounted(async () => {
  appSettingsStore.applyToDocument()

  window.addEventListener('beforeunload', handleBeforeUnload)
  window.addEventListener('focus', refreshPublicSettings)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  layoutRefreshIntervalId.value = window.setInterval(refreshPublicSettings, KASSE_LAYOUT_REFRESH_INTERVAL_MS)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  window.removeEventListener('focus', refreshPublicSettings)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (layoutRefreshIntervalId.value !== null) {
    window.clearInterval(layoutRefreshIntervalId.value)
  }
})
</script>



<style scoped lang="scss">
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 100vh;
  position: relative;
  background-color: var(--app-background-color);
  overflow: hidden;
}


/* ── Navbar ─────────────────────────────────────────────── */
.navbar {
  position: sticky;
  top: 0;
  z-index: 1200;
  flex-shrink: 0;

  background: var(--app-banner-color);
  color: white;

  /* Highlight-Streifen unten, etwas kräftiger */
  border-bottom: 3px solid var(--app-highlight-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, .18);
}

.navbar-content {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  align-items: center;

  width: 100%;
  padding: .3rem .85rem;
  box-sizing: border-box;
  min-height: 52px; /* kompakte Gesamthöhe */
}

/* ── Spalten ─────────────────────────────────────────────── */
.navbar-col {
  display: flex;
  align-items: center;

  &--logo {
    justify-content: flex-start;
  }

  &--title {
    justify-content: center;
  }

  &--actions {
    justify-content: flex-end;
    gap: .45rem;
    flex-wrap: wrap;
  }
}

/* ── Logo ────────────────────────────────────────────────── */
.navbar-logo {
  width: min(130px, 28vw);
  height: 40px;
  object-fit: contain;
}

/* ── Titel ───────────────────────────────────────────────── */
.navbar-title {
  color: var(--app-banner-contrast);
  font-size: clamp(.9rem, 1.4vw, 1.2rem);
  font-weight: 800;
  letter-spacing: .01em;
  text-align: center;
  white-space: nowrap;
}

/* ── Nav-Links ───────────────────────────────────────────── */
.nav-link {
  color: var(--app-banner-contrast);
  text-decoration: none;
  padding: .25rem .65rem;
  border-radius: 999px;
  font-size: .82rem;
  transition: all .2s;

  &:hover,
  &.router-link-active {
    background: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

/* ── Buttons ─────────────────────────────────────────────── */
.btn-login {
  background: var(--app-highlight-color);
  color: var(--app-highlight-contrast);
  border: none;
  padding: .25rem .7rem;
  border-radius: 999px;
  cursor: pointer;
  font-size: .82rem;
  line-height: 1.2;
}

/* Logout-Button: Username als kleine Zeile darüber */
.btn-logout {
  background: #c62828;
  color: #fff;
  border: none;
  padding: .18rem .7rem .22rem;
  border-radius: 999px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  line-height: 1.15;

  &__user {
    font-size: .65rem;
    font-weight: 600;
    opacity: .82;
    letter-spacing: .03em;
    text-transform: uppercase;
  }

  &__label {
    font-size: .82rem;
    font-weight: 700;
  }
}


/* ── Main ────────────────────────────────────────────────── */
.main-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 0 18px 0;
}


/* ── Footer ──────────────────────────────────────────────── */
.app-inline-footer {
  position: absolute;
  bottom: 3px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 10px;
  letter-spacing: .04em;
  line-height: 1.1;
  opacity: .42;
  color: var(--app-text-color, #555);
  user-select: none;
  pointer-events: none;
}


/* ── Modal ───────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, .55);
  display: grid;
  place-items: center;
  z-index: 2000;
}

.modal-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  width: min(92vw, 420px);
  display: flex;
  flex-direction: column;
  gap: .9rem;

  h3 { margin: 0; }

  label {
    display: flex;
    flex-direction: column;
    gap: .35rem;
    font-weight: 600;
  }
}

.form-input {
  width: 100%;
  padding: .75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.modal-actions {
  display: flex;
  gap: .75rem;
  justify-content: flex-end;
}

.modal-error {
  margin: 0;
  color: #c62828;
  font-weight: 600;
}


/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 700px) {
  .navbar-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    gap: .3rem;
    padding: .4rem .85rem;
    min-height: unset;
  }

  .navbar-col {
    justify-content: center;

    &--logo { order: 1; }
    &--title { order: 2; }
    &--actions {
      order: 3;
      flex-wrap: wrap;
      justify-content: center;
    }
  }
}
</style>
