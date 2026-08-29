/**
 * Caricamento di un file a blocchi, con ripresa.
 *
 * Il file viene inviato a pezzi invece che in una richiesta sola: su una rete
 * domestica un file da qualche gigabyte non arriva al primo tentativo, e
 * ricominciare da capo a ogni interruzione renderebbe la funzione inutile.
 *
 * Lo stato della ripresa lo tiene il server nel file parziale: qui non si
 * ricorda nulla fra una sessione e l'altra, si chiede.
 */

import { api, BASE } from '@/api/client'

/** 4 MB: abbastanza grande da non moltiplicare le richieste, abbastanza piccolo
 *  da non perdere molto quando la rete cade a metà di un blocco. */
export const BLOCCO = 4 * 1024 * 1024

export interface StatoCaricamento {
  nome: string
  /** Byte già arrivati. Zero significa che si parte dall'inizio. */
  ricevuti: number
  /** Vero se esiste già un file con quel nome: completare fallirebbe. */
  gia_presente: boolean
}

export const caricamentoApi = {
  stato: (slug: string, percorso: string, nome: string) => {
    const q = new URLSearchParams({ percorso, nome })
    return api.get<StatoCaricamento>(`/archivio/${encodeURIComponent(slug)}/carica/stato?${q}`)
  },

  completa: (slug: string, percorso: string, nome: string, dimensione: number) =>
    api.post<{ percorso: string }>(`/archivio/${encodeURIComponent(slug)}/carica/completa`, {
      percorso,
      nome,
      dimensione,
    }),

  annulla: (slug: string, percorso: string, nome: string) =>
    api.post<void>(`/archivio/${encodeURIComponent(slug)}/carica/annulla`, { percorso, nome }),
}

/**
 * Invia un blocco grezzo.
 *
 * Non passa dal client generico perché il corpo non è JSON: incapsularlo
 * costringerebbe a ricopiare gli stessi byte per nulla.
 */
export async function inviaBlocco(
  slug: string,
  percorso: string,
  nome: string,
  blocco: Blob,
  offset: number,
  token: string | null,
): Promise<number> {
  const q = new URLSearchParams({ percorso, nome, offset: String(offset) })
  const intestazioni: Record<string, string> = { 'Content-Type': 'application/octet-stream' }
  if (token) intestazioni.Authorization = `Bearer ${token}`

  const risposta = await fetch(`${BASE}/archivio/${encodeURIComponent(slug)}/carica?${q}`, {
    method: 'PUT',
    headers: intestazioni,
    body: blocco,
  })

  if (!risposta.ok) {
    const dettaglio = await risposta.json().catch(() => null)
    throw new Error(dettaglio?.detail ?? `Errore ${risposta.status}`)
  }
  return (await risposta.json()).ricevuti as number
}
