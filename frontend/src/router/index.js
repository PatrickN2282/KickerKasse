import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { SESSION_RELOAD_FLAG_KEY } from '@/constants'

const LAYOUT_STORAGE_KEY = 'kasseLayout'

function getKasseComponent() {
  const layout = localStorage.getItem(LAYOUT_STORAGE_KEY) || 'Kasse'
  if (layout === 'Kasse') {
    return () => import('@/views/kasse/Kasse.vue')
  }
  // Dynamically load alternate layouts (e.g. Kasse2.vue, Kasse3.vue)
  const allLayouts = import.meta.glob('@/views/kasse/Kasse*.vue')
  const key = `/src/views/kasse/${layout}.vue`
  if (allLayouts[key]) {
    return allLayouts[key]
  }
  // Fallback to default
  return () => import('@/views/kasse/Kasse.vue')
}

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/',
    name: 'Kasse',
    component: getKasseComponent(),
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
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/Settings.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN'] },
      },
      {
        path: 'data-maintenance',
        name: 'AdminDataMaintenance',
        component: () => import('@/views/admin/DataMaintenance.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN', 'ADMIN'] },
      },
      {
        path: 'ext-settings',
        name: 'AdminExtSettings',
        component: () => import('@/views/admin/ExtSettings.vue'),
        meta: { requiresAuth: true, allowedRoles: ['TOP_ADMIN'] },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let sessionHandled = false

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (!sessionHandled) {
    sessionHandled = true
    const wasReloading = sessionStorage.getItem(SESSION_RELOAD_FLAG_KEY)
    if (wasReloading) {
      sessionStorage.removeItem(SESSION_RELOAD_FLAG_KEY)
    } else {
      await authStore.logout()
    }
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
