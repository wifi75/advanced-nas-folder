/** Stato dei mount NFS. */

import { defineStore } from 'pinia'
import { ref } from 'vue'

import { ApiError } from '@/api/client'
import { mountsApi, type Mount, type MountDettaglio, type NuovoMount } from '@/api/mounts'

function messaggio(e: unknown): string {
  if (e instanceof ApiError) return e.message
  return 'Errore imprevisto.'
}

export const useMountsStore = defineStore('mounts', () => {
  const elenco = ref<Mount[]>([])
  const dettagli = ref<Record<number, MountDettaglio>>({})
  const caricamento = ref(false)
  const errore = ref('')
  /** Id dei mount su cui è in corso un'operazione: disabilita i pulsanti giusti. */
  const inCorso = ref<Set<number>>(new Set())

  function segna(id: number, attivo: boolean): void {
    const copia = new Set(inCorso.value)
    if (attivo) copia.add(id)
    else copia.delete(id)
    inCorso.value = copia
  }

  async function carica(): Promise<void> {
    caricamento.value = true
    errore.value = ''
    try {
      elenco.value = await mountsApi.elenca()
    } catch (e) {
      errore.value = messaggio(e)
    } finally {
      caricamento.value = false
    }
  }

  function aggiorna(dettaglio: MountDettaglio): void {
    dettagli.value = { ...dettagli.value, [dettaglio.id]: dettaglio }
    const indice = elenco.value.findIndex((m) => m.id === dettaglio.id)
    if (indice >= 0) elenco.value[indice] = dettaglio
    else elenco.value = [...elenco.value, dettaglio]
  }

  async function dettaglio(id: number): Promise<void> {
    segna(id, true)
    try {
      aggiorna(await mountsApi.dettaglio(id))
    } catch (e) {
      errore.value = messaggio(e)
    } finally {
      segna(id, false)
    }
  }

  async function crea(dati: NuovoMount): Promise<boolean> {
    errore.value = ''
    try {
      aggiorna(await mountsApi.crea(dati))
      return true
    } catch (e) {
      errore.value = messaggio(e)
      return false
    }
  }

  async function avvia(id: number): Promise<void> {
    segna(id, true)
    errore.value = ''
    try {
      aggiorna(await mountsApi.avvia(id))
    } catch (e) {
      errore.value = messaggio(e)
      // Lo stato mostrato potrebbe non riflettere piu la realta: si rilegge.
      await dettaglio(id)
    } finally {
      segna(id, false)
    }
  }

  async function ferma(id: number): Promise<void> {
    segna(id, true)
    errore.value = ''
    try {
      aggiorna(await mountsApi.ferma(id))
    } catch (e) {
      errore.value = messaggio(e)
    } finally {
      segna(id, false)
    }
  }

  async function elimina(id: number): Promise<boolean> {
    segna(id, true)
    errore.value = ''
    try {
      await mountsApi.elimina(id)
      elenco.value = elenco.value.filter((m) => m.id !== id)
      return true
    } catch (e) {
      errore.value = messaggio(e)
      return false
    } finally {
      segna(id, false)
    }
  }

  return {
    elenco,
    dettagli,
    caricamento,
    errore,
    inCorso,
    carica,
    dettaglio,
    crea,
    avvia,
    ferma,
    elimina,
  }
})
