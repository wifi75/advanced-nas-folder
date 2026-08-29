import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { titolo: 'menu.stato' },
  },
  {
    path: '/condivisioni',
    name: 'mounts',
    component: () => import('@/views/MountsView.vue'),
    meta: { titolo: 'menu.condivisioni' },
  },
  {
    path: '/pubblicazioni',
    name: 'shares',
    component: () => import('@/views/SharesView.vue'),
    meta: { titolo: 'menu.pubblicazioni' },
  },
  {
    path: '/accedi',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { titolo: 'accesso.titolo', pubblica: true },
  },
  {
    path: '/:percorso(.*)*',
    name: 'non-trovata',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { titolo: 'nonTrovata.titolo', pubblica: true },
  },
]

const router = createRouter({
  // Il pannello è servito sotto un prefisso (`/pannello/`), non alla radice
  // del sito: senza passarlo qui, ogni indirizzo interno punterebbe fuori
  // dall'applicazione e il web server risponderebbe con un 404.
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (!to.meta.pubblica && !auth.autenticato) {
    // Ricorda dove voleva andare, per riportarcelo dopo l'accesso.
    return { name: 'login', query: to.fullPath === '/' ? {} : { avanti: to.fullPath } }
  }
  if (to.name === 'login' && auth.autenticato) {
    return { name: 'home' }
  }
  return true
})

/**
 * Aggiorna il titolo della scheda.
 *
 * Esportata perché non basta chiamarla alla navigazione: cambiando lingua la
 * rotta non cambia, e senza una nuova chiamata il titolo resterebbe nella
 * lingua precedente.
 */
export function aggiornaTitolo(chiave: unknown): void {
  document.title =
    typeof chiave === 'string'
      ? `${i18n.global.t(chiave)} · Advanced NAS Folder`
      : 'Advanced NAS Folder'
}

router.afterEach((to) => aggiornaTitolo(to.meta.titolo))

export default router
