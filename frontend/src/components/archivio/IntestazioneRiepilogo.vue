<script setup lang="ts">
/**
 * Disposizione "Intestazione con riepilogo": una banda in alto con le
 * statistiche della cartella (elementi, spazio, ultimo caricamento) e le
 * azioni principali sempre in vista, prima ancora di scorrere alla lista.
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
  <header class="intestazione">
    <div class="riepilogo">
      <div class="riepilogo__titolo">
        <h1 class="titolo">
          {{ titolo }}
        </h1>
        <p
          v-if="descrizione"
          class="descrizione"
        >
          {{ descrizione }}
        </p>
      </div>

      <div class="riepilogo__stat">
        <b>{{ elementi }}</b>
        <span>{{ t('archivio.elementi') }}</span>
      </div>
      <div class="riepilogo__stat">
        <b>{{ dimensioneTotale }}</b>
        <span>{{ t('archivio.spazio') }}</span>
      </div>
      <div
        v-if="ultimoCaricamento"
        class="riepilogo__stat"
      >
        <b>{{ ultimoCaricamento }}</b>
        <span>{{ t('archivio.ultimoCaricamento') }}</span>
      </div>

      <div class="riepilogo__azioni">
        <div
          class="rimappa-vetro"
          style="--vetro-sfondo: var(--vetro-sfondo-pub); --vetro-bordo: var(--vetro-bordo-pub); --vetro-luce: var(--vetro-luce-pub)"
        >
          <SelettoreDisposizione compatto />
        </div>
        <button
          type="button"
          class="bottone bottone--tenue"
          @click="$emit('scarica-cartella')"
        >
          {{ t('archivio.scaricaCartella') }}
        </button>
      </div>
    </div>

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
    </div>
  </header>

  <Caricamenti
    v-if="puoScrivere"
    :slug="slug"
    :percorso="percorso"
    @caricato="$emit('caricato')"
  />

  <form
    v-if="puoScrivere"
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

  <slot />
</template>

<style scoped>
@import '@/assets/archivio-comune.css';

.riepilogo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1.25rem;
  padding: 1rem 1.1rem;
  border: 1px solid var(--vetro-bordo-pub);
  border-radius: 14px;
  background: var(--vetro-sfondo-pub);
  backdrop-filter: blur(14px) saturate(180%);
  -webkit-backdrop-filter: blur(14px) saturate(180%);
  box-shadow:
    inset 0 1px 0 var(--vetro-luce-pub),
    var(--vetro-ombra);
}

.riepilogo__titolo {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1 1 12rem;
}

.riepilogo__stat {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.riepilogo__stat b {
  font-family: var(--font-mono);
  font-size: 1.15rem;
  font-weight: 700;
}

.riepilogo__stat span {
  font-size: 0.7rem;
  color: var(--testo-tenue);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.riepilogo__azioni {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
