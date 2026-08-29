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
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { archivioApi, indirizzoDownload, type Voce } from '@/api/archivio'

const props = defineProps<{ slug: string; voce: Voce }>()
const emit = defineEmits<{ chiudi: [] }>()

const { t } = useI18n()

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
  return 'nessuno'
})

async function prepara(): Promise<void> {
  indirizzo.value = null
  errore.value = null
  impronta.value = null
  if (genere.value === 'nessuno') return

  try {
    indirizzo.value = await indirizzoDownload(props.slug, props.voce.percorso, undefined, true)
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  }
}

watch(() => props.voce.percorso, prepara, { immediate: true })

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

.impronta {
  overflow-wrap: anywhere;
  font-size: 0.75rem;
  user-select: all;
}

.bottone {
  padding: 0.4rem 0.75rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: transparent;
  color: var(--testo);
  cursor: pointer;
  font: inherit;
  font-size: 0.85rem;
}

.bottone:disabled {
  cursor: default;
  opacity: 0.55;
}
</style>
