<script setup lang="ts">
/**
 * Sottomenu a schede dentro una pagina.
 *
 * Serve dove una sola cosa — una condivisione, una pubblicazione — ha piu'
 * aspetti da governare: montaggio, accesso, permessi, collegamenti. Impilarli
 * uno sotto l'altro produce una pagina lunghissima in cui non si capisce dove
 * finisce un argomento e comincia il successivo, ed e' il motivo per cui il
 * pannello risultava confuso.
 *
 * La scheda scelta resta nell'indirizzo (`?scheda=`): ricaricando la pagina si
 * torna dove si era, e un collegamento a una scheda precisa si puo' mandare a
 * qualcuno.
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps<{ schede: { chiave: string; etichetta: string }[] }>()

const route = useRoute()
const router = useRouter()

const attiva = computed(() => {
  const richiesta = route.query.scheda
  const valida = props.schede.some((s) => s.chiave === richiesta)
  return valida ? String(richiesta) : (props.schede[0]?.chiave ?? '')
})

function scegli(chiave: string): void {
  // `replace` e non `push`: le schede non sono passi di navigazione, e
  // riempire la cronologia costringerebbe a premere «indietro» una volta per
  // ogni scheda guardata per uscire dalla pagina.
  void router.replace({ query: { ...route.query, scheda: chiave } })
}

defineExpose({ attiva })
</script>

<template>
  <div class="schede">
    <div
      class="schede__barra"
      role="tablist"
    >
      <button
        v-for="s in schede"
        :key="s.chiave"
        type="button"
        role="tab"
        class="scheda-voce"
        :class="{ 'scheda-voce--attiva': attiva === s.chiave }"
        :aria-selected="attiva === s.chiave"
        @click="scegli(s.chiave)"
      >
        {{ s.etichetta }}
      </button>
    </div>

    <div
      class="schede__corpo"
      role="tabpanel"
    >
      <slot :attiva="attiva" />
    </div>
  </div>
</template>

<style scoped>
.schede {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.schede__barra {
  display: flex;
  flex-wrap: wrap;
  gap: 0.15rem;
  border-bottom: 1px solid var(--bordo);
}

.scheda-voce {
  border: 0;
  border-bottom: 2px solid transparent;
  background: none;
  color: var(--testo-tenue);
  font: inherit;
  font-size: 0.9rem;
  font-weight: 500;
  padding: 0.5rem 0.9rem;
  margin-bottom: -1px;
  cursor: pointer;
}

.scheda-voce:hover {
  color: var(--testo);
}

.scheda-voce--attiva {
  color: var(--accento);
  border-bottom-color: var(--accento);
}

.schede__corpo {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
</style>
