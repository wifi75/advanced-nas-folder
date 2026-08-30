<script setup lang="ts">
/**
 * Gli indirizzi su cui una cartella pubblicata si raggiunge.
 *
 * Sta in un componente e non nella pagina perche compare in due posti — la
 * lista delle pubblicazioni e il dettaglio — e due copie divergerebbero: e gia
 * successo che l'elenco mostrasse solo l'identificatore mentre il resto
 * dell'indirizzo andava indovinato.
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{ slug: string }>()
const { t } = useI18n()

/** Indirizzo corto, sulla radice del sito: `https://sito/documenti`. */
function corto(): string {
  return `${window.location.origin}/${props.slug}`
}

/** Indirizzo completo, quello su cui il corto fa arrivare. */
function completo(): string {
  return `${window.location.origin}${import.meta.env.BASE_URL}archivio/${props.slug}`
}

const copiato = ref<string | null>(null)

async function copia(quale: string, testo: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(testo)
    copiato.value = quale
    setTimeout(() => {
      if (copiato.value === quale) copiato.value = null
    }, 2000)
  } catch {
    // Senza permesso sugli appunti (o fuori da HTTPS) l'indirizzo resta a
    // schermo e si seleziona a mano: meglio di un errore senza rimedio.
  }
}
</script>

<template>
  <div class="indirizzi">
    <p class="titolo">
      {{ t('share.daCondividere') }}
    </p>

    <div class="riga">
      <a
        class="valore"
        :href="corto()"
      >{{ corto() }}</a>
      <button
        type="button"
        class="copia"
        @click="copia('corto', corto())"
      >
        {{ copiato === 'corto' ? t('share.copiato') : t('share.copia') }}
      </button>
    </div>
    <p class="nota">
      {{ t('share.cortoNota') }}
    </p>

    <div class="riga">
      <a
        class="valore valore--tenue"
        :href="completo()"
      >{{ completo() }}</a>
      <button
        type="button"
        class="copia"
        @click="copia('completo', completo())"
      >
        {{ copiato === 'completo' ? t('share.copiato') : t('share.copia') }}
      </button>
    </div>
    <p class="nota">
      {{ t('share.completoNota') }}
    </p>
  </div>
</template>

<style scoped>
.indirizzi {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--bordo);
  border-radius: 0.5rem;
}

.titolo {
  margin: 0 0 0.15rem;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--testo-tenue);
}

.riga {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem;
}

.valore {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  word-break: break-all;
}

.valore--tenue {
  color: var(--testo-tenue);
  font-size: 0.9rem;
}

.nota {
  margin: 0 0 0.4rem;
  font-size: 0.78rem;
  color: var(--testo-tenue);
}

.copia {
  border: 1px solid var(--bordo);
  background: none;
  color: inherit;
  border-radius: 0.25rem;
  padding: 0.05rem 0.45rem;
  font-size: 0.75rem;
  cursor: pointer;
}

.copia:hover {
  background: var(--sfondo);
}
</style>
