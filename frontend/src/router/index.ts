import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: 'SlimCheck - 智能卡路里分析' }
  },
  {
    path: '/analyze',
    name: 'Analyze',
    component: () => import('@/views/Analyze.vue'),
    meta: { title: '流式分析 - SlimCheck' }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/views/Users.vue'),
    meta: { title: '用户管理 - SlimCheck' }
  },
  {
    path: '/requests',
    name: 'Requests',
    component: () => import('@/views/Requests.vue'),
    meta: { title: '请求管理 - SlimCheck' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

router.beforeEach((to, from, next) => {
  document.title = (to.meta.title as string) || 'SlimCheck'
  next()
})

export default router