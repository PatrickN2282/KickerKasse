import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/',
    name: 'Kasse',
    component: () => import('@/views/kasse/Kasse.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/Admin.vue'),
    meta: { requiresAuth: true, allowedRoles: ['ADMIN', 'KASSENMITGLIED'] },
    redirect: '/admin/members',
    children: [
      {
        path: 'members',
        name: 'AdminMembers',
        component: () => import('@/views/admin/Members.vue'),
        meta: { requiresAuth: true, allowedRoles: ['ADMIN', 'KASSENMITGLIED'] },
      },
      {
        path: 'products',
        name: 'AdminProducts',
        component: () => import('@/views/admin/Products.vue'),
        meta: { requiresAuth: true, allowedRoles: ['ADMIN'] },
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/admin/Categories.vue'),
        meta: { requiresAuth: true, allowedRoles: ['ADMIN'] },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
        meta: { requiresAuth: true, allowedRoles: ['ADMIN'] },
      },
      {
        path: 'vouchers',
        name: 'AdminVouchers',
        component: () => import('@/views/admin/Vouchers.vue'),
        meta: { requiresAuth: true, allowedRoles: ['ADMIN'] },
      },
      {
        path: 'finance',
        name: 'AdminFinance',
        component: () => import('@/views/admin/Finance.vue'),
        meta: { requiresAuth: true, allowedRoles: ['ADMIN', 'KASSENMITGLIED'] },
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/Settings.vue'),
        meta: { requiresAuth: true, allowedRoles: ['ADMIN'] },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

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
