import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      // 'prompt' e non 'autoUpdate': su un pannello di amministrazione il
      // codice non deve cambiare sotto le mani di chi ci sta lavorando. Si
      // avvisa e si aggiorna quando la persona è pronta.
      registerType: 'prompt',
      includeAssets: ['apple-touch-icon.png'],
      manifest: {
        name: 'Advanced NAS Folder',
        short_name: 'NAS Folder',
        // Senza, il plugin dichiara 'en' mentre la descrizione è in italiano.
        lang: 'it',
        dir: 'ltr',
        description:
          'Monta condivisioni NFS, pubblica cartelle con permessi per sottocartella, gestisci i file.',
        start_url: '/pannello/',
        scope: '/pannello/',
        display: 'standalone',
        orientation: 'any',
        background_color: '#f4f6f9',
        theme_color: '#1d5fa8',
        icons: [
          { src: 'icona-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icona-512.png', sizes: '512x512', type: 'image/png' },
          // "maskable" ha aria attorno al simbolo: i sistemi ritagliano
          // l'icona a piacere, e senza margine il disegno verrebbe tagliato.
          {
            src: 'icona-maskable-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,woff2,png,svg}'],
        // Applicazione a pagina singola: gli indirizzi interni non
        // corrispondono a file, e vanno serviti dall'index.
        navigateFallback: '/pannello/index.html',
        // Le chiamate all'API non vanno MAI servite dalla cache: mostrerebbero
        // uno stato del sistema che non è più quello reale, che su un pannello
        // che monta filesystem è peggio di un errore di rete.
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [
          {
            urlPattern: /^\/api\//,
            handler: 'NetworkOnly',
          },
        ],
        cleanupOutdatedCaches: true,
      },
      devOptions: {
        // In sviluppo il service worker resta spento: intercetterebbe le
        // richieste rendendo incomprensibile il comportamento a caldo.
        enabled: false,
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  base: '/pannello/',
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
  preview: {
    port: 5196,
    host: true,
    // Stesso inoltro dello sviluppo: senza, provare il build significherebbe
    // provarlo senza API, cioe non provarlo.
    proxy: {
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
