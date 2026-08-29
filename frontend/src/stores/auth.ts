/** Sessione dell'utente. */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api, ApiError, setAuthToken } from '@/api/client'

export interface Utente {
  id: number
  username: string
  email: string | null
  is_admin: boolean
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

interface RispostaAccesso {
  access_token: string
  token_type: string
  expires_in: number
  user: Utente
  password_predefinita: boolean
}

const CHIAVE = 'anf.token'

function leggiToken(): string | null {
  // Un browser in navigazione privata puo negare l'accesso all'archivio: il
  // pannello deve restare usabile, chiedendo semplicemente di riaccedere.
  try {
    return localStorage.getItem(CHIAVE)
  } catch {
    return null
  }
}

function scriviToken(token: string | null): void {
  try {
    if (token === null) localStorage.removeItem(CHIAVE)
    else localStorage.setItem(CHIAVE, token)
  } catch {
    /* archivio non disponibile: la sessione durera solo per questa pagina */
  }
}

export const useAuthStore = defineStore('auth', () => {
  const utente = ref<Utente | null>(null)
  const passwordPredefinita = ref(false)
  const inCorso = ref(false)
  const errore = ref('')

  const autenticato = computed(() => utente.value !== null)

  async function ripristina(): Promise<void> {
    const token = leggiToken()
    if (!token) return
    setAuthToken(token)
    try {
      utente.value = await api.get<Utente>('/auth/me')
    } catch {
      // Token scaduto o non piu valido: si riparte puliti.
      setAuthToken(null)
      scriviToken(null)
      utente.value = null
    }
  }

  async function accedi(username: string, password: string): Promise<boolean> {
    inCorso.value = true
    errore.value = ''
    try {
      const risposta = await api.post<RispostaAccesso>('/auth/login', { username, password })
      setAuthToken(risposta.access_token)
      scriviToken(risposta.access_token)
      utente.value = risposta.user
      passwordPredefinita.value = risposta.password_predefinita
      return true
    } catch (e) {
      errore.value =
        e instanceof ApiError && e.status === 401
          ? 'Nome utente o password non corretti.'
          : e instanceof ApiError
            ? e.message
            : 'Errore imprevisto durante l’accesso.'
      return false
    } finally {
      inCorso.value = false
    }
  }

  function esci(): void {
    setAuthToken(null)
    scriviToken(null)
    utente.value = null
    passwordPredefinita.value = false
  }

  return { utente, autenticato, passwordPredefinita, inCorso, errore, ripristina, accedi, esci }
})
