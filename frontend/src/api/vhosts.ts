/** Pubblicazione del pannello sul web server. */

import { api } from '@/api/client'

export type WebServer = 'apache' | 'nginx'

export interface VHost {
  id: number
  hostname: string
  path_prefix: string
  webserver: WebServer
  is_enabled: boolean
  share_id: number | null
  last_error: string | null
}

export interface NuovoVHost {
  hostname: string
  webserver: WebServer
  prefisso: string
}

export const vhostsApi = {
  disponibili: () => api.get<{ installati: WebServer[] }>('/vhosts/disponibili'),
  elenca: () => api.get<VHost[]>('/vhosts'),
  /** Mostra cosa verrebbe scritto, senza scriverlo. */
  anteprima: (dati: NuovoVHost) =>
    api.post<{ configurazione: string }>('/vhosts/anteprima', dati),
  crea: (dati: NuovoVHost) => api.post<VHost>('/vhosts', dati),
  configurazione: (id: number) => api.get<{ configurazione: string }>(`/vhosts/${id}/configurazione`),
  elimina: (id: number) => api.delete<void>(`/vhosts/${id}`),
}
