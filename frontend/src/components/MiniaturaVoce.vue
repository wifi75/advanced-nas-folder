<script setup lang="ts">
/**
 * Miniatura di un'immagine nella vista a galleria.
 *
 * L'indirizzo non si chiede subito: ogni miniatura richiede un gettone
 * all'API, e una cartella con qualche centinaio di foto ne genererebbe
 * altrettante richieste all'apertura, per immagini che nessuno ha ancora
 * guardato. Il gettone viene chiesto quando la miniatura entra nello schermo.
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { indirizzoMiniatura } from '@/api/archivio'

const props = defineProps<{ slug: string; percorso: string; nome: string }>()

/** Un video ha la stessa miniatura di una foto: senza un segno, in una
 *  cartella mista non si distinguono. */
const eVideo = computed(() => /\.(mp4|m4v|mov|mkv|webm|avi)$/i.test(props.nome))

const indirizzo = ref<string | null>(null)
const fallito = ref(false)
const elemento = ref<HTMLElement | null>(null)
let osservatore: IntersectionObserver | null = null

async function chiedi(): Promise<void> {
  try {
    // La miniatura e non l'originale: una cartella di foto pesa gigabyte, e
    // scaricarle intere per mostrarle a 150 pixel satura la rete.
    indirizzo.value = await indirizzoMiniatura(props.slug, props.percorso)
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
    <span
      v-if="eVideo && indirizzo && !fallito"
      class="segno-video"
      aria-hidden="true"
    >▶</span>
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

.segno-video {
  position: absolute;
  right: 0.3rem;
  bottom: 0.3rem;
  display: grid;
  place-items: center;
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 50%;
  background: rgb(0 0 0 / 55%);
  color: #fff;
  font-size: 0.6rem;
  line-height: 1;
}

.miniatura {
  position: relative;
}

.miniatura img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
