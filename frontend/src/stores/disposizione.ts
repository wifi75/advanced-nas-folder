/**
 * Disposizione della pagina "File": quale delle 5 intestazioni mostrare.
 *
 * Stessa logica di `tema.ts`: è una preferenza di lettura di chi guarda,
 * non una proprietà della cartella, quindi resta nel browser e non tocca il
 * server. Vale sia per chi amministra sia per chi apre un link pubblico —
 * questa pagina non ha mai la barra laterale del pannello (vedi
 * `router/index.ts`, `meta.senzaMenu`), quindi non c'è un posto comune dove
 * mettere la scelta se non dentro la pagina stessa.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const DISPOSIZIONI = ['unificata', 'laterale', 'riepilogo', 'tabella', 'card'] as const
export type Disposizione = (typeof DISPOSIZIONI)[number]

const CHIAVE = 'anf.archivio.disposizione'

function salvata(): Disposizione {
  try {
    const valore = localStorage.getItem(CHIAVE)
    return (DISPOSIZIONI as readonly string[]).includes(valore ?? '')
      ? (valore as Disposizione)
      : 'unificata'
  } catch {
    return 'unificata'
  }
}

export const useDisposizioneStore = defineStore('disposizione', () => {
  const disposizione = ref<Disposizione>(salvata())

  function imposta(nuova: Disposizione): void {
    disposizione.value = nuova
    try {
      localStorage.setItem(CHIAVE, nuova)
    } catch {
      /* archivio non disponibile: la scelta vale per questa sessione */
    }
  }

  return { disposizione, imposta }
})
