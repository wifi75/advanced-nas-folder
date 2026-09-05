<script setup lang="ts">
/**
 * Disposizione "Barra laterale": azioni e riepilogo sempre visibili a
 * sinistra, il resto della pagina (passato come slot) a destra. È l'unica
 * delle 5 disposizioni che cambia la forma della pagina invece che solo
 * l'intestazione: per questo è l'unica con uno slot.
 */
import { useI18n } from 'vue-i18n'

import Caricamenti from '@/components/Caricamenti.vue'
import SelettoreDisposizione from '@/components/SelettoreDisposizione.vue'

type Vista = 'elenco' | 'griglia' | 'galleria'
const VISTE: Vista[] = ['elenco', 'griglia', 'galleria']

defineProps<{
  titolo: string
  descrizione: string | null
  briciole: Array<[string, string]>
  puoScrivere: boolean
  slug: string
  percorso: string
  operazione: boolean
  cercando: boolean
  hasRisultati: boolean
  vista: Vista
  mostraViste: boolean
  elementi: number
  dimensioneTotale: string
  ultimoCaricamento: string
}>()

defineEmits<{
  cerca: []
  'azzera-ricerca': []
  'scarica-cartella': []
  'crea-cartella': []
  'vai-a': [percorso: string]
  'cambia-vista': [vista: Vista]
  caricato: []
}>()

const termine = defineModel<string>('termine', { required: true })
const nuovaCartella = defineModel<string>('nuovaCartella', { required: true })

const { t } = useI18n()
</script>

<template>
  <div class="laterale">
    <aside class="rail">
      <h1 class="titolo">
        {{ titolo }}
      </h1>
      <p
        v-if="descrizione"
        class="descrizione"
      >
        {{ descrizione }}
      </p>

      <nav
        class="briciole briciole--verticale"
        :aria-label="t('archivio.percorso')"
      >
        <button
          type="button"
          class="briciola"
          @click="$emit('vai-a', '')"
        >
          {{ t('archivio.radice') }}
        </button>
        <button
          v-for="[nome, p] in briciole"
          :key="p"
          type="button"
          class="briciola"
          @click="$emit('vai-a', p)"
        >
          {{ nome }}
        </button>
      </nav>

      <div
        v-if="puoScrivere"
        class="azioni-rapide"
      >
        <Caricamenti
          :slug="slug"
          :percorso="percorso"
          @caricato="$emit('caricato')"
        />
        <form
          class="riga-form riga-form--verticale"
          @submit.prevent="$emit('crea-cartella')"
        >
          <input
            v-model="nuovaCartella"
            type="text"
            class="campo"
            :placeholder="t('operazioni.nuovaCartella')"
          >
          <button
            type="submit"
            class="bottone bottone--tenue"
            :disabled="operazione || nuovaCartella.trim() === ''"
          >
            {{ t('operazioni.crea') }}
          </button>
        </form>
      </div>

      <button
        type="button"
        class="bottone bottone--tenue"
        @click="$emit('scarica-cartella')"
      >
        {{ t('archivio.scaricaCartella') }}
      </button>

      <div class="riepilogo">
        <div class="riepilogo__voce">
          <span>{{ t('archivio.elementi') }}</span>
          <b>{{ elementi }}</b>
        </div>
        <div class="riepilogo__voce">
          <span>{{ t('archivio.spazio') }}</span>
          <b>{{ dimensioneTotale }}</b>
        </div>
        <div
          v-if="ultimoCaricamento"
          class="riepilogo__voce"
        >
          <span>{{ t('archivio.ultimoCaricamento') }}</span>
          <b>{{ ultimoCaricamento }}</b>
        </div>
      </div>

      <div
        class="rimappa-vetro"
        style="--vetro-sfondo: var(--vetro-sfondo-pub); --vetro-bordo: var(--vetro-bordo-pub); --vetro-luce: var(--vetro-luce-pub)"
      >
        <SelettoreDisposizione compatto />
      </div>
    </aside>

    <div class="contenuto">
      <div class="barra-top">
        <form
          class="cerca"
          @submit.prevent="$emit('cerca')"
        >
          <input
            v-model="termine"
            type="search"
            class="campo"
            :placeholder="t('ricerca.campo')"
            @search="$emit('cerca')"
            @keyup.enter="$emit('cerca')"
          >
          <button
            type="submit"
            class="bottone bottone--tenue"
            :disabled="termine.trim().length < 2 || cercando"
          >
            {{ t('ricerca.cerca') }}
          </button>
          <button
            v-if="hasRisultati"
            type="button"
            class="bottone bottone--tenue"
            @click="$emit('azzera-ricerca')"
          >
            {{ t('ricerca.azzera') }}
          </button>
        </form>

        <div
          v-if="mostraViste"
          class="viste"
          role="group"
          :aria-label="t('archivio.vista')"
        >
          <button
            v-for="v in VISTE"
            :key="v"
            type="button"
            class="vista"
            :class="{ 'vista--scelta': vista === v }"
            :aria-pressed="vista === v"
            @click="$emit('cambia-vista', v)"
          >
            {{ t(`archivio.vista${v.charAt(0).toUpperCase() + v.slice(1)}`) }}
          </button>
        </div>
      </div>

      <slot />
    </div>
  </div>
</template>

<style scoped>
@import '@/assets/archivio-comune.css';

.laterale {
  display: flex;
  align-items: flex-start;
  gap: 1.25rem;
}

.rail {
  flex: none;
  inline-size: 15rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  position: sticky;
  top: 1rem;
}

.briciole--verticale {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.1rem;
}

.azioni-rapide {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.riga-form--verticale {
  flex-direction: column;
  max-width: none;
}

.riepilogo {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.7rem;
  border: 1px solid var(--vetro-bordo-pub);
  border-radius: 12px;
  background: var(--vetro-sfondo-pub);
  box-shadow:
    inset 0 1px 0 var(--vetro-luce-pub),
    var(--vetro-ombra);
}

.riepilogo__voce {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.78rem;
  color: var(--testo-tenue);
}

.riepilogo__voce b {
  font-family: var(--font-mono);
  color: var(--testo);
  font-weight: 600;
}

.contenuto {
  flex: 1;
  min-inline-size: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.barra-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
}

@media (max-width: 46rem) {
  .laterale {
    flex-direction: column;
  }

  .rail {
    inline-size: auto;
    position: static;
  }
}
</style>
