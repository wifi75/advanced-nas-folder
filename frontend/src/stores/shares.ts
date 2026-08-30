/** Stato delle cartelle pubblicate. */

import { defineStore } from 'pinia'
import { ref } from 'vue'

import { ApiError } from '@/api/client'
import {
  sharesApi,
  type Livello,
  type NuovaShare,
  type Share,
  type ShareDettaglio,
  type Visibilita,
} from '@/api/shares'

function messaggio(e: unknown): string {
  return e instanceof ApiError ? e.message : 'Errore imprevisto.'
}

export const useSharesStore = defineStore('shares', () => {
  const elenco = ref<Share[]>([])
  const aperta = ref<ShareDettaglio | null>(null)
  const caricamento = ref(false)
  const errore = ref('')

  async function carica(): Promise<void> {
    caricamento.value = true
    errore.value = ''
    try {
      elenco.value = await sharesApi.elenca()
    } catch (e) {
      errore.value = messaggio(e)
    } finally {
      caricamento.value = false
    }
  }

  async function apri(id: number): Promise<void> {
    errore.value = ''
    try {
      aperta.value = await sharesApi.dettaglio(id)
    } catch (e) {
      errore.value = messaggio(e)
    }
  }

  function chiudi(): void {
    aperta.value = null
  }

  async function crea(dati: NuovaShare): Promise<boolean> {
    errore.value = ''
    try {
      await sharesApi.crea(dati)
      await carica()
      return true
    } catch (e) {
      errore.value = messaggio(e)
      return false
    }
  }

  /** Restituisce l'esito: chi chiama deve poter distinguere riuscita da errore. */
  async function modifica(id: number, dati: Partial<NuovaShare>): Promise<boolean> {
    errore.value = ''
    try {
      await sharesApi.modifica(id, dati)
      await carica()
      if (aperta.value?.id === id) await apri(id)
      return true
    } catch (e) {
      errore.value = messaggio(e)
      return false
    }
  }

  async function elimina(id: number): Promise<boolean> {
    errore.value = ''
    try {
      await sharesApi.elimina(id)
      if (aperta.value?.id === id) aperta.value = null
      await carica()
      return true
    } catch (e) {
      errore.value = messaggio(e)
      return false
    }
  }

  async function aggiungiRegola(
    id: number,
    percorso: string,
    visibilita: Visibilita,
    password?: string,
  ): Promise<boolean> {
    errore.value = ''
    try {
      const dati: { path_prefix: string; visibility: Visibilita; password?: string } = {
        path_prefix: percorso,
        visibility: visibilita,
      }
      if (password) dati.password = password
      await sharesApi.aggiungiRegola(id, dati)
      await apri(id)
      return true
    } catch (e) {
      errore.value = messaggio(e)
      return false
    }
  }

  async function togliRegola(id: number, regolaId: number): Promise<void> {
    errore.value = ''
    try {
      await sharesApi.togliRegola(id, regolaId)
      await apri(id)
    } catch (e) {
      errore.value = messaggio(e)
    }
  }

  async function assegnaPermesso(
    id: number,
    utente: number,
    percorso: string,
    livello: Livello,
  ): Promise<boolean> {
    errore.value = ''
    try {
      await sharesApi.assegnaPermesso(id, { user_id: utente, path_prefix: percorso, livello })
      await apri(id)
      return true
    } catch (e) {
      errore.value = messaggio(e)
      return false
    }
  }

  async function togliPermesso(id: number, permessoId: number): Promise<void> {
    errore.value = ''
    try {
      await sharesApi.togliPermesso(id, permessoId)
      await apri(id)
    } catch (e) {
      errore.value = messaggio(e)
    }
  }

  return {
    elenco,
    aperta,
    caricamento,
    errore,
    carica,
    apri,
    chiudi,
    crea,
    modifica,
    elimina,
    aggiungiRegola,
    togliRegola,
    assegnaPermesso,
    togliPermesso,
  }
})
