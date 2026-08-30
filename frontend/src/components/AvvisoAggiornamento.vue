<script setup lang="ts">
/**
 * Avviso che il pannello funziona anche senza rete, e aggiornamento automatico.
 *
 * Non c'è un avviso di aggiornamento da premere: chiedeva conferma in fondo
 * alla pagina, dove non veniva letto, e chi non lo notava restava sulla
 * versione vecchia convinto che l'aggiornamento del server non avesse
 * funzionato.
 *
 * Toglierlo non bastava. «Si applica al caricamento successivo» vale per chi
 * apre il pannello dopo; in una scheda **gia' aperta** quel caricamento non
 * arriva mai, e il pannello continua a mostrare la versione precedente finche'
 * non si svuota la cache a mano. Succede proprio a chi aggiorna il server e
 * subito dopo va a guardare il risultato: e' il caso peggiore, perche' e'
 * l'unica persona che conclude che l'aggiornamento sia rotto.
 *
 * Quindi: si controlla se c'e' una versione nuova a intervalli e ogni volta
 * che la scheda torna in primo piano, e quando quella nuova prende il
 * comando la pagina si ricarica da sola.
 */
import { onBeforeUnmount, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRegisterSW } from 'virtual:pwa-register/vue'

const { t } = useI18n()

/** Ogni quanto chiedere al server se c'e' una versione nuova. */
const CONTROLLO = 5 * 60 * 1000

const { offlineReady } = useRegisterSW({
  onRegisteredSW(_url, registrazione) {
    if (!registrazione) return

    const controlla = (): void => void registrazione.update().catch(() => undefined)

    const timer = window.setInterval(controlla, CONTROLLO)
    // Tornare sulla scheda e' il momento in cui si guarda se l'aggiornamento
    // ha avuto effetto: e' li' che serve il controllo, non cinque minuti dopo.
    const alRitorno = (): void => {
      if (document.visibilityState === 'visible') controlla()
    }
    document.addEventListener('visibilitychange', alRitorno)

    onBeforeUnmount(() => {
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', alRitorno)
    })
  },
})

onMounted(() => {
  if (!('serviceWorker' in navigator)) return
  let ricaricando = false
  // `controllerchange` scatta quando la versione nuova prende il posto della
  // vecchia. La guardia evita il ciclo: senza, la pagina ricaricata scatena
  // di nuovo l'evento e si ricarica all'infinito.
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (ricaricando) return
    ricaricando = true
    window.location.reload()
  })
})

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
  inset-block-end: var(--fondo-sicuro);
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
