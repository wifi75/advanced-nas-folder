/** Impostazioni del pannello e spazio disco. */

import { api } from '@/api/client'

export interface Impostazioni {
  titolo: string
  sottotitolo: string | null
  logo_url: string | null
  mostra_nascosti: boolean
}

export interface SpazioDisco {
  mount_id: number | null
  label: string
  mountpoint: string
  /** Vuoti se il percorso non è raggiungibile: zero farebbe sembrare pieno
   *  un disco che semplicemente non risponde. */
  totale: number | null
  libero: number | null
}

export const impostazioniApi = {
  leggi: () => api.get<Impostazioni>('/impostazioni'),
  modifica: (dati: Partial<Impostazioni>) => api.patch<Impostazioni>('/impostazioni', dati),
  spazio: () => api.get<SpazioDisco[]>('/impostazioni/spazio'),
  spazioPannello: () => api.get<SpazioDisco>('/impostazioni/spazio/pannello'),
}
