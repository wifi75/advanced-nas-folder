<script setup lang="ts">
/**
 * Navigazione di una cartella pubblicata.
 *
 * È l'unica vista che funziona anche senza aver effettuato l'accesso: chi
 * riceve il collegamento a una cartella pubblica non ha un account, e
 * chiedergliene uno renderebbe quella visibilità inutile.
 */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { archivioApi, indirizzoDownload, type Contenuto, type Voce } from '@/api/archivio'
import { ApiError } from '@/api/client'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()

const contenuto = ref<Contenuto | null>(null)
const errore = ref<string | null>(null)
/** Vero quando il percorso è protetto da password e non l'abbiamo ancora. */
const chiedePassword = ref(false)
const password = ref('')
const carico = ref(false)
const inPreparazione = ref<string | null>(null)

const slug = computed(() => String(route.params.slug ?? ''))
const percorso = computed(() => {
  const parti = route.params.percorso
  return Array.isArray(parti) ? parti.join('/') : String(parti ?? '')
})

async function carica(): Promise<void> {
  carico.value = true
  errore.value = null
  try {
    contenuto.value = await archivioApi.contenuto(
      slug.value,
      percorso.value,
      password.value || undefined,
    )
    chiedePassword.value = false
  } catch (e) {
    contenuto.value = null
    if (e instanceof ApiError && e.status === 403) {
      // Un 403 su un percorso pubblicato è quasi sempre una password
      // mancante: offrirla subito evita un vicolo cieco. Se la password non
      // c'entra, il messaggio del server resta comunque visibile.
      chiedePassword.value = true
    }
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    carico.value = false
  }
}

watch([slug, percorso], carica, { immediate: true })

function apri(voce: Voce): void {
  router.push(`/archivio/${slug.value}/${voce.percorso.split('/').map(encodeURIComponent).join('/')}`)
}

function vaiA(p: string): void {
  const coda = p ? `/${p.split('/').map(encodeURIComponent).join('/')}` : ''
  router.push(`/archivio/${slug.value}${coda}`)
}

async function scarica(voce: Voce): Promise<void> {
  inPreparazione.value = voce.percorso
  try {
    // Una navigazione, non una fetch: è il browser a doversi occupare della
    // barra di avanzamento e della ripresa se la rete cade.
    globalThis.location.href = await indirizzoDownload(
      slug.value,
      voce.percorso,
      password.value || undefined,
    )
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    inPreparazione.value = null
  }
}

// --- modifiche ---
// Compaiono solo quando il server dice che questa cartella è scrivibile: il
// controllo vero lo rifà lui a ogni chiamata, ma mostrare pulsanti che
// falliranno di sicuro è solo un modo di far perdere tempo.
const puoScrivere = computed(() => contenuto.value?.scrittura === true)

const nuovaCartella = ref('')
const inRinomina = ref<Voce | null>(null)
const nomeNuovo = ref('')
const daEliminare = ref<Voce | null>(null)
const daSpostare = ref<Voce | null>(null)
const destinazione = ref('')
const operazione = ref(false)

async function conEsito(azione: () => Promise<unknown>): Promise<void> {
  operazione.value = true
  errore.value = null
  try {
    await azione()
    await carica()
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    operazione.value = false
  }
}

async function creaCartella(): Promise<void> {
  const nome = nuovaCartella.value.trim()
  if (!nome) return
  await conEsito(async () => {
    await archivioApi.creaCartella(slug.value, percorso.value, nome)
    nuovaCartella.value = ''
  })
}

function apriRinomina(voce: Voce): void {
  inRinomina.value = voce
  nomeNuovo.value = voce.nome
}

async function confermaRinomina(): Promise<void> {
  const voce = inRinomina.value
  if (voce === null || nomeNuovo.value.trim() === '') return
  await conEsito(async () => {
    await archivioApi.rinomina(slug.value, voce.percorso, nomeNuovo.value.trim())
    inRinomina.value = null
  })
}

function apriSposta(voce: Voce): void {
  daSpostare.value = voce
  destinazione.value = percorso.value
}

async function confermaSposta(copiando: boolean): Promise<void> {
  const voce = daSpostare.value
  if (voce === null) return
  await conEsito(async () => {
    const dove = destinazione.value.trim()
    if (copiando) await archivioApi.copia(slug.value, voce.percorso, dove)
    else await archivioApi.sposta(slug.value, voce.percorso, dove)
    daSpostare.value = null
  })
}

async function confermaElimina(ricorsivo: boolean): Promise<void> {
  const voce = daEliminare.value
  if (voce === null) return
  await conEsito(async () => {
    await archivioApi.elimina(slug.value, voce.percorso, ricorsivo)
    daEliminare.value = null
  })
}

const UNITA = ['B', 'kB', 'MB', 'GB', 'TB'] as const

function dimensione(byte: number | null): string {
  if (byte === null) return ''
  let valore = byte
  let unita = 0
  while (valore >= 1000 && unita < UNITA.length - 1) {
    valore /= 1000
    unita += 1
  }
  const cifre = unita === 0 || valore >= 100 ? 0 : 1
  return `${valore.toLocaleString(locale.value, { maximumFractionDigits: cifre })} ${UNITA[unita]}`
}

function quando(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString(locale.value, { dateStyle: 'medium', timeStyle: 'short' })
}
</script>

<template>
  <section class="archivio">
    <header class="intestazione">
      <h1 class="titolo">
        {{ contenuto?.label ?? slug }}
      </h1>
      <p
        v-if="contenuto?.descrizione"
        class="descrizione"
      >
        {{ contenuto.descrizione }}
      </p>

      <nav
        class="briciole"
        :aria-label="t('archivio.percorso')"
      >
        <button
          type="button"
          class="briciola"
          @click="vaiA('')"
        >
          {{ t('archivio.radice') }}
        </button>
        <template
          v-for="[nome, p] in contenuto?.briciole ?? []"
          :key="p"
        >
          <span
            class="briciole__separatore"
            aria-hidden="true"
          >/</span>
          <button
            type="button"
            class="briciola"
            @click="vaiA(p)"
          >
            {{ nome }}
          </button>
        </template>
      </nav>
    </header>

    <form
      v-if="puoScrivere"
      class="riga-form"
      @submit.prevent="creaCartella"
    >
      <input
        v-model="nuovaCartella"
        type="text"
        class="campo"
        :placeholder="t('operazioni.nuovaCartella')"
      >
      <button
        type="submit"
        class="bottone bottone--tenue"
        :disabled="operazione || nuovaCartella.trim() === ''"
      >
        {{ t('operazioni.crea') }}
      </button>
    </form>

    <form
      v-if="chiedePassword"
      class="password"
      @submit.prevent="carica"
    >
      <label
        class="password__etichetta"
        for="anf-password-cartella"
      >{{ t('archivio.passwordRichiesta') }}</label>
      <div class="password__riga">
        <input
          id="anf-password-cartella"
          v-model="password"
          type="password"
          class="campo"
          autocomplete="current-password"
        >
        <button
          type="submit"
          class="bottone"
          :disabled="password === ''"
        >
          {{ t('archivio.sblocca') }}
        </button>
      </div>
    </form>

    <p
      v-if="errore && !carico"
      class="avviso avviso--errore"
      role="alert"
    >
      {{ errore }}
    </p>

    <p
      v-if="carico"
      class="avviso"
    >
      {{ t('comune.carico') }}
    </p>

    <p
      v-else-if="contenuto && contenuto.voci.length === 0"
      class="avviso"
    >
      {{ t('archivio.vuota') }}
    </p>

    <ul
      v-else-if="contenuto"
      class="voci"
    >
      <li
        v-for="voce in contenuto.voci"
        :key="voce.percorso"
        class="voce"
      >
        <button
          v-if="voce.cartella"
          type="button"
          class="voce__apri"
          @click="apri(voce)"
        >
          <svg
            class="voce__icona voce__icona--cartella"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
          </svg>
          <span class="voce__nome">{{ voce.nome }}</span>
        </button>

        <div
          v-else
          class="voce__apri voce__apri--file"
        >
          <svg
            class="voce__icona"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M6 3h7l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z M13 3v5h5" />
          </svg>
          <span class="voce__nome">{{ voce.nome }}</span>
        </div>

        <span class="voce__dimensione">{{ dimensione(voce.dimensione) }}</span>
        <span class="voce__data">{{ quando(voce.modificato) }}</span>

        <div class="voce__azioni">
          <button
            v-if="!voce.cartella"
            type="button"
            class="bottone bottone--tenue"
            :disabled="inPreparazione === voce.percorso"
            @click="scarica(voce)"
          >
            {{ inPreparazione === voce.percorso ? t('comune.carico') : t('archivio.scarica') }}
          </button>
          <template v-if="puoScrivere">
            <button
              type="button"
              class="bottone bottone--tenue"
              @click="apriRinomina(voce)"
            >
              {{ t('operazioni.rinomina') }}
            </button>
            <button
              type="button"
              class="bottone bottone--tenue"
              @click="apriSposta(voce)"
            >
              {{ t('operazioni.sposta') }}
            </button>
            <button
              type="button"
              class="bottone bottone--pericolo"
              @click="daEliminare = voce"
            >
              {{ t('comune.elimina') }}
            </button>
          </template>
        </div>
      </li>
    </ul>

    <div
      v-if="inRinomina"
      class="velo"
      @click.self="inRinomina = null"
    >
      <form
        class="pannello"
        @submit.prevent="confermaRinomina"
      >
        <h2>{{ t('operazioni.rinomina') }}</h2>
        <input
          v-model="nomeNuovo"
          type="text"
          class="campo"
        >
        <div class="pannello__azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="inRinomina = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="submit"
            class="bottone"
            :disabled="operazione"
          >
            {{ t('comune.salva') }}
          </button>
        </div>
      </form>
    </div>

    <div
      v-if="daSpostare"
      class="velo"
      @click.self="daSpostare = null"
    >
      <div
        class="pannello"
        role="dialog"
      >
        <h2>{{ t('operazioni.spostaTitolo', { nome: daSpostare.nome }) }}</h2>
        <label
          class="pannello__etichetta"
          for="anf-destinazione"
        >{{ t('operazioni.destinazione') }}</label>
        <input
          id="anf-destinazione"
          v-model="destinazione"
          type="text"
          class="campo"
          :placeholder="t('archivio.radice')"
        >
        <div class="pannello__azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="daSpostare = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="button"
            class="bottone bottone--tenue"
            :disabled="operazione"
            @click="confermaSposta(true)"
          >
            {{ t('operazioni.copia') }}
          </button>
          <button
            type="button"
            class="bottone"
            :disabled="operazione"
            @click="confermaSposta(false)"
          >
            {{ t('operazioni.sposta') }}
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="daEliminare"
      class="velo"
      @click.self="daEliminare = null"
    >
      <div
        class="pannello"
        role="dialog"
      >
        <h2>{{ t('operazioni.eliminaTitolo', { nome: daEliminare.nome }) }}</h2>
        <p class="pannello__testo">
          {{
            daEliminare.cartella ? t('operazioni.eliminaCartella') : t('operazioni.eliminaFile')
          }}
        </p>
        <div class="pannello__azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="daEliminare = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="button"
            class="bottone bottone--pericolo"
            :disabled="operazione"
            @click="confermaElimina(daEliminare.cartella)"
          >
            {{ t('comune.elimina') }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.archivio {
  display: flex;
  flex: 1;
  flex-direction: column;
  /* Stessa larghezza delle altre viste: righe lunghe quanto lo schermo
     rendono difficile seguire la riga fino alla colonna della data. */
  width: min(880px, 100% - 2.5rem);
  margin-inline: auto;
  gap: 1.25rem;
  padding-block: 1.5rem;
}

.intestazione {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.titolo {
  margin: 0;
  font-size: 1.5rem;
}

.descrizione {
  margin: 0;
  color: var(--testo-tenue);
}

.briciole {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.briciola {
  padding: 0.15rem 0.35rem;
  border: 0;
  border-radius: var(--raggio);
  background: none;
  color: var(--tinta-pubblicazioni);
  cursor: pointer;
  font: inherit;
}

.briciola:hover {
  background: var(--superficie-alt);
}

.briciole__separatore {
  color: var(--testo-tenue);
}

.voci {
  display: flex;
  flex-direction: column;
  gap: 1px;
  margin: 0;
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--bordo);
  list-style: none;
}

.voce {
  display: grid;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.85rem;
  background: var(--superficie);
  /* Nome elastico, poi dimensione e data a larghezza fissa così le colonne
     restano allineate anche quando i nomi sono molto diversi. */
  grid-template-columns: minmax(0, 1fr) 5.5rem 11rem auto;
}

.voce__apri {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 0.6rem;
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  text-align: left;
}

.voce__apri:not(.voce__apri--file) {
  cursor: pointer;
}

.voce__apri:not(.voce__apri--file):hover .voce__nome {
  text-decoration: underline;
}

.voce__icona {
  flex: none;
  width: 1.15rem;
  height: 1.15rem;
  fill: none;
  stroke: var(--testo-tenue);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.6;
}

.voce__icona--cartella {
  stroke: var(--tinta-file);
}

.voce__nome {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voce__dimensione,
.voce__data {
  color: var(--testo-tenue);
  font-size: 0.85rem;
  /* Cifre a larghezza fissa: senza, le colonne di numeri ballano. */
  font-variant-numeric: tabular-nums;
}

.voce__dimensione {
  text-align: right;
}

.campo {
  flex: 1;
  min-width: 0;
  padding: 0.55rem 0.7rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--sfondo);
  color: var(--testo);
  font: inherit;
}

.bottone {
  padding: 0.45rem 0.85rem;
  border: none;
  border-radius: var(--raggio);
  background: var(--accento);
  color: var(--accento-testo);
  cursor: pointer;
  font: inherit;
  font-size: 0.875rem;
  font-weight: 500;
}

.bottone--tenue {
  border: 1px solid var(--bordo);
  background: transparent;
  color: var(--testo);
}

.bottone:disabled {
  cursor: default;
  opacity: 0.55;
}

.voce__azioni {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.bottone--pericolo {
  border: 1px solid var(--errore);
  background: transparent;
  color: var(--errore);
}

.riga-form {
  display: flex;
  gap: 0.5rem;
  max-width: 26rem;
}

.velo {
  position: fixed;
  display: grid;
  padding: 1rem;
  background: rgb(0 0 0 / 45%);
  inset: 0;
  place-items: center;
}

.pannello {
  display: flex;
  flex-direction: column;
  width: min(26rem, 100%);
  gap: 0.7rem;
  padding: 1.25rem;
  border-radius: var(--raggio);
  background: var(--superficie);
}

.pannello h2 {
  margin: 0;
  font-size: 1.05rem;
}

.pannello__testo,
.pannello__etichetta {
  margin: 0;
  color: var(--testo-tenue);
  font-size: 0.9rem;
}

.pannello__azioni {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
}

.password {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-width: 24rem;
}

.password__riga {
  display: flex;
  gap: 0.5rem;
}

.password__etichetta {
  color: var(--testo-tenue);
  font-size: 0.9rem;
}

.avviso {
  margin: 0;
  color: var(--testo-tenue);
}

.avviso--errore {
  color: var(--tinta-link);
}

@media (width <= 40rem) {
  .voce {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .voce__data {
    display: none;
  }
}
</style>
