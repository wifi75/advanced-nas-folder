<script setup lang="ts">
/**
 * Scelta della lingua.
 *
 * Non è un menu a tendina: è un selettore a segmenti con la stessa grafica di
 * vetro delle voci del menu, così non stona con il resto dell'interfaccia. Con
 * due sole lingue un elenco a comparsa nasconderebbe una scelta che sta
 * comodamente a vista.
 */
import { useI18n } from 'vue-i18n'

import { cambiaLingua, LINGUE, type Lingua } from '@/i18n'

withDefaults(defineProps<{ compatto?: boolean }>(), { compatto: false })

const { t, locale } = useI18n()

const GLOBO =
  'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z M3 12h18 M12 3c2.5 2.7 2.5 15.3 0 18 M12 3c-2.5 2.7-2.5 15.3 0 18'
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
        <path :d="GLOBO" />
      </svg>
    </span>

    <span
      v-if="!compatto"
      class="etichetta"
    >{{ t('comune.lingua') }}</span>

    <div
      class="segmenti"
      role="group"
      :aria-label="t('comune.lingua')"
    >
      <button
        v-for="l in LINGUE"
        :key="l.codice"
        type="button"
        class="segmento"
        :class="{ 'segmento--scelto': locale === l.codice }"
        :aria-pressed="locale === l.codice"
        :title="l.nome"
        @click="cambiaLingua(l.codice as Lingua)"
      >
        {{ l.codice.toUpperCase() }}
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

/* Stessa pastiglia delle voci di menu, con la sua tinta. */
.pastiglia {
  --tinta: var(--tinta-lingua);
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

/* --- selettore a segmenti --- */

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
  padding: 0.18rem 0.5rem;
  font: inherit;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--testo-tenue);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-variant-numeric: tabular-nums;
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
  /* Il segmento scelto è in rilievo, non piatto: sfumatura più un filo di
     luce in alto, come le pastiglie. */
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
