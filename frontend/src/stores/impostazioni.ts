/**
 * Marchio e preferenze del pannello.
 *
 * Caricate una volta all'avvio e tenute qui: servono alla barra laterale e al
 * titolo della scheda, cioè a due punti lontani fra loro che non possono
 * chiederle ciascuno per conto proprio.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { impostazioniApi, type Impostazioni } from '@/api/impostazioni'

const PREDEFINITE: Impostazioni = {
  titolo: 'Advanced NAS Folder',
  sottotitolo: null,
  logo_url: null,
  mostra_nascosti: false,
}

export const useImpostazioniStore = defineStore('impostazioni', () => {
  const valori = ref<Impostazioni>({ ...PREDEFINITE })
  const caricate = ref(false)

  async function carica(): Promise<void> {
    try {
      valori.value = await impostazioniApi.leggi()
    } catch {
      // Il pannello deve disegnarsi comunque: senza il marchio, ma
      // disegnarsi. Un errore qui non è una ragione per una pagina bianca.
      valori.value = { ...PREDEFINITE }
    } finally {
      caricate.value = true
    }
  }

  async function salva(dati: Partial<Impostazioni>): Promise<void> {
    valori.value = await impostazioniApi.modifica(dati)
  }

  return { valori, caricate, carica, salva }
})
