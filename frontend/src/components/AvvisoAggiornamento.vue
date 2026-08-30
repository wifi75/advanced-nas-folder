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
      class="bottone bottone--principale"
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
  /* Sopra il piè di pagina, non addosso: quello sta nel flusso e su una pagina
     corta — l'accesso, per esempio — finisce proprio al fondo dello schermo,
     dove questo avviso e fisso. Si sovrapponevano, e il testo dell'uno si
     leggeva attraverso l'altro. */
  inset-block-end: 4.5rem;
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
