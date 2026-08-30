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
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { archivioApi, indirizzoDownload, type Voce } from '@/api/archivio'

const props = defineProps<{ slug: string; voce: Voce; modificabile?: boolean }>()
const emit = defineEmits<{ chiudi: []; salvato: [] }>()

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

watch(() => props.voce.percorso, prepara, { immediate: true })

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
</script>

<template>
  <div
    class="velo"
    @click.self="emit('chiudi')"
  >
    <section
      class="finestra"
      role="dialog"
      :aria-label="voce.nome"
    >
      <header class="testa">
        <span class="nome">{{ voce.nome }}</span>
        <button
          type="button"
          class="chiudi"
          :aria-label="t('comune.chiudi')"
          @click="emit('chiudi')"
        >
          ×
        </button>
      </header>

      <div class="corpo">
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
</style>
