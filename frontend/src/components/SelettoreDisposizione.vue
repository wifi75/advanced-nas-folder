<script setup lang="ts">
/**
 * Scelta della disposizione della pagina "File", stessa grafica a segmenti
 * di `SelettoreTema.vue`/`SelettoreLingua.vue` — cinque icone invece di tre.
 *
 * Usato sempre `compatto` dentro `ArchivioView.vue`: quella pagina non ha
 * mai la barra laterale del pannello (vedi `router/index.ts`,
 * `meta.senzaMenu`), quindi qui non c'è mai lo spazio di un'etichetta per
 * esteso.
 */
import { useI18n } from 'vue-i18n'

import { DISPOSIZIONI, useDisposizioneStore, type Disposizione } from '@/stores/disposizione'

withDefaults(defineProps<{ compatto?: boolean }>(), { compatto: false })

const { t } = useI18n()
const disposizione = useDisposizioneStore()

const PASTIGLIA = 'M4 4h16v16H4Z M4 9h16 M9 9v11'

const ICONE: Record<Disposizione, string> = {
  unificata: 'M4 4h16v16H4Z M4 9h16',
  laterale: 'M4 4h16v16H4Z M9 4v16',
  riepilogo: 'M4 4h16v16H4Z M4 10h16',
  tabella: 'M4 4h16v16H4Z M4 9h16 M4 14h16 M9 4v16 M14 4v16',
  card: 'M4 4h7v7H4Z M13 4h7v7h-7Z M4 13h7v7H4Z M13 13h7v7h-7Z',
}
</script>

<template>
  <div
    class="selettore"
    :class="{ 'selettore--compatto': compatto }"
  >
    <span
      v-if="!compatto"
      class="pastiglia"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.7"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path :d="PASTIGLIA" />
      </svg>
    </span>

    <span
      v-if="!compatto"
      class="etichetta"
    >{{ t('disposizione.titolo') }}</span>

    <div
      class="segmenti"
      role="group"
      :aria-label="t('disposizione.titolo')"
    >
      <button
        v-for="v in DISPOSIZIONI"
        :key="v"
        type="button"
        class="segmento"
        :class="{ 'segmento--scelto': disposizione.disposizione === v }"
        :aria-pressed="disposizione.disposizione === v"
        :title="t(`disposizione.${v}`)"
        :aria-label="t(`disposizione.${v}`)"
        @click="disposizione.imposta(v)"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path :d="ICONE[v]" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.selettore {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.5rem 0.7rem;
  border-radius: 11px;
  font-size: 0.875rem;
  color: var(--testo);
  background: var(--vetro-sfondo);
  border: 1px solid var(--vetro-bordo);
  backdrop-filter: blur(14px) saturate(180%);
  -webkit-backdrop-filter: blur(14px) saturate(180%);
  box-shadow:
    inset 0 1px 0 var(--vetro-luce),
    var(--vetro-ombra);
}

.selettore--compatto {
  padding: 0;
  background: none;
  border: none;
  box-shadow: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  justify-content: center;
}

.pastiglia {
  --tinta: var(--tinta-disposizione);
  flex: none;
  inline-size: 28px;
  block-size: 28px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  background: linear-gradient(
    165deg,
    color-mix(in srgb, var(--tinta) 100%, white 18%),
    color-mix(in srgb, var(--tinta) 78%, black 22%)
  );
  box-shadow:
    inset 0 1px 0 var(--vetro-luce),
    0 2px 5px -1px color-mix(in srgb, var(--tinta) 55%, transparent);
}

.pastiglia svg {
  inline-size: 16px;
  block-size: 16px;
}

.etichetta {
  flex: 1;
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.segmenti {
  flex: none;
  display: flex;
  padding: 2px;
  gap: 2px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--testo) 8%, transparent);
  box-shadow: inset 0 1px 2px rgb(0 0 0 / 12%);
}

.segmento {
  display: grid;
  place-items: center;
  inline-size: 26px;
  block-size: 22px;
  padding: 0;
  color: var(--testo-tenue);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.segmento svg {
  inline-size: 14px;
  block-size: 14px;
}

@media (prefers-reduced-motion: no-preference) {
  .segmento {
    transition:
      background 0.15s ease,
      color 0.15s ease;
  }
}

.segmento:hover {
  color: var(--testo);
}

.segmento--scelto {
  color: var(--testo);
  background: linear-gradient(
    170deg,
    color-mix(in srgb, var(--superficie) 100%, white 12%),
    var(--superficie)
  );
  box-shadow:
    inset 0 1px 0 var(--vetro-luce),
    0 1px 3px -1px rgb(0 0 0 / 30%);
}
</style>
