/**
 * Traduzioni del pannello.
 *
 * L'italiano è la lingua di riferimento: le chiavi si scrivono lì per prime e
 * l'inglese le rispecchia una a una. Il tipo `MessaggiIt` fa in modo che una
 * chiave dimenticata in inglese diventi un errore di compilazione invece di
 * una stringa mancante scoperta a schermo.
 */

import { createI18n } from 'vue-i18n'

import en from '@/i18n/en'
import it from '@/i18n/it'

export const LINGUE = [
  { codice: 'it', nome: 'Italiano' },
  { codice: 'en', nome: 'English' },
] as const

export type Lingua = (typeof LINGUE)[number]['codice']

type MessaggiIt = typeof it

const CHIAVE = 'anf.lingua'
const PREDEFINITA: Lingua = 'it'

function linguaSalvata(): Lingua | null {
  try {
    const valore = localStorage.getItem(CHIAVE)
    return LINGUE.some((l) => l.codice === valore) ? (valore as Lingua) : null
  } catch {
    return null
  }
}

function linguaDelBrowser(): Lingua {
  const preferite = navigator.languages ?? [navigator.language]
  for (const codice of preferite) {
    const breve = codice.slice(0, 2).toLowerCase()
    if (LINGUE.some((l) => l.codice === breve)) return breve as Lingua
  }
  return PREDEFINITA
}

/** Lingua iniziale: scelta dell'utente, altrimenti quella del browser. */
export function linguaIniziale(): Lingua {
  return linguaSalvata() ?? linguaDelBrowser()
}

export function ricordaLingua(lingua: Lingua): void {
  try {
    localStorage.setItem(CHIAVE, lingua)
  } catch {
    /* archivio non disponibile: la scelta vale per questa sessione */
  }
  document.documentElement.lang = lingua
}

// Il terzo parametro di tipo `false` dichiara la modalità composizione: senza,
// `locale` risulta una stringa invece di un riferimento scrivibile e non si
// può cambiare lingua a runtime.
export const i18n = createI18n<[MessaggiIt], Lingua, false>({
  legacy: false,
  locale: linguaIniziale(),
  fallbackLocale: PREDEFINITA,
  messages: { it, en },
})

export function cambiaLingua(lingua: Lingua): void {
  i18n.global.locale.value = lingua
  ricordaLingua(lingua)
}
