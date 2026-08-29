import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // Ascolta su tutte le interfacce, non solo su localhost: serve a provare il
    // pannello da un altro dispositivo della rete, per esempio un telefono.
    host: true,
    // Vite rifiuta le richieste con un Host che non conosce, come difesa dal
    // rebinding DNS. Arrivando da un indirizzo IP della LAN servono queste
    // eccezioni, altrimenti la pagina risponde "host non consentito".
    allowedHosts: ['localhost', '.local', '.lan'],
    proxy: {
      // Il frontend gira per conto suo e l'API sta altrove: il proxy evita di
      // dover gestire CORS. Punta a 127.0.0.1 perché gira sulla stessa
      // macchina del backend, anche quando il browser arriva dalla rete.
      '/api': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
    },
  },
  build: {
    // La CI produce questa cartella e la allega alla release: il server di
    // destinazione non compila mai nulla.
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
})
