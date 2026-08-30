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
 * La scheda scelta resta nell'indirizzo: ricaricando la pagina si torna dove
 * si era, e un collegamento a una scheda precisa si puo' mandare a qualcuno.
 *
 * **Ogni gruppo di schede ha il proprio parametro** (`nome`). Con due gruppi
 * annidati — le sezioni di una pubblicazione, e dentro «Chi accede» le sue
 * quattro schede — un parametro solo li faceva litigare: cliccare una scheda
 * interna riscriveva quello che leggeva anche la barra esterna, che non
 * riconosceva il valore e ripiegava sulla prima scheda. Il risultato era che
 * un clic su «Permessi per utente» buttava fuori dalla sezione.
 *
 * Il gruppo annidato si dichiara anche `livello: 'interno'`: due barre
 * identiche una dentro l'altra sembrano allo stesso livello, e non si capisce
 * piu' quale comanda quale.
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = withDefaults(
  defineProps<{
    schede: { chiave: string; etichetta: string }[]
    /** Il parametro nell'indirizzo. Va cambiato per ogni gruppo annidato. */
    nome?: string
    /** `interno`: gruppo dentro un altro, disegnato piu' sottomesso. */
    livello?: 'principale' | 'interno'
  }>(),
  { nome: 'scheda', livello: 'principale' },
)

const route = useRoute()
const router = useRouter()

const attiva = computed(() => {
  const richiesta = route.query[props.nome]
  const valida = props.schede.some((s) => s.chiave === richiesta)
  return valida ? String(richiesta) : (props.schede[0]?.chiave ?? '')
})

function scegli(chiave: string): void {
  // `replace` e non `push`: le schede non sono passi di navigazione, e
  // riempire la cronologia costringerebbe a premere «indietro» una volta per
  // ogni scheda guardata per uscire dalla pagina.
  void router.replace({ query: { ...route.query, [props.nome]: chiave } })
}

defineExpose({ attiva })
</script>

<template>
  <div class="schede">
    <div
      class="schede__barra"
      :class="{ 'schede__barra--interna': livello === 'interno' }"
      role="tablist"
    >
      <button
        v-for="s in schede"
        :key="s.chiave"
        type="button"
        role="tab"
        class="scheda-voce"
        :class="{
          'scheda-voce--attiva': attiva === s.chiave,
          'scheda-voce--interna': livello === 'interno',
        }"
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
  gap: 1.35rem;
}

/* Una barra segmentata, non testo nudo su una linea: le linguette devono
   sembrare qualcosa su cui si clicca anche prima di provarci. */
.schede__barra {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.2rem;
  padding: 0.25rem;
  border: 1px solid var(--vetro-bordo);
  border-radius: 12px;
  background: var(--vetro-sfondo);
  backdrop-filter: blur(14px) saturate(180%);
  -webkit-backdrop-filter: blur(14px) saturate(180%);
  box-shadow: inset 0 1px 0 var(--vetro-luce);
  align-self: flex-start;
  max-width: 100%;
}

.scheda-voce {
  border: 0;
  border-radius: 9px;
  background: none;
  color: var(--testo-tenue);
  font: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.4rem 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.12s ease, color 0.12s ease;
}

.scheda-voce:hover {
  color: var(--testo);
}

.scheda-voce--attiva {
  /* Stessa formula della scheda di stato: sfumatura leggera della tinta e
     testo dello stesso colore. Bianco su bianco non diceva quale fosse
     attiva. */
  color: var(--accento);
  background:
    linear-gradient(
      158deg,
      color-mix(in srgb, var(--accento) 20%, var(--superficie)),
      color-mix(in srgb, var(--accento) 8%, var(--superficie))
    );
  box-shadow:
    inset 0 1px 0 var(--vetro-luce),
    var(--vetro-ombra);
}

/* Il gruppo annidato non e' una barra: sono linguette sottolineate, piu'
   piccole e senza fondo proprio. Cosi' si legge come «dentro» la scheda
   aperta invece che come una seconda navigazione allo stesso livello. */
.schede__barra--interna {
  gap: 0.35rem;
  padding: 0;
  border: 0;
  border-block-end: 1px solid var(--bordo);
  border-radius: 0;
  background: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  box-shadow: none;
  align-self: stretch;
}

.scheda-voce--interna {
  border-radius: 0;
  padding: 0.35rem 0.1rem;
  margin-inline-end: 0.9rem;
  font-size: 0.8125rem;
  border-block-end: 2px solid transparent;
  margin-block-end: -1px;
}

.scheda-voce--interna.scheda-voce--attiva {
  background: none;
  box-shadow: none;
  color: var(--accento);
  border-block-end-color: var(--accento);
}

.schede__corpo {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
</style>
