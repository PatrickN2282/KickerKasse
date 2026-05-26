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
          <div class="logo-area">
            <img
              :src="appSettingsStore.logoUrl"
              :alt="appSettingsStore.settings.app_name"
              class="navbar-logo"
            >
            <PwaInstallButton />
          </div>
        </div>

        <!-- Spalte 2: Titel -->
        <div class="navbar-col navbar-col--title">
          <span class="navbar-title">
            {{ appSettingsStore.settings.app_name }}
          </span>
        </div>

        <!-- Spalte 3: Navigation + User-Aktionen -->
        <div class="navbar-col navbar-col--actions">

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
      <span>{{ pkg.name }} v{{ pkg.version }} · © by Pixel-Finanz 2026</span>
      <button
        type="button"
        class="footer-donate-link"
        @click="showDonationModal = true"
      >💛 Spenden</button>
    </div>

    <DonationModal
      :show="showDonationModal"
      @close="showDonationModal = false"
    />


    <div
      v-if="showLoginModal"
      class="modal-overlay"
    >
      <div class="modal-dialog">
        <div class="modal-header">
          <div class="modal-header-title">
            <h3>Benutzer anmelden <span class="header-pipe">|</span> <span class="header-sub">Zugangsdaten eingeben</span></h3>
          </div>
          <button
            class="close-btn"
            @click="closeLoginModal"
          >
            ✕
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>Benutzername</label>
            <input
              v-model="loginForm.username"
              type="text"
              list="login-usernames-list"
              class="form-input"
              placeholder="Benutzername eingeben oder auswählen"
              autocomplete="username"
            >
            <datalist id="login-usernames-list">
              <option
                v-for="name in availableUsernames"
                :key="name"
                :value="name"
              />
            </datalist>
          </div>

          <div class="form-group">
            <label>Passwort</label>
            <input
              v-model="loginForm.password"
              type="password"
              class="form-input"
              placeholder="Passwort eingeben"
              autocomplete="current-password"
              @keyup.enter="loginFromModal"
            >
          </div>

          <p
            v-if="modalError"
            class="modal-error"
          >
            {{ modalError }}
          </p>
        </div>

        <div class="modal-footer">
          <button
            class="btn btn-secondary"
            @click="closeLoginModal"
          >
            Abbrechen
          </button>
          <button
            class="btn btn-primary"
            :disabled="!loginForm.username.trim() || !loginForm.password"
            @click="loginFromModal"
          >
            Login
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
import DonationModal from '@/components/DonationModal.vue'
import apiService from '@/services/api'

import pkg from '../package.json'
import { KASSE_LAYOUT_REFRESH_INTERVAL_MS, KASSE_LAYOUT_STORAGE_KEY, SESSION_RELOAD_FLAG_KEY } from '@/constants'

const SESSION_ACTIVITY_RESET_THROTTLE_MS = 1000

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
const showDonationModal = ref(false)
const modalError = ref('')
const availableUsernames = ref([])
const layoutRefreshIntervalId = ref(null)
const refreshInFlight = ref(false)
const sessionTimerId = ref(null)
const lastSessionActivityAt = ref(0)

const loginForm = reactive({
  username: '',
  password: ''
})

const openLoginModal = async () => {
  showLoginModal.value = true
  modalError.value = ''
  loginForm.username = authStore.user?.username || ''
  loginForm.password = ''
  try {
    const response = await apiService.get('/auth/usernames')
    availableUsernames.value = response.data ?? []
  } catch {
    availableUsernames.value = []
  }
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

  const now = Date.now()
  if (now - lastSessionActivityAt.value < SESSION_ACTIVITY_RESET_THROTTLE_MS) {
    return
  }

  lastSessionActivityAt.value = now
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
  router.push(authStore.canAccessAdminPanel ? '/admin' : '/')
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
  window.addEventListener('scroll', handleUserActivity, { capture: true, passive: true })
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
    justify-content: center;
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
.logo-area {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: .6rem;
  text-align: center;
  font-size: 10px;
  letter-spacing: .04em;
  line-height: 1.1;
  opacity: .42;
  color: var(--app-text-color, #555);
  user-select: none;
  pointer-events: none;
}

.footer-donate-link {
  pointer-events: all;
  color: var(--app-text-color, #555);
  text-decoration: underline;
  opacity: 1;
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  font: inherit;

  &:hover {
    opacity: .8;
  }
}


/* ── Modal ───────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, .55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  z-index: 2000;
}

.modal-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: 100%;
  max-width: 460px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}

.modal-header {
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  flex-shrink: 0;
}

.modal-header-title {
  display: flex;
  align-items: center;
  min-width: 0;

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .header-pipe {
    margin: 0 0.5rem;
    opacity: 0.5;
  }

  .header-sub {
    font-weight: 400;
    opacity: 0.88;
    font-size: 0.92rem;
  }
}

.close-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 1.1rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
}

.modal-body {
  padding: 1rem 1.25rem;
  flex: 1;
}

.modal-footer {
  padding: 0.95rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  background: #ffffff;
  flex-shrink: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1rem;

  label {
    font-weight: 600;
    font-size: 0.9rem;
  }
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 1rem;
  box-sizing: border-box;
}

.btn {
  border: none;
  border-radius: 8px;
  padding: 0.65rem 1rem;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;

  &:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
}

.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
}

.btn-primary {
  background: var(--app-highlight-color);
  color: var(--app-highlight-contrast);
}

.modal-error {
  margin: 0 0 0.5rem;
  color: #c62828;
  font-weight: 600;
  font-size: 0.9rem;
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
