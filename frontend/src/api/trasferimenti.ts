/** Monitoraggio dei trasferimenti. */

import { api, BASE, tokenCorrente } from '@/api/client'

export interface Trasferimento {
  id: number
  kind: 'download' | 'upload'
  status: 'in_corso' | 'completato' | 'interrotto' | 'fallito'
  share_id: number | null
  user_id: number | null
  path: string
  size: number | null
  /**
   * Byte davvero arrivati. Resta vuoto finché il web server non li ha scritti
   * nel suo log: la consegna è delegata a lui, e l'applicazione non li vede
   * passare. Un numero inventato sarebbe peggio di uno assente.
   */
  bytes_transferred: number | null
  client_ip: string | null
  is_resumed: boolean
  started_at: string
  finished_at: string | null
}

export const trasferimentiApi = {
  elenca: (limite = 100) => api.get<Trasferimento[]>(`/trasferimenti?limite=${limite}`),
}

/**
 * Eventi dal vivo, via SSE.
 *
 * `EventSource` non permette di aggiungere intestazioni, quindi non può
 * portare il token: si usa `fetch` e si legge il corpo man mano che arriva.
 * È lo stesso protocollo, senza il vincolo.
 */
export async function seguiTrasferimenti(
  suEvento: (t: Record<string, unknown>) => void,
  segnale: AbortSignal,
): Promise<void> {
  const token = tokenCorrente()
  const risposta = await fetch(`${BASE}/trasferimenti/flusso`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    signal: segnale,
  })
  if (!risposta.ok || risposta.body === null) throw new Error(`Errore ${risposta.status}`)

  const lettore = risposta.body.getReader()
  const decodificatore = new TextDecoder()
  let resto = ''

  while (!segnale.aborted) {
    const { done, value } = await lettore.read()
    if (done) break

    resto += decodificatore.decode(value, { stream: true })
    // Gli eventi SSE sono separati da una riga vuota: si elabora solo ciò che
    // è arrivato per intero, il resto aspetta il pezzo successivo.
    const pezzi = resto.split('\n\n')
    resto = pezzi.pop() ?? ''

    for (const pezzo of pezzi) {
      const riga = pezzo.split('\n').find((r) => r.startsWith('data:'))
      if (riga) suEvento(JSON.parse(riga.slice(5).trim()))
    }
  }
}
