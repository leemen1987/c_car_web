import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/confirm/:token', name: 'ConfirmSchedule', component: () => import('../views/ConfirmSchedule.vue') },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/tasks',
    children: [
      { path: 'tasks', name: 'Tasks', component: () => import('../views/TaskManagement.vue'), meta: { permission: 'task' } },
      { path: 'permissions', name: 'Permissions', component: () => import('../views/PermissionControl.vue'), meta: { permission: 'permission' } },
      { path: 'reports', name: 'Reports', component: () => import('../views/ReportManagement.vue'), meta: { permission: 'report' } },
      { path: 'drivers', name: 'Drivers', component: () => import('../views/DriverManagement.vue'), meta: { permission: 'driver' } },
      { path: 'vehicles', name: 'Vehicles', component: () => import('../views/VehicleManagement.vue'), meta: { permission: 'vehicle' } },
      { path: 'labor-rates', name: 'LaborRates', component: () => import('../views/LaborRateManagement.vue'), meta: { permission: 'labor_rate' } },
      { path: 'clients', name: 'Clients', component: () => import('../views/ClientManagement.vue'), meta: { permission: 'client' } },
      { path: 'confirmations', name: 'Confirmations', component: () => import('../views/ConfirmationManagement.vue'), meta: { permission: 'task' } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  // 公开页面：登录页、确认页
  const publicPages = ['/login', '/confirm']
  const isPublicPage = publicPages.some(page => to.path.startsWith(page))

  if (!isPublicPage) {
    const user = JSON.parse(localStorage.getItem('user') || 'null')
    if (!user) {
      next('/login')
      return
    }
  }
  next()
})

export default router
