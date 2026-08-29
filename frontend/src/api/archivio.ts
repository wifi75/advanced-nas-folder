/**
 * Consultazione e download delle cartelle pubblicate.
 *
 * A differenza del resto dell'API, questi endpoint rispondono anche senza
 * token: una cartella pubblicata come pubblica dev'essere raggiungibile da
 * chiunque.
 */

import { api, BASE } from '@/api/client'
import type { Visibilita } from '@/api/shares'

export interface Voce {
  nome: string
  percorso: string
  cartella: boolean
  /** Assente per le cartelle: calcolarne la dimensione costerebbe quanto l'elenco. */
  dimensione: number | null
  modificato: string | null
}

export interface Contenuto {
  slug: string
  label: string
  descrizione: string | null
  percorso: string
  /** Nome e percorso di ogni cartella attraversata. */
  briciole: [string, string][]
  voci: Voce[]
  scrittura: boolean
  visibilita: Visibilita
}

interface Gettone {
  gettone: string
  valido_secondi: number
}

export const archivioApi = {
  contenuto: (slug: string, percorso = '', password?: string) => {
    const q = new URLSearchParams({ percorso })
    if (password) q.set('password', password)
    return api.get<Contenuto>(`/archivio/${encodeURIComponent(slug)}?${q}`)
  },

  gettone: (slug: string, percorso: string, password?: string) =>
    api.post<Gettone>(`/archivio/${encodeURIComponent(slug)}/gettone`, {
      percorso,
      password: password ?? null,
    }),
}

/**
 * Indirizzo da cui scaricare un file, autorizzato per pochi minuti.
 *
 * Il download deve essere una navigazione del browser e non una `fetch`:
 * scaricare via `fetch` significherebbe tenere l'intero file in memoria e
 * perdere sia la barra di avanzamento del browser sia la ripresa di un
 * trasferimento interrotto. Una navigazione però non porta intestazioni, e
 * quindi nemmeno il token di sessione: da qui il gettone a vita breve.
 */
export async function indirizzoDownload(
  slug: string,
  percorso: string,
  password?: string,
): Promise<string> {
  const { gettone } = await archivioApi.gettone(slug, percorso, password)
  const q = new URLSearchParams({ percorso, g: gettone })
  return `${BASE}/archivio/${encodeURIComponent(slug)}/file?${q}`
}

/**
 * Cartella aperta da un link di condivisione.
 *
 * Il token è l'autorizzazione: non serve alcun accesso al pannello.
 */
export const linkApi = {
  contenuto: (token: string, percorso = '', password?: string) => {
    const q = new URLSearchParams({ percorso })
    if (password) q.set('password', password)
    return api.get<Contenuto>(`/link/${encodeURIComponent(token)}?${q}`)
  },
}

/**
 * Indirizzo da cui scaricare un file passando dal link.
 *
 * Qui non serve un gettone separato: il token nell'indirizzo è già
 * l'autorizzazione, e vive nella pagina che l'utente sta guardando.
 */
export function indirizzoDownloadLink(
  token: string,
  percorso: string,
  password?: string,
): string {
  const q = new URLSearchParams({ percorso })
  if (password) q.set('password', password)
  return `${BASE}/link/${encodeURIComponent(token)}/file?${q}`
}
