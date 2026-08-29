import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from '@/App.vue'
import router from '@/router'
import { useAppStore } from '@/stores/app'

import '@/assets/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// Versione e attribuzione arrivano dall'API: caricate una volta all'avvio,
// prima del montaggio, cosi il piede di pagina non appare a scatti.
await useAppStore().carica()

app.mount('#app')
