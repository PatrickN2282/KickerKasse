import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { INITIAL_SETUP_LOCK_KEY, KASSE_ROUTE_NAME, SESSION_RELOAD_FLAG_KEY } from '@/constants'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    // Anforderung 1: dedizierte Passwort-Reset-Seite, die über den Link aus der
    // Reset-E-Mail des TopAdmin-Self-Service-Flows erreicht wird.
    path: '/password-reset/:token',
    name: 'PasswordReset',
    component: () => import('@/views/PasswordResetView.vue'),
  },
  {
    path: '/',
    name: KASSE_ROUTE_NAME,
    component: () => import('@/views/kasse/KasseLayoutHost.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/Admin.vue'),
    meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
    redirect: '/admin/members',
    children: [
      {
        path: 'members',
        name: 'AdminMembers',
        component: () => import('@/views/admin/Members.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
      },
      {
        path: 'products',
        name: 'AdminProducts',
        component: () => import('@/views/admin/Products.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/admin/Categories.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN'] },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN'] },
      },
      {
        path: 'vouchers',
        name: 'AdminVouchers',
        component: () => import('@/views/admin/Vouchers.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
      },
      {
        path: 'finance',
        name: 'AdminFinance',
        component: () => import('@/views/admin/Finance.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
      },
      {
        path: 'corrections',
        name: 'AdminCorrections',
        redirect: '/admin/finance?tab=corrections',
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN'] },
      },
      {
        path: 'config',
        name: 'AdminConfig',
        component: () => import('@/views/admin/AdminConfig.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN'] },
      },
      {
        path: 'guestlist',
        name: 'AdminGuestList',
        component: () => import('@/views/admin/GuestList.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
      },
      {
        path: 'material-transactions',
        name: 'AdminMaterialTransactions',
        component: () => import('@/views/admin/MaterialTransactions.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN', 'MANAGER'] },
      },
      {
        path: 'settings',
        redirect: '/admin/config?section=design',
      },
      {
        path: 'data-maintenance',
        redirect: '/admin/config?section=datamaintenance',
      },
      {
        path: 'ext-settings',
        redirect: '/admin/config?section=extsettings',
      },
      {
        path: 'email-settings',
        redirect: '/admin/config?section=emailsettings',
      },
      {
        path: 'audit-log',
        redirect: '/admin/config?section=auditlog',
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let sessionChecked = false
let setupStatusChecked = false

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (!setupStatusChecked) {
    setupStatusChecked = true
    const setupStatus = await authStore.fetchSetupStatus()
    if (setupStatus?.setup_required) {
      sessionStorage.setItem(INITIAL_SETUP_LOCK_KEY, '1')
      authStore.clearClientSession()
    } else if (setupStatus?.top_admin_exists) {
      sessionStorage.removeItem(INITIAL_SETUP_LOCK_KEY)
    }
  }

  const setupLockActive = authStore.setupRequired
    || sessionStorage.getItem(INITIAL_SETUP_LOCK_KEY) === '1'

  if (setupLockActive && to.path !== '/login') {
    next('/login')
    return
  }

  if (!sessionChecked) {
    sessionChecked = true
    sessionStorage.removeItem(SESSION_RELOAD_FLAG_KEY)
    await authStore.checkAuth()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    await authStore.checkAuth()

    if (!authStore.isAuthenticated) {
      next('/login')
      return
    }
  }

  if (to.meta.allowedRoles?.length && !to.meta.allowedRoles.includes(authStore.role)) {
    next('/')
    return
  }

  next()
})

export default router
