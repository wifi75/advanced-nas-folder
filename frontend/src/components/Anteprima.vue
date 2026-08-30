<script setup lang="ts">
/**
 * Anteprima di un file, sopra l'elenco.
 *
 * Solo i tipi che il browser sa mostrare senza rischi: immagini, video,
 * audio, PDF e testo semplice. Il server rifiuta comunque di aprire in linea
 * qualunque altro tipo — HTML e SVG compresi, che eseguiti nel contesto del
 * pannello sarebbero codice altrui — quindi questo elenco non è la difesa, è
 * solo il modo di non proporre un'anteprima che non arriverebbe.
 */
import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import ini from 'highlight.js/lib/languages/ini'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import python from 'highlight.js/lib/languages/python'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { archivioApi, indirizzoDownload, type DatiScatto, type Voce } from '@/api/archivio'

const props = defineProps<{
  slug: string
  voce: Voce
  modificabile?: boolean
  /** Posizione fra le immagini della cartella, per «3 di 12». Da 1; zero
   *  significa «non e' una raccolta», e le frecce non compaiono. */
  posizione: number
  quante: number
}>()
const emit = defineEmits<{
  chiudi: []
  salvato: []
  precedente: []
  successiva: []
  primaImmagine: []
}>()

/** Le frecce compaiono solo se c'e' davvero qualcosa prima o dopo. */
const haPrecedente = computed(() => props.posizione > 1)
const haSuccessiva = computed(() => props.posizione > 0 && props.posizione < props.quante)

/**
 * Tastiera e dito: sono i due modi in cui si sfoglia una raccolta di foto.
 * Senza, ogni immagine andrebbe chiusa e riaperta dalla griglia.
 */
function daTastiera(evento: KeyboardEvent): void {
  // Non mentre si scrive: le frecce servono a muoversi nel testo.
  if (inModifica.value) return
  if (evento.key === 'ArrowLeft' && haPrecedente.value) emit('precedente')
  if (evento.key === 'ArrowRight' && haSuccessiva.value) emit('successiva')
  if (evento.key === 'Escape') emit('chiudi')
  if (evento.key === ' ' && props.quante > 1) {
    evento.preventDefault()
    alternaPresentazione()
  }
}

/** Schermo intero vero, quello del browser: la finestra del pannello resta
 *  comunque dentro la pagina, e per guardare una panoramica non basta. */
const finestra = ref<HTMLElement | null>(null)
const aSchermoIntero = ref(false)

async function alternaSchermoIntero(): Promise<void> {
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else if (finestra.value) {
      await finestra.value.requestFullscreen()
    }
  } catch {
    // Alcuni browser lo negano se non arriva da un gesto diretto, e su iPhone
    // non esiste affatto per un elemento qualunque: il pulsante non fa nulla,
    // ma l'anteprima continua a funzionare.
  }
}

function segnaSchermoIntero(): void {
  aSchermoIntero.value = document.fullscreenElement !== null
}

// --- dati di scatto ---
const scatto = ref<DatiScatto | null>(null)
const dettagliAperti = ref(false)

async function leggiScatto(): Promise<void> {
  scatto.value = null
  if (genere.value !== 'immagine') return
  try {
    scatto.value = await archivioApi.scatto(props.slug, props.voce.percorso)
  } catch {
    // Una foto senza dati di scatto e' normale: le immagini modificate o
    // esportate spesso li perdono. Il riquadro semplicemente non compare.
  }
}

const haDettagli = computed(
  () =>
    scatto.value !== null &&
    (scatto.value.scattata !== null ||
      scatto.value.fotocamera !== null ||
      scatto.value.tempo !== null),
)

const quandoScattata = computed(() => {
  const q = scatto.value?.scattata
  if (!q) return null
  return new Date(q).toLocaleString()
})

const mappa = computed(() => {
  const s = scatto.value
  if (!s || s.latitudine === null || s.longitudine === null) return null
  return `https://www.openstreetmap.org/?mlat=${s.latitudine}&mlon=${s.longitudine}#map=15/${s.latitudine}/${s.longitudine}`
})

// --- ingrandimento ---
//
// Su una panoramica da 14000 pixel guardare l'immagine intera non serve a
// niente: il dettaglio si vede solo ingrandendo.
const ingrandimento = ref(1)
const spostamento = ref({ x: 0, y: 0 })

function azzeraIngrandimento(): void {
  ingrandimento.value = 1
  spostamento.value = { x: 0, y: 0 }
}

function rotella(evento: WheelEvent): void {
  if (genere.value !== 'immagine') return
  evento.preventDefault()
  const passo = evento.deltaY < 0 ? 1.2 : 1 / 1.2
  ingrandimento.value = Math.min(8, Math.max(1, ingrandimento.value * passo))
  if (ingrandimento.value === 1) spostamento.value = { x: 0, y: 0 }
}

let trascina: { x: number; y: number } | null = null

function iniziaTrascino(evento: MouseEvent): void {
  if (ingrandimento.value === 1) return
  trascina = { x: evento.clientX - spostamento.value.x, y: evento.clientY - spostamento.value.y }
}

function muovi(evento: MouseEvent): void {
  if (!trascina) return
  spostamento.value = { x: evento.clientX - trascina.x, y: evento.clientY - trascina.y }
}

function fermaTrascino(): void {
  trascina = null
}

// --- presentazione ---
const inPresentazione = ref(false)
const intervallo = ref(4)
let timer: ReturnType<typeof setInterval> | null = null

function fermaPresentazione(): void {
  if (timer) clearInterval(timer)
  timer = null
  inPresentazione.value = false
}

function alternaPresentazione(): void {
  if (inPresentazione.value) {
    fermaPresentazione()
    return
  }
  inPresentazione.value = true
  timer = setInterval(() => {
    // Alla fine ricomincia invece di fermarsi: una presentazione che si
    // interrompe da sola costringe a rimetterla in moto ogni giro.
    if (haSuccessiva.value) emit('successiva')
    else emit('primaImmagine')
  }, intervallo.value * 1000)
}

let partenzaX = 0

function inizioTocco(evento: TouchEvent): void {
  partenzaX = evento.changedTouches[0]?.clientX ?? 0
}

function fineTocco(evento: TouchEvent): void {
  const spostamento = (evento.changedTouches[0]?.clientX ?? 0) - partenzaX
  // Sotto i 50 pixel e' un tocco, non uno scorrimento: cambiare foto a ogni
  // sfioramento renderebbe impossibile guardarne una.
  if (Math.abs(spostamento) < 50) return
  if (spostamento > 0 && haPrecedente.value) emit('precedente')
  if (spostamento < 0 && haSuccessiva.value) emit('successiva')
}

onMounted(() => {
  window.addEventListener('keydown', daTastiera)
  document.addEventListener('fullscreenchange', segnaSchermoIntero)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', daTastiera)
  document.removeEventListener('fullscreenchange', segnaSchermoIntero)
  fermaPresentazione()
  // Uscendo dall'anteprima mentre si e' a schermo intero, il browser
  // resterebbe cosi' su una pagina che non lo prevede.
  if (document.fullscreenElement) void document.exitFullscreen()
})

const { t } = useI18n()

for (const [nome, definizione] of Object.entries({
  bash,
  css,
  ini,
  javascript,
  json,
  python,
  sql,
  typescript,
  xml,
  yaml,
})) {
  hljs.registerLanguage(nome, definizione)
}

const indirizzo = ref<string | null>(null)
const errore = ref<string | null>(null)
const impronta = ref<string | null>(null)
const calcolando = ref(false)

const genere = computed(() => {
  const nome = props.voce.nome.toLowerCase()
  if (/\.(jpe?g|png|gif|webp|avif|bmp)$/.test(nome)) return 'immagine'
  if (/\.(mp4|webm|mov|m4v)$/.test(nome)) return 'video'
  if (/\.(mp3|ogg|wav|m4a|opus|flac)$/.test(nome)) return 'audio'
  if (nome.endsWith('.pdf')) return 'pdf'
  if (/\.(txt|md|log|csv)$/.test(nome)) return 'testo'
  if (LINGUAGGI[estensione(nome)]) return 'codice'
  return 'nessuno'
})

/**
 * Il linguaggio da usare per l'evidenziazione, per estensione.
 *
 * Si dichiarano uno per uno invece di caricare highlight.js per intero: la
 * libreria completa pesa piu di un megabyte, e finirebbe tutta nella precache
 * della PWA per evidenziare cinque tipi di file.
 */
const LINGUAGGI: Record<string, string> = {
  ts: 'typescript',
  js: 'javascript',
  mjs: 'javascript',
  json: 'json',
  py: 'python',
  sh: 'bash',
  bash: 'bash',
  yml: 'yaml',
  yaml: 'yaml',
  toml: 'ini',
  ini: 'ini',
  conf: 'ini',
  sql: 'sql',
  css: 'css',
  html: 'xml',
  htm: 'xml',
  xml: 'xml',
  vue: 'xml',
}

function estensione(nome: string): string {
  return nome.split('.').pop()?.toLowerCase() ?? ''
}

/** Il contenuto evidenziato, gia trasformato in HTML da highlight.js. */
const evidenziato = computed(() => {
  if (testo.value === null) return ''
  const linguaggio = LINGUAGGI[estensione(props.voce.nome)]
  if (!linguaggio) return hljs.highlightAuto(testo.value).value
  return hljs.highlight(testo.value, { language: linguaggio, ignoreIllegals: true }).value
})

const inModifica = ref(false)

/** Lo strato colorato sotto l'area di testo, da tenere allineato allo scorrimento. */
const strato = ref<HTMLElement | null>(null)

function sincronizza(evento: Event): void {
  const area = evento.target as HTMLTextAreaElement
  if (!strato.value) return
  strato.value.scrollTop = area.scrollTop
  strato.value.scrollLeft = area.scrollLeft
}

/**
 * Il testo evidenziato con una riga vuota in coda.
 *
 * Senza, l'ultima riga scompare dallo strato colorato mentre la si scrive:
 * un `<pre>` che finisce con un a capo non lo mostra, mentre l'area di testo
 * ce l'ha e il cursore sta li.
 */
const evidenziatoConCoda = computed(() => evidenziato.value + '\n')

async function prepara(): Promise<void> {
  indirizzo.value = null
  errore.value = null
  impronta.value = null
  testo.value = null
  salvato.value = false
  if (genere.value === 'nessuno') return
  // Il codice non si consegna come file da mostrare nel riquadro: si legge il
  // testo e lo si evidenzia qui.
  if (genere.value === 'codice') {
    void mostraTesto()
    return
  }

  try {
    indirizzo.value = await indirizzoDownload(props.slug, props.voce.percorso, undefined, true)
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  }
}

// --- modifica del testo ---
// Solo per i file di testo e solo dove si può scrivere: aprire un editor su
// un file che poi non si riesce a salvare è un modo di far perdere tempo.
const testo = ref<string | null>(null)
const troncato = ref(false)
const salvando = ref(false)
const salvato = ref(false)

/** Carica il contenuto per la sola lettura, senza aprire l'editor. */
async function mostraTesto(): Promise<void> {
  inModifica.value = false
  try {
    const letto = await archivioApi.leggiTesto(props.slug, props.voce.percorso)
    testo.value = letto.contenuto
    troncato.value = letto.troncato
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  }
}

async function apriEditor(): Promise<void> {
  inModifica.value = true
  errore.value = null
  salvato.value = false
  try {
    const letto = await archivioApi.leggiTesto(props.slug, props.voce.percorso)
    testo.value = letto.contenuto
    troncato.value = letto.troncato
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  }
}

async function salvaTesto(): Promise<void> {
  if (testo.value === null) return
  salvando.value = true
  errore.value = null
  try {
    await archivioApi.salvaTesto(props.slug, props.voce.percorso, testo.value)
    salvato.value = true
    emit('salvato')
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    salvando.value = false
  }
}

async function calcolaImpronta(): Promise<void> {
  calcolando.value = true
  errore.value = null
  try {
    impronta.value = (await archivioApi.checksum(props.slug, props.voce.percorso)).valore
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    calcolando.value = false
  }
}

// In fondo, non accanto a `prepara`: con `immediate` il controllo parte
// subito, e `prepara` azzera anche `testo` e `salvato`, dichiarati piu' sotto.
// Eseguito prima della loro inizializzazione, il componente moriva con
// «Cannot access ... before initialization» e l'anteprima restava su «Carico...».
watch(
  () => props.voce.percorso,
  () => {
    void prepara()
    void leggiScatto()
    azzeraIngrandimento()
  },
  { immediate: true },
)
</script>

<template>
  <div
    class="velo"
    @click.self="emit('chiudi')"
  >
    <section
      ref="finestra"
      class="finestra"
      :class="{ 'finestra--intera': aSchermoIntero }"
      role="dialog"
      :aria-label="voce.nome"
    >
      <header class="testa">
        <span class="nome">{{ voce.nome }}</span>
        <span
          v-if="quante > 1 && posizione > 0"
          class="posizione"
        >{{ t('anteprima.posizione', { n: posizione, tot: quante }) }}</span>
        <button
          v-if="quante > 1"
          type="button"
          class="chiudi"
          :aria-label="t('anteprima.presentazione')"
          :title="t('anteprima.presentazione')"
          @click="alternaPresentazione"
        >
          {{ inPresentazione ? '❚❚' : '▶' }}
        </button>
        <button
          v-if="genere === 'immagine' || genere === 'video'"
          type="button"
          class="chiudi"
          :aria-label="t('anteprima.schermoIntero')"
          :title="t('anteprima.schermoIntero')"
          @click="alternaSchermoIntero"
        >
          {{ aSchermoIntero ? '⤡' : '⤢' }}
        </button>
        <button
          type="button"
          class="chiudi"
          :aria-label="t('comune.chiudi')"
          @click="emit('chiudi')"
        >
          ×
        </button>
      </header>

      <div
        class="corpo"
        @touchstart.passive="inizioTocco"
        @touchend.passive="fineTocco"
      >
        <button
          v-if="haPrecedente"
          type="button"
          class="freccia freccia--prima"
          :aria-label="t('anteprima.precedente')"
          @click="emit('precedente')"
        >
          ‹
        </button>
        <button
          v-if="haSuccessiva"
          type="button"
          class="freccia freccia--dopo"
          :aria-label="t('anteprima.successiva')"
          @click="emit('successiva')"
        >
          ›
        </button>

        <p
          v-if="errore"
          class="messaggio"
          role="alert"
        >
          {{ errore }}
        </p>

        <p
          v-else-if="genere === 'nessuno'"
          class="messaggio"
        >
          {{ t('anteprima.nonMostrabile') }}
        </p>

        <template v-if="testo !== null">
          <!-- Editor con evidenziazione: uno strato colorato sotto, l'area di
               testo sopra con il testo trasparente e il solo cursore visibile.
               Devono avere le stesse identiche metriche del carattere, o le
               due copie si sfalsano riga dopo riga. -->
          <div
            v-if="inModifica"
            class="editore"
          >
            <!-- eslint-disable vue/no-v-html -->
            <pre
              ref="strato"
              class="editore__strato hljs"
              aria-hidden="true"
            ><code v-html="evidenziatoConCoda" /></pre>
            <!-- eslint-enable vue/no-v-html -->
            <textarea
              v-model="testo"
              class="editore__testo"
              spellcheck="false"
              wrap="off"
              :aria-label="voce.nome"
              @scroll="sincronizza"
            />
          </div>
          <!-- L'HTML qui dentro lo produce highlight.js dal testo del file, non
               il file stesso: la libreria sostituisce i caratteri speciali
               prima di aggiungere i propri tag, quindi un file che contiene
               markup resta testo e non diventa codice eseguito. Il testo
               arriva dall'API di lettura, che serve solo file di testo. -->
          <!-- eslint-disable vue/no-v-html -->
          <pre
            v-else
            class="codice hljs"
          ><code v-html="evidenziato" /></pre>
          <!-- eslint-enable vue/no-v-html -->
        </template>

        <template v-else-if="indirizzo">
          <img
            v-if="genere === 'immagine'"
            :src="indirizzo"
            :alt="voce.nome"
            class="media"
            :class="{ 'media--ingrandita': ingrandimento > 1 }"
            :style="{
              transform: `translate(${spostamento.x}px, ${spostamento.y}px) scale(${ingrandimento})`,
            }"
            draggable="false"
            @wheel="rotella"
            @mousedown.prevent="iniziaTrascino"
            @mousemove="muovi"
            @mouseup="fermaTrascino"
            @mouseleave="fermaTrascino"
            @dblclick="azzeraIngrandimento"
          >
          <video
            v-else-if="genere === 'video'"
            :src="indirizzo"
            controls
            class="media"
          />
          <audio
            v-else-if="genere === 'audio'"
            :src="indirizzo"
            controls
            class="audio"
          />
          <iframe
            v-else
            :src="indirizzo"
            :title="voce.nome"
            class="riquadro"
          />
        </template>

        <p
          v-else
          class="messaggio"
        >
          {{ t('comune.carico') }}
        </p>
      </div>

      <section
        v-if="haDettagli"
        class="scatto"
      >
        <button
          type="button"
          class="scatto__testa"
          :aria-expanded="dettagliAperti"
          @click="dettagliAperti = !dettagliAperti"
        >
          <span>{{ t('anteprima.datiScatto') }}</span>
          <span aria-hidden="true">{{ dettagliAperti ? '▾' : '▸' }}</span>
        </button>

        <dl
          v-if="dettagliAperti && scatto"
          class="scatto__dati"
        >
          <template v-if="quandoScattata">
            <dt>{{ t('anteprima.quando') }}</dt>
            <dd>{{ quandoScattata }}</dd>
          </template>
          <template v-if="scatto.fotocamera">
            <dt>{{ t('anteprima.fotocamera') }}</dt>
            <dd>{{ scatto.fotocamera }}</dd>
          </template>
          <template v-if="scatto.obiettivo">
            <dt>{{ t('anteprima.obiettivo') }}</dt>
            <dd>{{ scatto.obiettivo }}</dd>
          </template>
          <template v-if="scatto.tempo || scatto.diaframma || scatto.iso || scatto.focale">
            <dt>{{ t('anteprima.esposizione') }}</dt>
            <dd>
              {{ [scatto.tempo, scatto.diaframma, scatto.iso ? `ISO ${scatto.iso}` : null, scatto.focale].filter(Boolean).join(' · ') }}
            </dd>
          </template>
          <template v-if="scatto.larghezza && scatto.altezza">
            <dt>{{ t('anteprima.dimensioni') }}</dt>
            <dd>{{ scatto.larghezza }} × {{ scatto.altezza }}</dd>
          </template>
          <template v-if="mappa">
            <dt>{{ t('anteprima.luogo') }}</dt>
            <dd>
              <a
                :href="mappa"
                target="_blank"
                rel="noopener noreferrer"
              >{{ t('anteprima.vediSullaMappa') }}</a>
            </dd>
          </template>
        </dl>
      </section>

      <footer class="piede">
        <button
          v-if="modificabile && (genere === 'testo' || genere === 'codice') && !inModifica"
          type="button"
          class="bottone"
          @click="apriEditor"
        >
          {{ t('anteprima.modifica') }}
        </button>
        <template v-if="inModifica">
          <button
            type="button"
            class="bottone"
            :disabled="salvando"
            @click="salvaTesto"
          >
            {{ salvando ? t('comune.carico') : t('comune.salva') }}
          </button>
          <span
            v-if="salvato"
            class="fatto"
            role="status"
          >{{ t('anteprima.salvato') }}</span>
          <span
            v-if="troncato"
            class="nota"
          >{{ t('anteprima.troncato') }}</span>
        </template>
        <button
          type="button"
          class="bottone"
          :disabled="calcolando"
          @click="calcolaImpronta"
        >
          {{ calcolando ? t('comune.carico') : t('anteprima.impronta') }}
        </button>
        <code
          v-if="impronta"
          class="impronta"
        >{{ impronta }}</code>
        <p
          v-if="impronta"
          class="nota"
        >
          {{ t('anteprima.improntaNota') }}
        </p>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.velo {
  position: fixed;
  z-index: 20;
  display: grid;
  padding: 1rem;
  background: rgb(0 0 0 / 65%);
  inset: 0;
  place-items: center;
}

.finestra {
  display: flex;
  flex-direction: column;
  width: min(60rem, 100%);
  max-height: 90vh;
  gap: 0.5rem;
  padding: 0.9rem 1rem 1rem;
  border-radius: var(--raggio);
  background: var(--superficie);
}

.testa {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.nome {
  overflow: hidden;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* A schermo intero la foto prende tutto: il fondo scuro toglie di mezzo
   l'ambiente e lascia solo l'immagine, che e' il punto. */
.finestra--intera {
  width: 100vw;
  max-width: none;
  height: 100vh;
  max-height: none;
  border-radius: 0;
  display: flex;
  flex-direction: column;
  background: #0b0f14;
  color: #e8eef6;
}

.finestra--intera .corpo {
  flex: 1;
  align-content: center;
  background: #0b0f14;
}

.finestra--intera .media {
  max-height: 88vh;
}

.media--ingrandita {
  cursor: grab;
}

.media {
  transform-origin: center;
  transition: transform 0.08s linear;
}

.scatto {
  border-top: 1px solid var(--bordo);
  padding: 0.5rem 0.9rem;
}

.scatto__testa {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  padding: 0.25rem 0;
  border: 0;
  background: none;
  color: var(--testo-tenue);
  font: inherit;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
}

.scatto__dati {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.2rem 0.9rem;
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
}

.scatto__dati dt {
  color: var(--testo-tenue);
}

.scatto__dati dd {
  margin: 0;
}

.posizione {
  font-size: 0.8rem;
  color: var(--testo-tenue);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* Sopra l'immagine, ai lati: e' dove si cercano, e su un telefono cadono
   sotto il pollice senza coprire il centro della foto. */
.freccia {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  width: 2.6rem;
  height: 2.6rem;
  display: grid;
  place-items: center;
  border: 1px solid var(--vetro-bordo);
  border-radius: 50%;
  background: var(--vetro-sfondo);
  backdrop-filter: blur(14px) saturate(180%);
  -webkit-backdrop-filter: blur(14px) saturate(180%);
  color: var(--testo);
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
}

.freccia--prima { left: 0.5rem; }
.freccia--dopo { right: 0.5rem; }

.chiudi {
  padding: 0 0.4rem;
  border: 0;
  background: none;
  color: var(--testo-tenue);
  cursor: pointer;
  font-size: 1.4rem;
  line-height: 1;
}

.corpo {
  position: relative;
  display: grid;
  min-height: 12rem;
  overflow: auto;
  place-items: center;
}

.media {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
}

.audio {
  width: min(30rem, 100%);
}

/* Il PDF sta in un riquadro isolato: non condivide nulla con la pagina, e
   quello che contiene resta fatto suo. */
.riquadro {
  width: 100%;
  height: 70vh;
  border: 0;
}

.messaggio,
.nota {
  margin: 0;
  color: var(--testo-tenue);
  font-size: 0.9rem;
}

.piede {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--bordo);
}

/* Le due copie del testo devono coincidere carattere per carattere: ogni
   proprieta' che sposta il testo va dichiarata identica su entrambe. */
.editore {
  position: relative;
  min-height: 20rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--sfondo);
  overflow: hidden;
}

.editore__strato,
.editore__testo {
  margin: 0;
  padding: 0.6rem;
  border: 0;
  font-family: ui-monospace, monospace;
  font-size: 0.82rem;
  line-height: 1.5;
  tab-size: 2;
  white-space: pre;
  overflow: auto;
}

.editore__strato {
  position: absolute;
  inset: 0;
  background: none;
  pointer-events: none;
}

.editore__testo {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 20rem;
  background: transparent;
  /* Il testo e' invisibile: quello che si legge e' lo strato sotto. Il cursore
     invece deve restare visibile, o non si capisce dove si sta scrivendo. */
  color: transparent;
  caret-color: var(--testo);
  resize: none;
}

.editore__testo::selection {
  background: color-mix(in srgb, var(--accento) 35%, transparent);
}

.fatto {
  color: var(--ok);
  font-size: 0.85rem;
}

.impronta {
  overflow-wrap: anywhere;
  font-size: 0.75rem;
  user-select: all;
}


.codice {
  margin: 0;
  padding: 0.9rem;
  overflow: auto;
  max-height: 60vh;
  border-radius: var(--raggio);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  tab-size: 2;
}
@media (width <= 40rem) {
  /* A tutto schermo: su un telefono una finestra con i margini spreca proprio
     lo spazio che serve a guardare la foto. Il velo ha un margine suo, che
     lasciava 16 pixel di bordo per lato: va tolto anche quello. */
  .velo {
    padding: 0;
  }

  .finestra {
    width: 100%;
    max-width: none;
    height: 100dvh;
    max-height: none;
    border-radius: 0;
    display: flex;
    flex-direction: column;
  }

  /* Senza, il corpo resta alto quanto il suo contenuto — 192 pixel su uno
     schermo da 812 — e la foto si guarda in un francobollo con sotto un
     pannello bianco vuoto. */
  .corpo {
    flex: 1;
    align-content: center;
    overflow: auto;
  }

  /* Bersagli piu' grandi e piu' in basso: in alto il pollice non arriva. */
  .freccia {
    width: 3rem;
    height: 3rem;
    top: auto;
    bottom: 1rem;
    transform: none;
  }
}
</style>
