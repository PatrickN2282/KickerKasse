import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { KASSE_ROUTE_NAME, SESSION_RELOAD_FLAG_KEY } from '@/constants'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
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
        path: 'settings',
        redirect: '/admin/config',
      },
      {
        path: 'data-maintenance',
        redirect: '/admin/config',
      },
      {
        path: 'ext-settings',
        redirect: '/admin/config',
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
