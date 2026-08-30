<script setup lang="ts">
/**
 * Scelta di una cartella dentro una pubblicazione.
 *
 * Prima il percorso si scriveva a mano. Chi assegna un permesso non ha in
 * testa l'albero del NAS, e un percorso sbagliato non da' errore: crea un
 * permesso su una cartella che non esiste, che semplicemente non fa niente.
 * Il difetto si scopre quando qualcuno dice che non vede la cartella.
 *
 * Si scende un livello per volta invece di caricare tutto l'albero: su NFS
 * elencare ogni sottocartella di una fototeca sono centinaia di richieste, e
 * la scelta serve quasi sempre nei primi due o tre livelli.
 */
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { archivioApi } from '@/api/archivio'

const props = defineProps<{
  /** La pubblicazione in cui cercare. */
  slug: string
  /** Il percorso scelto. Vuoto = tutta la pubblicazione. */
  modelValue: string
}>()

const emit = defineEmits<{ 'update:modelValue': [valore: string] }>()

const { t } = useI18n()

const sottocartelle = ref<string[]>([])
const caricando = ref(false)
const errore = ref(false)

async function leggi(percorso: string): Promise<void> {
  caricando.value = true
  errore.value = false
  try {
    const contenuto = await archivioApi.contenuto(props.slug, percorso)
    sottocartelle.value = contenuto.voci.filter((v) => v.cartella).map((v) => v.nome)
  } catch {
    // Una cartella non leggibile non deve bloccare il modulo: resta la
    // possibilita' di scrivere il percorso a mano.
    sottocartelle.value = []
    errore.value = true
  } finally {
    caricando.value = false
  }
}

watch(() => [props.slug, props.modelValue], () => void leggi(props.modelValue), {
  immediate: true,
})

function scendi(nome: string): void {
  if (!nome) return
  emit('update:modelValue', props.modelValue ? `${props.modelValue}/${nome}` : nome)
}

function risali(): void {
  const parti = props.modelValue.split('/').filter(Boolean)
  parti.pop()
  emit('update:modelValue', parti.join('/'))
}
</script>

<template>
  <div class="scegli">
    <span class="scegli__titolo">{{ t('permessi.cartella') }}</span>

    <div class="scegli__riga">
      <button
        type="button"
        class="risali"
        :disabled="modelValue === ''"
        :title="t('scegliCartella.risali')"
        @click="risali"
      >
        ↑
      </button>
      <span class="scegli__ora">
        {{ modelValue || t('permessi.tutte') }}
      </span>
    </div>

    <select
      class="scegli__elenco"
      :disabled="caricando || sottocartelle.length === 0"
      :aria-label="t('scegliCartella.scendi')"
      @change="scendi(($event.target as HTMLSelectElement).value)"
    >
      <option value="">
        {{
          caricando
            ? t('comune.carico')
            : sottocartelle.length
              ? t('scegliCartella.scendi')
              : errore
                ? t('scegliCartella.nonLeggibile')
                : t('scegliCartella.nessuna')
        }}
      </option>
      <option
        v-for="c in sottocartelle"
        :key="c"
        :value="c"
      >
        {{ c }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.scegli {
  flex: 2;
  min-inline-size: 190px;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.scegli__titolo {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--testo-tenue);
}

.scegli__riga {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-inline-size: 0;
}

/* Il percorso scelto va letto tutto: e' l'unica cosa che dice davvero su
   quale cartella si sta per agire. */
.scegli__ora {
  flex: 1;
  min-inline-size: 0;
  padding: 0.4rem 0.55rem;
  font-family: var(--mono, ui-monospace, monospace);
  font-size: 0.8125rem;
  overflow-wrap: anywhere;
  background: var(--sfondo);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

.risali {
  inline-size: 30px;
  block-size: 30px;
  flex: none;
  display: grid;
  place-items: center;
  font: inherit;
  color: var(--testo);
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  cursor: pointer;
}

.risali:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
