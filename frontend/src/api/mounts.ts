/** Chiamate agli endpoint dei mount NFS. */

import { api } from '@/api/client'

export type AccessoRichiesto = 'ro' | 'rw'
export type StatoMount = 'configurato' | 'montato' | 'smontato' | 'errore'

export interface StatoEffettivo {
  montato: boolean
  sorgente: string | null
  opzioni: string | null
  scrittura: boolean | null
  /** Esito della prova di scrittura sul campo: più attendibile delle opzioni. */
  scrittura_verificata: boolean | null
}

export interface Mount {
  id: number
  slug: string
  label: string
  server: string
  export_path: string
  mountpoint: string
  nfs_version: string
  requested_access: AccessoRichiesto
  automount: boolean
  idle_timeout: number
  state: StatoMount
  effective_read_write: boolean | null
  effective_options: string | null
  last_error: string | null
}

export interface MountDettaglio extends Mount {
  effettivo: StatoEffettivo | null
  /** Valorizzato quando richiesto ed effettivo divergono. Va mostrato in evidenza. */
  avviso: string | null
}

export interface NuovoMount {
  slug: string
  label: string
  server: string
  export_path: string
  nfs_version: string
  automount: boolean
  idle_timeout: number
  consenti_scrittura: boolean
}

export interface Esportazione {
  percorso: string
  client: string
}

export interface Scoperta {
  server: string
  esportazioni: Esportazione[]
  /** Versioni NFS che il NAS espone davvero. Senza la 4, chiederla fallisce. */
  versioni: string[]
}

export const mountsApi = {
  elenca: () => api.get<Mount[]>('/mounts'),
  dettaglio: (id: number) => api.get<MountDettaglio>(`/mounts/${id}`),
  crea: (dati: NuovoMount) => api.post<MountDettaglio>('/mounts', dati),
  modifica: (id: number, dati: Partial<NuovoMount>) =>
    api.patch<MountDettaglio>(`/mounts/${id}`, dati),
  avvia: (id: number) => api.post<MountDettaglio>(`/mounts/${id}/avvia`),
  ferma: (id: number) => api.post<MountDettaglio>(`/mounts/${id}/ferma`),
  elimina: (id: number) => api.delete<void>(`/mounts/${id}`),
  scopri: (server: string) => api.post<Scoperta>('/mounts/discover', { server }),
}
