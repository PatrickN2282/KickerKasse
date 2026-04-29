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
    </main>


    <!-- Kein eigenes Banner, eingebettet über dem grauen Rand -->
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
import { SESSION_RELOAD_FLAG_KEY } from '@/constants'

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
.app{
  display:flex;
  flex-direction:column;
  height:100vh;
  min-height:100vh;

  position:relative; /* wichtig für Footer */

  background-color:var(--app-background-color);
  overflow:hidden;
}


.navbar{
  position:sticky;
  top:0;
  z-index:1200;

  flex-shrink:0;

  background:var(--app-banner-color);
  color:white;

  padding:.4rem .85rem;

  box-shadow:0 2px 8px rgba(0,0,0,.18);
  border-bottom:2px solid var(--app-highlight-color);

  .navbar-content{
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:.75rem;

    max-width:1200px;
    margin:0 auto;
  }

  .navbar-brand{
    display:flex;
    align-items:center;
    gap:.5rem;
  }

  .navbar-title{
    color:var(--app-banner-contrast);
    font-size:clamp(.85rem,1.2vw,1.15rem);
    font-weight:700;
  }

  .navbar-logo{
    width:min(150px,32vw);
    height:30px;
    object-fit:contain;
  }

  .navbar-menu{
    display:flex;
    flex-direction:column;
    gap:.2rem;
    align-items:flex-end;
  }

  .navbar-actions{
    display:flex;
    gap:.5rem;
    align-items:center;
    flex-wrap:wrap;
    justify-content:flex-end;
  }

  .nav-link{
    color:var(--app-banner-contrast);
    text-decoration:none;
    padding:.3rem .7rem;
    border-radius:999px;
    font-size:.85rem;

    transition:all .2s;

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
    padding:.3rem .75rem;
    border-radius:999px;
    cursor:pointer;
    font-size:.82rem;
  }

  .btn-login{
    background:var(--app-highlight-color);
    color:var(--app-highlight-contrast);
    border:none;
    padding:.3rem .75rem;
    border-radius:999px;
    cursor:pointer;
    font-size:.82rem;
  }

  .current-user{
    font-weight:600;
    font-size:.78rem;
    opacity:.85;
  }
}


.main-content{
  flex:1;
  min-height:0;

  overflow-y:auto;

  /* Reserve damit Footer nichts verschiebt */
  padding:0 0 18px 0;
}



/* schwebender Footer ohne zusätzliche Höhe */
.app-inline-footer{
  position:absolute;
  bottom:3px;
  left:0;
  right:0;

  text-align:center;

  font-size:10px;
  letter-spacing:.04em;
  line-height:1.1;

  opacity:.42;

  color:var(--app-text-color,#555);

  user-select:none;
  pointer-events:none;
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
    text-align:center;
  }

  .navbar .navbar-menu{
    align-items:center;
  }

  .navbar .navbar-actions{
    justify-content:center;
  }

}
</style>
