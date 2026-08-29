/**
 * Stato applicativo: versione, attribuzione e stato del servizio.
 *
 * Versione e autore arrivano dall'API e non sono scritti nel frontend: esiste
 * una sola sorgente di verita, `backend/app/core/version.py`.
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api } from '@/api/client'

interface Health {
  status: string
  name: string
  version: string
  author: string
}

export const useAppStore = defineStore('app', () => {
  const name = ref('Advanced NAS Folder')
  const version = ref('')
  const author = ref('')
  const online = ref(false)
  const caricato = ref(false)

  /** Riga di attribuzione, su un'unica riga come da standard di progetto. */
  const footer = computed(() =>
    version.value && author.value
      ? `v${version.value} — Ideato e sviluppato da ${author.value}`
      : '',
  )

  async function carica(): Promise<void> {
    try {
      const health = await api.get<Health>('/health')
      name.value = health.name
      version.value = health.version
      author.value = health.author
      online.value = health.status === 'ok'
    } catch {
      // Il pannello resta usabile anche senza: mostrera il piede vuoto invece
      // di bloccarsi su una schermata di errore.
      online.value = false
    } finally {
      caricato.value = true
    }
  }

  return { name, version, author, online, caricato, footer, carica }
})
