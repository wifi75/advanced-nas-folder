<script setup lang="ts">
/**
 * Regole, permessi e verifica di una pubblicazione.
 *
 * La verifica dell'accesso sta qui accanto alle regole di proposito: chi
 * configura permessi a prefissi deve poter controllare l'esito senza uscire
 * dalla pagina, altrimenti gli errori li scoprono gli utenti.
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import {
  sharesApi,
  type EsitoAccesso,
  type LinkCondivisione,
  type Livello,
  type Visibilita,
} from '@/api/shares'
import { useSharesStore } from '@/stores/shares'

const props = defineProps<{ id: number }>()

const { t } = useI18n()
const shares = useSharesStore()

const VISIBILITA: Visibilita[] = ['pubblica', 'password', 'utenti', 'utenti_scelti', 'negata']
const LIVELLI: Livello[] = ['lettura', 'scrittura', 'negato']

const share = computed(() => shares.aperta)

// --- nuova regola ---
const nuovoPercorso = ref('')
const nuovaVisibilita = ref<Visibilita>('utenti')
const nuovaPassword = ref('')

async function aggiungiRegola(): Promise<void> {
  const fatto = await shares.aggiungiRegola(
    props.id,
    nuovoPercorso.value,
    nuovaVisibilita.value,
    nuovaVisibilita.value === 'password' ? nuovaPassword.value : undefined,
  )
  if (fatto) {
    nuovoPercorso.value = ''
    nuovaPassword.value = ''
  }
}

// --- nuovo permesso ---
const permessoUtente = ref<number | null>(null)
const permessoPercorso = ref('')
const permessoLivello = ref<Livello>('lettura')

async function assegnaPermesso(): Promise<void> {
  if (permessoUtente.value === null) return
  const fatto = await shares.assegnaPermesso(
    props.id,
    permessoUtente.value,
    permessoPercorso.value,
    permessoLivello.value,
  )
  if (fatto) permessoPercorso.value = ''
}

// --- link di condivisione ---
const link = ref<LinkCondivisione[]>([])
const linkPercorso = ref('')
const linkEtichetta = ref('')
const linkPassword = ref('')
const linkGiorni = ref<number | string>('')
const linkMaxDownload = ref<number | string>('')
const erroreLink = ref('')
/**
 * Il token appena creato.
 *
 * Resta a schermo finché non lo si chiude di proposito: nel database c'è solo
 * la sua impronta, quindi questa è l'unica occasione per copiarlo.
 */
const tokenNuovo = ref<string | null>(null)
const copiato = ref(false)

async function caricaLink(): Promise<void> {
  try {
    link.value = await sharesApi.elencaLink(props.id)
  } catch (e) {
    erroreLink.value = e instanceof Error ? e.message : ''
  }
}

/** Un campo numerico svuotato vale stringa vuota, non `null`: qui diventa «nessun limite». */
function limite(valore: number | string): number | null {
  return typeof valore === 'number' && valore > 0 ? valore : null
}

async function creaLink(): Promise<void> {
  erroreLink.value = ''
  try {
    const creato = await sharesApi.creaLink(props.id, {
      percorso: linkPercorso.value,
      etichetta: linkEtichetta.value || null,
      password: linkPassword.value || null,
      giorni: limite(linkGiorni.value),
      max_download: limite(linkMaxDownload.value),
    })
    tokenNuovo.value = creato.token
    copiato.value = false
    linkPercorso.value = ''
    linkEtichetta.value = ''
    linkPassword.value = ''
    await caricaLink()
  } catch (e) {
    erroreLink.value = e instanceof Error ? e.message : ''
  }
}

async function revocaLink(linkId: number): Promise<void> {
  erroreLink.value = ''
  try {
    await sharesApi.revocaLink(props.id, linkId)
    await caricaLink()
  } catch (e) {
    erroreLink.value = e instanceof Error ? e.message : ''
  }
}

/** Indirizzo completo da consegnare a chi deve ricevere i file. */
function indirizzoLink(token: string): string {
  return `${window.location.origin}${import.meta.env.BASE_URL}l/${token}`
}

async function copia(token: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(indirizzoLink(token))
    copiato.value = true
  } catch {
    // Senza permesso per gli appunti resta la selezione manuale: il testo è
    // visibile a schermo apposta.
    copiato.value = false
  }
}

function quando(iso: string | null): string {
  return iso ? new Date(iso).toLocaleDateString() : ''
}

onMounted(caricaLink)

// --- verifica ---
const provaPercorso = ref('')
const provaUtente = ref<number | string | null>(null)
const esito = ref<EsitoAccesso | null>(null)
const erroreProva = ref('')
const provaInCorso = ref(false)

/**
 * Campo utente vuoto significa **visitatore anonimo**.
 *
 * `v-model.number` su un campo svuotato restituisce una stringa vuota, non
 * `null`: inviarla farebbe fallire la validazione, e la verifica anonima —
 * cioè il caso che più conta controllare — non funzionerebbe mai.
 */
const utenteRichiesto = computed<number | null>(() => {
  const valore = provaUtente.value
  if (valore === null || valore === '' || Number.isNaN(Number(valore))) return null
  return Number(valore)
})

async function verifica(): Promise<void> {
  provaInCorso.value = true
  esito.value = null
  erroreProva.value = ''
  try {
    esito.value = await sharesApi.provaAccesso(props.id, {
      percorso: provaPercorso.value,
      user_id: utenteRichiesto.value,
    })
  } catch (e) {
    // Mostrare l'errore invece di lasciare la pagina muta: un esito assente
    // sembra un guasto del pannello, non una richiesta rifiutata.
    erroreProva.value = e instanceof ApiError ? e.message : t('errori.imprevisto')
  } finally {
    provaInCorso.value = false
  }
}

/** Spiega in una riga chi ha deciso: la regola, il permesso o il valore predefinito. */
const chiHaDeciso = computed(() => {
  if (!esito.value) return ''
  if (esito.value.permesso !== null) {
    return t('prova.decisoDaPermesso', { percorso: esito.value.permesso || t('permessi.tutte') })
  }
  if (esito.value.regola !== null) {
    return t('prova.decisoDaRegola', { percorso: esito.value.regola || t('regole.radice') })
  }
  return t('prova.decisoDaPredefinita')
})
</script>

<template>
  <div
    v-if="share"
    class="dettaglio"
  >
    <!-- regole per cartella -->
    <section class="blocco">
      <h3>{{ t('regole.titolo') }}</h3>
      <p class="spiega">
        {{ t('regole.descrizione') }}
      </p>

      <ul
        v-if="share.regole.length"
        class="elenco"
      >
        <li
          v-for="r in share.regole"
          :key="r.id"
        >
          <span class="percorso">{{ r.path_prefix || t('regole.radice') }}</span>
          <span class="etichetta">{{ t(`visibilita.breve_${r.visibility}`) }}</span>
          <span
            v-if="r.protetta_da_password"
            class="nota"
          >{{ t('regole.protetta') }}</span>
          <button
            type="button"
            class="togli"
            :title="t('comune.elimina')"
            @click="shares.togliRegola(id, r.id)"
          >
            ×
          </button>
        </li>
      </ul>
      <p
        v-else
        class="vuoto"
      >
        {{ t('regole.nessuna') }}
      </p>

      <div class="riga-form">
        <input
          v-model="nuovoPercorso"
          type="text"
          :placeholder="t('regole.percorso')"
        >
        <select v-model="nuovaVisibilita">
          <option
            v-for="v in VISIBILITA"
            :key="v"
            :value="v"
          >
            {{ t(`visibilita.${v}`) }}
          </option>
        </select>
        <input
          v-if="nuovaVisibilita === 'password'"
          v-model="nuovaPassword"
          type="password"
          :placeholder="t('regole.password')"
        >
        <button
          type="button"
          @click="aggiungiRegola"
        >
          {{ t('regole.aggiungi') }}
        </button>
      </div>
    </section>

    <!-- permessi per utente -->
    <section class="blocco">
      <h3>{{ t('permessi.titolo') }}</h3>
      <p class="spiega">
        {{ t('permessi.descrizione') }}
      </p>

      <ul
        v-if="share.permessi.length"
        class="elenco"
      >
        <li
          v-for="p in share.permessi"
          :key="p.id"
        >
          <span class="percorso">#{{ p.user_id }}</span>
          <span class="freccia">→</span>
          <span class="percorso">{{ p.path_prefix || t('permessi.tutte') }}</span>
          <span
            class="etichetta"
            :class="{ 'etichetta--negato': p.livello === 'negato' }"
          >
            {{ t(`permessi.${p.livello}`) }}
          </span>
          <button
            type="button"
            class="togli"
            :title="t('comune.elimina')"
            @click="shares.togliPermesso(id, p.id)"
          >
            ×
          </button>
        </li>
      </ul>
      <p
        v-else
        class="vuoto"
      >
        {{ t('permessi.nessuno') }}
      </p>

      <div class="riga-form">
        <input
          v-model.number="permessoUtente"
          type="number"
          min="1"
          :placeholder="t('permessi.utente')"
        >
        <input
          v-model="permessoPercorso"
          type="text"
          :placeholder="t('permessi.cartella')"
        >
        <select v-model="permessoLivello">
          <option
            v-for="l in LIVELLI"
            :key="l"
            :value="l"
          >
            {{ t(`permessi.${l}`) }}
          </option>
        </select>
        <button
          type="button"
          :disabled="permessoUtente === null"
          @click="assegnaPermesso"
        >
          {{ t('permessi.assegna') }}
        </button>
      </div>
    </section>

    <!-- link di condivisione -->
    <section class="blocco">
      <h3>{{ t('link.titolo') }}</h3>
      <p class="spiega">
        {{ t('link.descrizione') }}
      </p>

      <div
        v-if="tokenNuovo"
        class="token"
        role="status"
      >
        <p class="token__avviso">
          {{ t('link.copiaOra') }}
        </p>
        <code class="token__valore">{{ indirizzoLink(tokenNuovo) }}</code>
        <div class="token__azioni">
          <button
            type="button"
            @click="copia(tokenNuovo)"
          >
            {{ copiato ? t('link.copiato') : t('link.copia') }}
          </button>
          <button
            type="button"
            class="secondario"
            @click="tokenNuovo = null"
          >
            {{ t('comune.chiudi') }}
          </button>
        </div>
      </div>

      <ul
        v-if="link.length"
        class="elenco"
      >
        <li
          v-for="c in link"
          :key="c.id"
        >
          <span class="percorso">{{ c.label || c.path || t('regole.radice') }}</span>
          <span
            class="etichetta"
            :class="{ 'etichetta--negato': c.esaurito }"
          >
            {{ c.esaurito ? t('link.chiuso') : t('link.attivo') }}
          </span>
          <span class="nota">
            {{ t('link.usato', { n: c.download_count }) }}
            <template v-if="c.max_downloads">/ {{ c.max_downloads }}</template>
            <template v-if="c.expires_at"> · {{ quando(c.expires_at) }}</template>
            <template v-if="c.protetto_da_password"> · {{ t('regole.protetta') }}</template>
          </span>
          <button
            v-if="!c.is_revoked"
            type="button"
            class="togli"
            :title="t('link.revoca')"
            @click="revocaLink(c.id)"
          >
            ×
          </button>
        </li>
      </ul>
      <p
        v-else
        class="vuoto"
      >
        {{ t('link.nessuno') }}
      </p>

      <div class="riga-form">
        <input
          v-model="linkPercorso"
          type="text"
          :placeholder="t('link.cartella')"
        >
        <input
          v-model="linkEtichetta"
          type="text"
          :placeholder="t('link.etichetta')"
        >
        <input
          v-model.number="linkGiorni"
          type="number"
          min="1"
          :placeholder="t('link.giorni')"
        >
        <input
          v-model.number="linkMaxDownload"
          type="number"
          min="1"
          :placeholder="t('link.maxDownload')"
        >
        <input
          v-model="linkPassword"
          type="password"
          :placeholder="t('link.password')"
        >
        <button
          type="button"
          @click="creaLink"
        >
          {{ t('link.crea') }}
        </button>
      </div>

      <p
        v-if="erroreLink"
        class="errore-prova"
        role="alert"
      >
        {{ erroreLink }}
      </p>
    </section>

    <!-- verifica -->
    <section class="blocco blocco--prova">
      <h3>{{ t('prova.titolo') }}</h3>
      <p class="spiega">
        {{ t('prova.descrizione') }}
      </p>

      <div class="riga-form">
        <input
          v-model="provaPercorso"
          type="text"
          :placeholder="t('prova.percorso')"
        >
        <input
          v-model.number="provaUtente"
          type="number"
          min="1"
          :placeholder="t('prova.anonimo')"
        >
        <button
          type="button"
          :disabled="provaInCorso"
          @click="verifica"
        >
          {{ t('prova.verifica') }}
        </button>
      </div>

      <p
        v-if="erroreProva"
        class="errore-prova"
        role="alert"
      >
        {{ erroreProva }}
      </p>

      <div
        v-if="esito"
        class="esito"
        :class="esito.consentito ? 'esito--ok' : 'esito--no'"
        role="status"
      >
        <strong>
          {{ esito.consentito ? t('prova.consentito') : t('prova.negato') }}
          <template v-if="esito.consentito && esito.scrittura">
            · {{ t('prova.conScrittura') }}
          </template>
        </strong>
        <span>{{ esito.motivo }}</span>
        <span class="chi">{{ chiHaDeciso }}</span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.token {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--accento);
  border-radius: var(--raggio);
  background: var(--superficie-alt);
}

.token__avviso {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 500;
}

.token__valore {
  overflow-wrap: anywhere;
  font-size: 0.8rem;
  user-select: all;
}

.token__azioni {
  display: flex;
  gap: 0.5rem;
}

.dettaglio {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding-block-start: 1rem;
  border-block-start: 1px solid var(--bordo);
}

.blocco {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

h3 {
  margin: 0;
  font-size: 0.95rem;
}

.spiega {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--testo-tenue);
  max-width: 70ch;
}

.elenco {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.elenco li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  background: var(--sfondo);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  font-size: 0.875rem;
}

.percorso {
  font-family: ui-monospace, monospace;
  font-size: 0.8125rem;
}

.freccia {
  color: var(--testo-tenue);
}

.etichetta {
  padding: 0.1rem 0.45rem;
  font-size: 0.7rem;
  border-radius: 999px;
  border: 1px solid var(--bordo);
  color: var(--testo-tenue);
}

.etichetta--negato {
  color: var(--errore);
  border-color: var(--errore);
}

.togli {
  margin-inline-start: auto;
  inline-size: 22px;
  block-size: 22px;
  display: grid;
  place-items: center;
  font: inherit;
  line-height: 1;
  color: var(--testo-tenue);
  background: transparent;
  border: 1px solid var(--bordo);
  border-radius: 6px;
  cursor: pointer;
}

.togli:hover {
  color: var(--errore);
  border-color: var(--errore);
}

.vuoto {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--testo-tenue);
  font-style: italic;
}

.riga-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.riga-form input,
.riga-form select {
  flex: 1;
  min-inline-size: 110px;
  padding: 0.4rem 0.55rem;
  font: inherit;
  font-size: 0.8125rem;
  color: var(--testo);
  background: var(--sfondo);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

.riga-form button {
  flex: none;
  padding: 0.4rem 0.8rem;
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--accento-testo);
  background: var(--accento);
  border: none;
  border-radius: var(--raggio);
  cursor: pointer;
}

.riga-form button:disabled {
  opacity: 0.55;
  cursor: default;
}

.blocco--prova {
  padding: 0.9rem 1rem;
  background: var(--superficie-alt);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

.esito {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.65rem 0.85rem;
  border-radius: var(--raggio);
  font-size: 0.875rem;
  border: 1px solid var(--bordo);
  border-left-width: 3px;
}

.esito--ok {
  border-left-color: var(--ok);
}

.esito--no {
  border-left-color: var(--errore);
}

.esito .chi {
  font-size: 0.8125rem;
  color: var(--testo-tenue);
}

.errore-prova {
  margin: 0;
  font-size: 0.875rem;
  color: var(--errore);
}
</style>
