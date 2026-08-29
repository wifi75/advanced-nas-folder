import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from '@/App.vue'
import { i18n, linguaIniziale, ricordaLingua } from '@/i18n'
import router from '@/router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useImpostazioniStore } from '@/stores/impostazioni'

import '@/assets/main.css'

ricordaLingua(linguaIniziale())

const app = createApp(App)
app.use(createPinia())
app.use(i18n)

// La sessione va ripristinata PRIMA del router: altrimenti la prima guardia
// gira senza utente e rimanda all'accesso chi era già autenticato.
await Promise.all([
  useAppStore().carica(),
  useAuthStore().ripristina(),
  // Il marchio serve gia' alla pagina di accesso: caricarlo dopo la farebbe
  // comparire con il nome predefinito e poi cambiare sotto gli occhi.
  useImpostazioniStore().carica(),
])

app.use(router)
app.mount('#app')
