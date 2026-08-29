/**
 * Client HTTP verso l'API.
 *
 * Un solo punto di uscita verso la rete: cosi la gestione degli errori e
 * l'aggiunta del token restano in un posto solo invece di essere sparse nei
 * componenti.
 */

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const BASE = '/api/v1'

let authToken: string | null = null

export function setAuthToken(token: string | null): void {
  authToken = token
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Accept')) headers.set('Accept', 'application/json')
  if (authToken) headers.set('Authorization', `Bearer ${authToken}`)

  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, { ...init, headers })
  } catch {
    // Rete irraggiungibile: distinguerlo da un errore applicativo permette di
    // mostrare all'utente un messaggio che dice cosa fare.
    throw new ApiError(0, 'Server non raggiungibile. Controlla la connessione.')
  }

  if (!response.ok) {
    let detail: unknown
    try {
      detail = await response.json()
    } catch {
      detail = await response.text().catch(() => undefined)
    }
    // Il server spiega spesso cosa è andato storto e cosa fare: buttare via
    // quel messaggio per mostrarne uno generico sarebbe uno spreco.
    throw new ApiError(response.status, dettaglioLeggibile(detail) ?? messaggioPerStato(response.status), detail)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

/**
 * Estrae il messaggio del server, se ne ha mandato uno leggibile.
 *
 * FastAPI mette l'errore in `detail`: una stringa per gli errori applicativi,
 * un elenco di oggetti per quelli di validazione. Solo il primo caso è
 * pensato per essere letto da una persona.
 */
function dettaglioLeggibile(detail: unknown): string | null {
  if (typeof detail === 'string' && detail.trim() !== '') return detail
  if (detail !== null && typeof detail === 'object' && 'detail' in detail) {
    const interno = (detail as { detail: unknown }).detail
    if (typeof interno === 'string' && interno.trim() !== '') return interno
  }
  return null
}

function messaggioPerStato(status: number): string {
  switch (status) {
    case 401:
      return 'Sessione scaduta. Accedi di nuovo.'
    case 403:
      return 'Non hai i permessi per questa operazione.'
    case 404:
      return 'Risorsa non trovata.'
    case 409:
      return 'Operazione in conflitto con lo stato attuale.'
    default:
      return status >= 500 ? 'Errore del server.' : 'Richiesta non valida.'
  }
}

/**
 * Costruisce la richiesta con corpo.
 *
 * La proprieta `body` viene aggiunta solo se c'e davvero: con
 * `exactOptionalPropertyTypes` attivo, passare esplicitamente `undefined` non
 * equivale a ometterla.
 */
function conCorpo(method: string, body?: unknown): RequestInit {
  const init: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) init.body = JSON.stringify(body)
  return init
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, conCorpo('POST', body)),
  put: <T>(path: string, body?: unknown) => request<T>(path, conCorpo('PUT', body)),
  patch: <T>(path: string, body?: unknown) => request<T>(path, conCorpo('PATCH', body)),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
