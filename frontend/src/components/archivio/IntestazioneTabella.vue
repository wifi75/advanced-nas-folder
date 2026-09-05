<script setup lang="ts">
/**
 * Disposizione "Tabella densa": intestazione minima — titolo e briciole
 * sulla stessa riga — per lasciare più spazio verticale alla tabella vera
 * e propria, che vive in ArchivioView.vue (solo quando la vista è
 * "Elenco": vedi la nota lì).
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
  /** Non mostrate qui: servono solo alle disposizioni Laterale/Riepilogo,
   *  ma fanno parte del contratto comune delle 5 intestazioni. */
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
  <header class="intestazione intestazione--slim">
    <div class="riga-titolo">
      <h1 class="titolo titolo--slim">
        {{ titolo }}
      </h1>
      <nav
        class="briciole"
        :aria-label="t('archivio.percorso')"
      >
        <button
          type="button"
          class="briciola"
          @click="$emit('vai-a', '')"
        >
          {{ t('archivio.radice') }}
        </button>
        <template
          v-for="[nome, p] in briciole"
          :key="p"
        >
          <span
            class="briciole__separatore"
            aria-hidden="true"
          >/</span>
          <button
            type="button"
            class="briciola"
            @click="$emit('vai-a', p)"
          >
            {{ nome }}
          </button>
        </template>
      </nav>
    </div>
    <p
      v-if="descrizione"
      class="descrizione"
    >
      {{ descrizione }}
    </p>

    <div class="strumenti">
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

      <button
        type="button"
        class="bottone bottone--tenue"
        @click="$emit('scarica-cartella')"
      >
        {{ t('archivio.scaricaCartella') }}
      </button>

      <div
        class="rimappa-vetro"
        style="--vetro-sfondo: var(--vetro-sfondo-pub); --vetro-bordo: var(--vetro-bordo-pub); --vetro-luce: var(--vetro-luce-pub)"
      >
        <SelettoreDisposizione compatto />
      </div>
    </div>

    <div
      v-if="puoScrivere"
      class="riga-secondaria"
    >
      <Caricamenti
        :slug="slug"
        :percorso="percorso"
        @caricato="$emit('caricato')"
      />
      <form
        class="riga-form"
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
  </header>

  <slot />
</template>

<style scoped>
@import '@/assets/archivio-comune.css';

.intestazione--slim {
  gap: 0.5rem;
}

.riga-titolo {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.75rem;
}

.titolo--slim {
  font-size: 1.15rem;
}

.riga-secondaria {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 0.6rem;
}
</style>
