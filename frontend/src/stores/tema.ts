/**
 * Tema dell'interfaccia: chiaro, scuro o automatico.
 *
 * Gli stati sono tre, non due. "Automatico" non è un terzo colore: è l'assenza
 * di scelta, e si esprime **non marcando** l'attributo sulla radice, così la
 * pagina segue `prefers-color-scheme` del sistema. Marcare qualcosa anche per
 * l'automatico costringerebbe a duplicare la logica del sistema operativo.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const TEMI = ['chiaro', 'auto', 'scuro'] as const
export type Tema = (typeof TEMI)[number]

const CHIAVE = 'anf.tema'

function salvato(): Tema {
  try {
    const valore = localStorage.getItem(CHIAVE)
    return TEMI.includes(valore as Tema) ? (valore as Tema) : 'auto'
  } catch {
    return 'auto'
  }
}

function applica(tema: Tema): void {
  const radice = document.documentElement
  if (tema === 'auto') radice.removeAttribute('data-tema')
  else radice.setAttribute('data-tema', tema)
}

export const useTemaStore = defineStore('tema', () => {
  const tema = ref<Tema>(salvato())
  applica(tema.value)

  function imposta(nuovo: Tema): void {
    tema.value = nuovo
    applica(nuovo)
    try {
      localStorage.setItem(CHIAVE, nuovo)
    } catch {
      /* archivio non disponibile: la scelta vale per questa sessione */
    }
  }

  return { tema, imposta }
})
