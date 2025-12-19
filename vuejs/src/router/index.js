import { createRouter, createWebHistory } from 'vue-router'
import TopMenu from '../layouts/top-menu/Main.vue'
import Dashboard from '../views/dashboard/Main.vue'
import Login from '../views/login/Main.vue'
import ErrorPage from '../views/error-page/Main.vue'

const routes = [
  {
    path: '/',
    component: TopMenu,
    children: [
      {
        path: '/',
        name: 'dashboard',
        component: Dashboard,
        meta: { internal: true }
      },
      {
        path: 'meter/list',
        name: 'meter-list',
        component: () => import('../views/meter/meter-list/Main.vue'),
        meta: { internal: true }
      },
      {
        path: 'meter/detail/:pk',
        name: 'meter-detail',
        component: () => import('../views/meter/meter-detail/Main.vue'),
        meta: { internal: true }
      },
      {
        path: 'reading/list',
        name: 'reading-list',
        component: () => import('../views/reading/reading-list/Main.vue'),
        meta: { internal: true }
      },
      {
        path: 'alert/list',
        name: 'alert-list',
        component: () => import('../views/alert/alert-list/Main.vue'),
        meta: { internal: true }
      },
      {
        path: 'user/list',
        name: 'user-list',
        component: () => import('../views/user/user-list/Main.vue'),
        meta: { internal: true }
      },
      {
        path: 'user/detail/:pk',
        name: 'user-detail',
        component: () => import('../views/user/user-detail/Main.vue'),
        meta: { internal: true }
      },
    ]
  },
  {
    path: '/login',
    name: 'login',
    component: Login
  },
  {
    path: '/error-page',
    name: 'error-page',
    component: ErrorPage
  },
  {
    path: '/:pathMatch(.*)*',
    component: ErrorPage
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { left: 0, top: 0 }
  }
})

import store from '@/store'

router.beforeEach(async (to, from, next) => {
  const publicPages = ['/login', '/error-page']
  const authRequired = !publicPages.includes(to.path)
  const token = localStorage.getItem('token')

  if (authRequired && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router