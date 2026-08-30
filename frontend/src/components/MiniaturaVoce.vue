<script setup lang="ts">
/**
 * Miniatura di un'immagine nella vista a galleria.
 *
 * L'indirizzo non si chiede subito: ogni miniatura richiede un gettone
 * all'API, e una cartella con qualche centinaio di foto ne genererebbe
 * altrettante richieste all'apertura, per immagini che nessuno ha ancora
 * guardato. Il gettone viene chiesto quando la miniatura entra nello schermo.
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'

import { indirizzoDownload } from '@/api/archivio'

const props = defineProps<{ slug: string; percorso: string; nome: string }>()

const indirizzo = ref<string | null>(null)
const fallito = ref(false)
const elemento = ref<HTMLElement | null>(null)
let osservatore: IntersectionObserver | null = null

async function chiedi(): Promise<void> {
  try {
    indirizzo.value = await indirizzoDownload(props.slug, props.percorso, undefined, true)
  } catch {
    // Una miniatura che non arriva non è un errore da mostrare: resta
    // l'icona del tipo di file, che è già un'informazione.
    fallito.value = true
  }
}

onMounted(() => {
  if (!elemento.value) return
  // Senza IntersectionObserver (contesti molto vecchi) si chiede e basta:
  // meglio qualche richiesta in più di una galleria vuota.
  if (typeof IntersectionObserver === 'undefined') {
    void chiedi()
    return
  }
  osservatore = new IntersectionObserver(
    (voci) => {
      if (voci.some((v) => v.isIntersecting)) {
        void chiedi()
        osservatore?.disconnect()
      }
    },
    { rootMargin: '200px' },
  )
  osservatore.observe(elemento.value)
})

onBeforeUnmount(() => osservatore?.disconnect())
</script>

<template>
  <span
    ref="elemento"
    class="miniatura"
  >
    <img
      v-if="indirizzo && !fallito"
      :src="indirizzo"
      :alt="nome"
      loading="lazy"
      decoding="async"
      @error="fallito = true"
    >
    <slot v-else />
  </span>
</template>

<style scoped>
.miniatura {
  display: grid;
  place-items: center;
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 0.35rem;
  background: var(--sfondo);
}

.miniatura img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
