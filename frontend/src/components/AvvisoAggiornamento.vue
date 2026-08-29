<script setup lang="ts">
/**
 * Avviso di aggiornamento disponibile.
 *
 * Il service worker scarica la versione nuova ma **non la applica da solo**:
 * su un pannello che monta filesystem, ricaricare il codice mentre qualcuno
 * sta configurando un mount è peggio che restare una versione indietro per
 * qualche minuto. Si avvisa, e decide chi sta lavorando.
 */
import { useI18n } from 'vue-i18n'
import { useRegisterSW } from 'virtual:pwa-register/vue'

const { t } = useI18n()

const { needRefresh, offlineReady, updateServiceWorker } = useRegisterSW()

function aggiorna(): void {
  void updateServiceWorker(true)
}

function chiudi(): void {
  needRefresh.value = false
  offlineReady.value = false
}
</script>

<template>
  <div
    v-if="needRefresh || offlineReady"
    class="avviso"
    role="status"
  >
    <span class="testo">
      {{ needRefresh ? t('pwa.aggiornamento') : t('pwa.prontoOffline') }}
    </span>
    <button
      v-if="needRefresh"
      type="button"
      class="principale"
      @click="aggiorna"
    >
      {{ t('pwa.ricarica') }}
    </button>
    <button
      type="button"
      class="chiudi"
      :aria-label="t('comune.chiudi')"
      @click="chiudi"
    >
      ×
    </button>
  </div>
</template>

<style scoped>
.avviso {
  position: fixed;
  inset-block-end: 1rem;
  inset-inline: 1rem;
  margin-inline: auto;
  inline-size: fit-content;
  max-inline-size: min(460px, calc(100% - 2rem));
  z-index: 30;

  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 0.85rem;
  font-size: 0.875rem;

  background: var(--vetro-sfondo);
  border: 1px solid var(--vetro-bordo);
  border-radius: 12px;
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  box-shadow:
    inset 0 1px 0 var(--vetro-luce),
    var(--ombra);
}

.testo {
  flex: 1;
  min-inline-size: 0;
}

button {
  flex: none;
  font: inherit;
  cursor: pointer;
  border-radius: 8px;
}

.principale {
  padding: 0.35rem 0.75rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--accento-testo);
  background: var(--accento);
  border: none;
}

.chiudi {
  inline-size: 26px;
  block-size: 26px;
  display: grid;
  place-items: center;
  line-height: 1;
  color: var(--testo-tenue);
  background: transparent;
  border: 1px solid var(--bordo);
}
</style>
