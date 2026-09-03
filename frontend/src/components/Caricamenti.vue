<script setup lang="ts">
/**
 * Caricamento dei file nella cartella corrente.
 *
 * I file vengono inviati a blocchi e uno alla volta. Uno alla volta di
 * proposito: caricarne cinque in parallelo su una linea domestica non li fa
 * arrivare prima, e rende ogni avanzamento illeggibile perché si muovono
 * tutti a scatti.
 *
 * Se un caricamento si interrompe, riprende da dove era arrivato: quanto è
 * già stato ricevuto lo dice il server, non questa pagina — che di sessione
 * in sessione non ricorda nulla.
 */
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { archivioApi } from '@/api/archivio'
import { BLOCCO, caricamentoApi, inviaBlocco } from '@/api/caricamento'
import { tokenCorrente } from '@/api/client'

const props = defineProps<{ slug: string; percorso: string }>()
const emit = defineEmits<{ caricato: [] }>()

const { t } = useI18n()

type Stato = 'attesa' | 'invio' | 'fatto' | 'errore' | 'annullato'

interface InCorso {
  file: File
  /** Percorso relativo dentro la cartella trascinata, se ce n'è uno. */
  dentro: string
  inviati: number
  stato: Stato
  errore: string | null
}

const coda = ref<InCorso[]>([])
const sopra = ref(false)
const lavorando = ref(false)
/** Alzata per fermare il ciclo: il blocco in volo finisce, poi ci si ferma. */
const fermare = ref(false)

const attivi = computed(() => coda.value.filter((c) => c.stato === 'invio' || c.stato === 'attesa'))

function percento(c: InCorso): number {
  return c.file.size === 0 ? 100 : Math.round((c.inviati / c.file.size) * 100)
}

function aggiungi(files: FileList | null): void {
  if (!files) return
  for (const file of Array.from(files)) {
    // Scegliendo una cartella il browser riempie `webkitRelativePath` con il
    // percorso interno: è così che si ricostruisce l'albero dall'altra parte.
    const relativo = (file as File & { webkitRelativePath?: string }).webkitRelativePath ?? ''
    const dentro = relativo.includes('/') ? relativo.slice(0, relativo.lastIndexOf('/')) : ''
    coda.value.push({ file, dentro, inviati: 0, stato: 'attesa', errore: null })
  }
  void lavora()
}

/** Crea le cartelle mancanti lungo il percorso, ignorando quelle che ci sono già. */
async function preparaCartelle(dentro: string): Promise<string> {
  let corrente = props.percorso
  for (const pezzo of dentro.split('/').filter(Boolean)) {
    try {
      await archivioApi.creaCartella(props.slug, corrente, pezzo)
    } catch {
      // Esiste già: è il caso normale dal secondo file in poi.
    }
    corrente = corrente ? `${corrente}/${pezzo}` : pezzo
  }
  return corrente
}

function suRilascio(evento: DragEvent): void {
  sopra.value = false
  aggiungi(evento.dataTransfer?.files ?? null)
}

function suScelta(evento: Event): void {
  const campo = evento.target as HTMLInputElement
  aggiungi(campo.files)
  // Azzerato perché scegliendo di nuovo lo stesso file l'evento non
  // scatterebbe: per il campo il valore non è cambiato.
  campo.value = ''
}

async function lavora(): Promise<void> {
  if (lavorando.value) return
  lavorando.value = true
  fermare.value = false

  try {
    for (const voce of coda.value) {
      if (fermare.value) break
      if (voce.stato !== 'attesa') continue
      await invia(voce)
    }
  } finally {
    lavorando.value = false
  }
}

async function invia(voce: InCorso): Promise<void> {
  voce.stato = 'invio'
  voce.errore = null

  try {
    const dove = voce.dentro ? await preparaCartelle(voce.dentro) : props.percorso

    // Da dove riprendere lo sa il server: un caricamento interrotto ieri
    // riparte oggi senza che questa pagina se lo sia ricordato.
    const stato = await caricamentoApi.stato(props.slug, dove, voce.file.name)
    if (stato.gia_presente) {
      voce.stato = 'errore'
      voce.errore = t('caricamento.esiste')
      return
    }
    voce.inviati = Math.min(stato.ricevuti, voce.file.size)

    while (voce.inviati < voce.file.size) {
      if (fermare.value) {
        voce.stato = 'attesa'
        return
      }
      const fine = Math.min(voce.inviati + BLOCCO, voce.file.size)
      voce.inviati = await inviaBlocco(
        props.slug,
        dove,
        voce.file.name,
        voce.file.slice(voce.inviati, fine),
        voce.inviati,
        tokenCorrente(),
      )
    }

    await caricamentoApi.completa(props.slug, dove, voce.file.name, voce.file.size)
    voce.stato = 'fatto'
    emit('caricato')
  } catch (e) {
    voce.stato = 'errore'
    voce.errore = e instanceof Error ? e.message : t('errori.generico')
  }
}

function riprova(voce: InCorso): void {
  voce.stato = 'attesa'
  voce.errore = null
  void lavora()
}

async function annulla(voce: InCorso): Promise<void> {
  fermare.value = true
  voce.stato = 'annullato'
  try {
    // Senza, il file parziale resterebbe sul NAS a occupare spazio senza che
    // nessuno sappia più cosa fosse.
    await caricamentoApi.annulla(props.slug, props.percorso, voce.file.name)
  } catch {
    /* se non si riesce a toglierlo lo si potrà riprendere: non è un guasto */
  }
  void lavora()
}

function pulisci(): void {
  coda.value = coda.value.filter((c) => c.stato === 'invio' || c.stato === 'attesa')
}
</script>

<template>
  <section class="caricamenti">
    <div
      class="zona"
      :class="{ 'zona--sopra': sopra }"
      @dragover.prevent="sopra = true"
      @dragleave="sopra = false"
      @drop.prevent="suRilascio"
    >
      <p class="zona__testo">
        {{ t('caricamento.trascina') }}
      </p>
      <label class="zona__scegli">
        {{ t('caricamento.scegli') }}
        <input
          type="file"
          multiple
          class="zona__campo"
          @change="suScelta"
        >
      </label>
      <label class="zona__scegli">
        {{ t('caricamento.scegliCartella') }}
        <input
          type="file"
          webkitdirectory
          class="zona__campo"
          @change="suScelta"
        >
      </label>
    </div>

    <ul
      v-if="coda.length"
      class="coda"
    >
      <li
        v-for="(c, i) in coda"
        :key="`${c.file.name}-${i}`"
        class="voce"
      >
        <div class="voce__testa">
          <span class="voce__nome">{{ c.dentro ? `${c.dentro}/${c.file.name}` : c.file.name }}</span>
          <span class="voce__stato">
            <template v-if="c.stato === 'fatto'">{{ t('caricamento.fatto') }}</template>
            <template v-else-if="c.stato === 'annullato'">
              {{ t('caricamento.annullato') }}
            </template>
            <template v-else-if="c.stato === 'errore'">{{ c.errore }}</template>
            <template v-else>{{ percento(c) }}%</template>
          </span>
        </div>

        <div
          v-if="c.stato === 'invio' || c.stato === 'attesa'"
          class="barra"
          role="progressbar"
          :aria-valuenow="percento(c)"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <div
            class="barra__pieno"
            :style="{ width: `${percento(c)}%` }"
          />
        </div>

        <div class="voce__azioni">
          <button
            v-if="c.stato === 'errore'"
            type="button"
            class="minuto"
            @click="riprova(c)"
          >
            {{ t('caricamento.riprova') }}
          </button>
          <button
            v-if="c.stato === 'invio' || c.stato === 'attesa'"
            type="button"
            class="minuto"
            @click="annulla(c)"
          >
            {{ t('comune.annulla') }}
          </button>
        </div>
      </li>
    </ul>

    <button
      v-if="coda.length && attivi.length === 0"
      type="button"
      class="minuto"
      @click="pulisci"
    >
      {{ t('caricamento.pulisci') }}
    </button>
  </section>
</template>

<style scoped>
.caricamenti {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

/* Solo usato da ArchivioView.vue: puo' contare sui token --vetro-*-pub che
   quella vista definisce su ".archivio" (le proprieta' CSS personalizzate
   attraversano lo scoping di Vue, seguono solo l'ereditarieta' del DOM). */
.zona {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.9rem;
  border: 1px dashed var(--vetro-bordo-pub);
  border-radius: var(--raggio);
  background: var(--vetro-sfondo-pub);
  backdrop-filter: blur(14px) saturate(180%);
  -webkit-backdrop-filter: blur(14px) saturate(180%);
  box-shadow: var(--vetro-ombra);
  color: var(--testo-tenue);
  font-size: 0.9rem;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.zona--sopra {
  border-color: var(--testo);
  background: var(--vetro-attivo-pub);
}

.zona__testo {
  margin: 0;
}

.zona__scegli {
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  color: var(--testo);
  cursor: pointer;
  font-size: 0.85rem;
}

/* Il campo vero è nascosto ma resta raggiungibile da tastiera: `display: none`
   lo toglierebbe anche alla navigazione con Tab. */
.zona__campo {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}

.coda {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.voce {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--superficie);
}

.voce__testa {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
}

.voce__nome {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voce__stato {
  flex: none;
  color: var(--testo-tenue);
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
}

.barra {
  height: 4px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--superficie-alt);
}

.barra__pieno {
  height: 100%;
  background: var(--accento);
  transition: width 0.2s ease;
}

.voce__azioni {
  display: flex;
  gap: 0.4rem;
}

.minuto {
  align-self: flex-start;
  padding: 0.2rem 0.5rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: transparent;
  color: var(--testo-tenue);
  cursor: pointer;
  font: inherit;
  font-size: 0.8rem;
}
</style>
