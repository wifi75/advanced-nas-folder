/** Chiamate agli endpoint delle pubblicazioni, delle regole e dei permessi. */

import { api } from '@/api/client'

export type Visibilita = 'pubblica' | 'password' | 'utenti' | 'utenti_scelti' | 'negata'
export type Livello = 'negato' | 'lettura' | 'scrittura'

export interface Regola {
  id: number
  path_prefix: string
  visibility: Visibilita
  protetta_da_password: boolean
}

export interface Permesso {
  id: number
  user_id: number
  path_prefix: string
  livello: Livello
}

export interface Share {
  id: number
  slug: string
  label: string
  description: string | null
  mount_id: number
  subpath: string
  is_enabled: boolean
  default_visibility: Visibilita
}

export interface ShareDettaglio extends Share {
  regole: Regola[]
  permessi: Permesso[]
}

export interface NuovaShare {
  slug: string
  label: string
  mount_id: number
  subpath: string
  description: string | null
  default_visibility: Visibilita
  is_enabled: boolean
}

export interface EsitoAccesso {
  consentito: boolean
  scrittura: boolean
  visibilita: Visibilita
  motivo: string
  /** Prefisso della regola che ha deciso, se ce n'è una. */
  regola: string | null
  /** Prefisso del permesso personale che ha deciso, se ce n'è uno. */
  permesso: string | null
}

export const sharesApi = {
  elenca: () => api.get<Share[]>('/shares'),
  dettaglio: (id: number) => api.get<ShareDettaglio>(`/shares/${id}`),
  crea: (dati: NuovaShare) => api.post<Share>('/shares', dati),
  modifica: (id: number, dati: Partial<NuovaShare>) => api.patch<Share>(`/shares/${id}`, dati),
  elimina: (id: number) => api.delete<void>(`/shares/${id}`),

  aggiungiRegola: (
    id: number,
    dati: { path_prefix: string; visibility: Visibilita; password?: string },
  ) => api.post<Regola>(`/shares/${id}/regole`, dati),
  togliRegola: (id: number, regolaId: number) =>
    api.delete<void>(`/shares/${id}/regole/${regolaId}`),

  assegnaPermesso: (
    id: number,
    dati: { user_id: number; path_prefix: string; livello: Livello },
  ) => api.put<Permesso>(`/shares/${id}/permessi`, dati),
  togliPermesso: (id: number, permessoId: number) =>
    api.delete<void>(`/shares/${id}/permessi/${permessoId}`),

  provaAccesso: (id: number, dati: { percorso: string; user_id: number | null }) =>
    api.post<EsitoAccesso>(`/shares/${id}/prova-accesso`, dati),
}
