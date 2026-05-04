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

          <PwaInstallButton />

          <!-- User-Chip: immer sichtbar -->
          <span class="user-chip">
            👤 {{ authStore.user?.username }}
          </span>

          <!-- Kasse-User: nur Login anzeigen, kein Kasse/Logout -->
          <template v-if="isKasseUser">
            <button
              class="btn-login"
              @click="openLoginModal"
            >
              Login
            </button>
          </template>

          <!-- Anderer User: entweder Kasse oder Admin (je nach aktiver Route), plus Logout -->
          <template v-else>
            <router-link
              v-if="isOnAdminRoute"
              to="/"
              class="nav-link nav-link--kasse"
            >
              Kasse
            </router-link>

            <router-link
              v-else-if="authStore.canAccessAdminPanel"
              to="/admin"
              class="nav-link nav-link--admin"
            >
              Admin
            </router-link>

            <button
              class="btn-logout"
              @click="logout"
            >
              Logout
            </button>
          </template>

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
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppSettingsStore } from '@/stores/appSettings'
import { useNotificationStore } from '@/stores/notification'
import { useRoute, useRouter } from 'vue-router'

import NotificationCenter from '@/components/NotificationCenter.vue'
import PwaInstallButton from '@/components/PwaInstallButton.vue'

import pkg from '../package.json'
import { KASSE_LAYOUT_REFRESH_INTERVAL_MS, KASSE_LAYOUT_STORAGE_KEY, SESSION_RELOAD_FLAG_KEY } from '@/constants'

const authStore = useAuthStore()
const appSettingsStore = useAppSettingsStore()
const notificationStore = useNotificationStore()
const router = useRouter()
const route = useRoute()

// true wenn der angemeldete User der Kasse-User ist
const isKasseUser = computed(() => authStore.isKasseUser)
// true wenn gerade die Admin-Route aktiv ist
const isOnAdminRoute = computed(() => route.path.startsWith('/admin'))

const showLoginModal = ref(false)
const modalError = ref('')
const layoutRefreshIntervalId = ref(null)
const refreshInFlight = ref(false)
const sessionTimerId = ref(null)

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

const clearSessionTimer = () => {
  if (sessionTimerId.value !== null) {
    window.clearTimeout(sessionTimerId.value)
    sessionTimerId.value = null
  }
}

const sessionTimerDelayMs = computed(() => {
  if (!authStore.isAuthenticated || !appSettingsStore.settings.session_timer_enabled) {
    return null
  }

  const minutes = Number(appSettingsStore.settings.session_timer_minutes)
  if (!Number.isFinite(minutes) || minutes < 1) {
    return null
  }

  return minutes * 60 * 1000
})

const handleSessionTimeout = async () => {
  clearSessionTimer()
  if (!authStore.isAuthenticated) return

  closeLoginModal()
  await authStore.logout()
  notificationStore.info('Session-Timer: Benutzer wurde automatisch abgemeldet')
  router.replace('/login')
}

const resetSessionTimer = () => {
  clearSessionTimer()
  if (sessionTimerDelayMs.value == null) return
  sessionTimerId.value = window.setTimeout(handleSessionTimeout, sessionTimerDelayMs.value)
}

const handleUserActivity = () => {
  if (document.visibilityState === 'hidden') return
  resetSessionTimer()
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
  clearSessionTimer()
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

watch(
  [
    () => authStore.isAuthenticated,
    () => appSettingsStore.settings.session_timer_enabled,
    () => appSettingsStore.settings.session_timer_minutes,
  ],
  ([isAuthenticated]) => {
    if (!isAuthenticated) {
      clearSessionTimer()
      return
    }
    resetSessionTimer()
  },
  { immediate: true }
)

onMounted(async () => {
  appSettingsStore.applyToDocument()

  window.addEventListener('beforeunload', handleBeforeUnload)
  window.addEventListener('focus', refreshPublicSettings)
  window.addEventListener('pointerdown', handleUserActivity)
  window.addEventListener('keydown', handleUserActivity)
  window.addEventListener('touchstart', handleUserActivity)
  window.addEventListener('scroll', handleUserActivity, true)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  layoutRefreshIntervalId.value = window.setInterval(refreshPublicSettings, KASSE_LAYOUT_REFRESH_INTERVAL_MS)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  window.removeEventListener('focus', refreshPublicSettings)
  window.removeEventListener('pointerdown', handleUserActivity)
  window.removeEventListener('keydown', handleUserActivity)
  window.removeEventListener('touchstart', handleUserActivity)
  window.removeEventListener('scroll', handleUserActivity, true)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (layoutRefreshIntervalId.value !== null) {
    window.clearInterval(layoutRefreshIntervalId.value)
  }
  clearSessionTimer()
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
  align-items: stretch; /* Spalten auf volle Navhöhe dehnen */

  width: 100%;
  padding: 0 .85rem;
  box-sizing: border-box;
  min-height: 54px;
}

/* ── Spalten ─────────────────────────────────────────────── */
.navbar-col {
  display: flex;
  align-items: center;

  &--logo {
    justify-content: flex-start;
    padding: .2rem 0; /* mini Luft oben/unten, Logo selbst füllt Rest */
  }

  &--title {
    justify-content: center;
  }

  &--actions {
    justify-content: flex-end;
    gap: .4rem;
    flex-wrap: wrap;
  }
}

/* ── Logo ────────────────────────────────────────────────── */
.navbar-logo {
  /* volle Navhöhe minus Border-bottom (3px) nutzen */
  height: calc(100% - 0px);
  max-height: 54px;
  width: auto;
  max-width: min(160px, 30vw);
  object-fit: contain;
}

/* ── Titel ───────────────────────────────────────────────── */
.navbar-title {
  color: var(--app-banner-contrast);
  font-size: clamp(1rem, 1.7vw, 1.4rem);
  font-weight: 800;
  letter-spacing: .01em;
  text-align: center;
  white-space: nowrap;
}

/* ── Gemeinsame Pill-Basis für Nav-Links + Buttons ───────── */
%pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: .85rem;
  font-weight: 700;
  letter-spacing: .05em;
  text-transform: uppercase;
  text-decoration: none;
  padding: .45rem 1.1rem;
  line-height: 1.2;
  transition: border-color .15s, box-shadow .15s;
  white-space: nowrap;

  &:hover { border-color: rgba(255,255,255,.85); }
}

/* ── Nav-Links ───────────────────────────────────────────── */
.nav-link {
  @extend %pill;
  background: rgba(255,255,255,.12);
  color: var(--app-banner-contrast);
  border-color: rgba(255,255,255,.18);

  &.router-link-active {
    border-color: rgba(255,255,255,.5);
  }

  &:hover {
    border-color: rgba(255,255,255,.85);
  }
}

/* Kasse → Highlight-Farbe */
.nav-link--kasse {
  background: var(--app-highlight-color);
  color: var(--app-highlight-contrast);
  border-color: transparent;
  box-shadow: 0 2px 6px rgba(0,0,0,.25);

  &.router-link-active {
    border-color: rgba(255,255,255,.5);
  }
}

/* Admin → Pastell-Gelb */
.nav-link--admin {
  background: #f5e642;
  color: #5a4a00;
  border-color: transparent;
  box-shadow: 0 2px 6px rgba(0,0,0,.2);
}

/* ── Login-Button → helles Grün ──────────────────────────── */
.btn-login {
  @extend %pill;
  background: #2e9e5b;
  color: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,.25);
}

/* ── User-Chip ───────────────────────────────────────────── */
.user-chip {
  display: inline-flex;
  align-items: center;
  gap: .3rem;
  background: rgba(255,255,255,.15);
  color: var(--app-banner-contrast);
  border: 1.5px solid rgba(255,255,255,.28);
  border-radius: 8px;
  padding: .4rem .85rem;
  font-size: .82rem;
  font-weight: 600;
  letter-spacing: .02em;
  white-space: nowrap;
  user-select: none;
}

/* ── Logout-Button ───────────────────────────────────────── */
.btn-logout {
  @extend %pill;
  background: #c62828;
  color: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,.28);
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
