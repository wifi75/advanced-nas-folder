<script setup lang="ts">
/**
 * Avviso che il pannello funziona anche senza rete.
 *
 * Non c'è più un avviso di aggiornamento da premere: il service worker applica
 * da solo la versione nuova al caricamento successivo. Prima chiedeva
 * conferma, e chi non notava l'avviso — in fondo alla pagina — restava sulla
 * versione vecchia convinto che l'aggiornamento non avesse funzionato.
 */
import { useI18n } from 'vue-i18n'
import { useRegisterSW } from 'virtual:pwa-register/vue'

const { t } = useI18n()

const { offlineReady } = useRegisterSW()

function chiudi(): void {
  offlineReady.value = false
}
</script>

<template>
  <div
    v-if="offlineReady"
    class="avviso"
    role="status"
  >
    <span class="testo">
      {{ t('pwa.prontoOffline') }}
    </span>
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
