import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from '@/App.vue'
import router from '@/router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

import '@/assets/main.css'

const app = createApp(App)
app.use(createPinia())

// La sessione va ripristinata PRIMA del router: altrimenti la prima guardia
// gira senza utente e rimanda all'accesso chi era gia autenticato.
await Promise.all([useAppStore().carica(), useAuthStore().ripristina()])

app.use(router)
app.mount('#app')
