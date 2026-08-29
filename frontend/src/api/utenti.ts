/** Gestione degli utenti del pannello. */

import { api } from '@/api/client'

export interface Utente {
  id: number
  username: string
  email: string | null
  is_admin: boolean
  is_active: boolean
  /** Percorso oltre il quale l'utente non può uscire. Vuoto = nessun limite. */
  scope: string
  locale: string
  theme: string
  hide_dotfiles: boolean
  can_create: boolean
  can_delete: boolean
  can_modify: boolean
  can_rename: boolean
  can_share: boolean
  can_download: boolean
  can_upload: boolean
}

export interface NuovoUtente {
  username: string
  password: string
  email?: string | null
  is_admin: boolean
  scope: string
  can_create: boolean
  can_delete: boolean
  can_modify: boolean
  can_rename: boolean
  can_share: boolean
  can_download: boolean
  can_upload: boolean
}

export const utentiApi = {
  elenca: () => api.get<Utente[]>('/utenti'),
  crea: (dati: NuovoUtente) => api.post<Utente>('/utenti', dati),
  modifica: (id: number, dati: Partial<NuovoUtente> & { is_active?: boolean }) =>
    api.patch<Utente>(`/utenti/${id}`, dati),
  elimina: (id: number) => api.delete<void>(`/utenti/${id}`),
  cambiaLaMiaPassword: (attuale: string, nuova: string) =>
    api.post<void>('/utenti/me/password', { attuale, nuova }),
}
