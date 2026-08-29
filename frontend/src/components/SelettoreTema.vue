<script setup lang="ts">
/**
 * Scelta del tema, con la stessa grafica a segmenti del selettore di lingua.
 *
 * Le icone al posto delle parole tengono il controllo compatto e leggibile
 * quanto quello della lingua, che ha etichette di due lettere.
 */
import { useI18n } from 'vue-i18n'

import { TEMI, useTemaStore, type Tema } from '@/stores/tema'

withDefaults(defineProps<{ compatto?: boolean }>(), { compatto: false })

const { t } = useI18n()
const tema = useTemaStore()

const PENNELLO =
  'M12 3a9 9 0 0 0 0 18c.8 0 1.5-.7 1.5-1.5 0-.4-.2-.8-.4-1-.3-.3-.4-.6-.4-1 0-.8.7-1.5 1.5-1.5H16a5 5 0 0 0 5-5c0-4.4-4-8-9-8Z M7.5 12.5a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z M9.5 8.5a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z M14.5 8.5a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z'

const ICONE: Record<Tema, string> = {
  chiaro:
    'M12 4V2 M12 22v-2 M4 12H2 M22 12h-2 M6 6 4.5 4.5 M19.5 19.5 18 18 M18 6l1.5-1.5 M4.5 19.5 6 18 M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z',
  auto: 'M12 3a9 9 0 1 0 0 18Z M12 3a9 9 0 0 1 0 18',
  scuro: 'M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z',
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
        <path :d="PENNELLO" />
      </svg>
    </span>

    <span
      v-if="!compatto"
      class="etichetta"
    >{{ t('tema.titolo') }}</span>

    <div
      class="segmenti"
      role="group"
      :aria-label="t('tema.titolo')"
    >
      <button
        v-for="v in TEMI"
        :key="v"
        type="button"
        class="segmento"
        :class="{ 'segmento--scelto': tema.tema === v }"
        :aria-pressed="tema.tema === v"
        :title="t(`tema.${v}`)"
        :aria-label="t(`tema.${v}`)"
        @click="tema.imposta(v)"
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
  --tinta: var(--tinta-tema);
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
    inset 0 1px 0 rgb(255 255 255 / 45%),
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
