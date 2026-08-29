import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { titolo: 'Pannello' },
  },
  {
    path: '/accedi',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { titolo: 'Accedi', pubblica: true },
  },
  {
    path: '/:percorso(.*)*',
    name: 'non-trovata',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { titolo: 'Pagina non trovata', pubblica: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  const titolo = to.meta.titolo
  document.title = typeof titolo === 'string' ? `${titolo} · Advanced NAS Folder` : 'Advanced NAS Folder'
})

export default router
