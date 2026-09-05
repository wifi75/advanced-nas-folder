<script setup lang="ts">
/**
 * Sfoglia le cartelle di un mount e ne mette in spunta più di una.
 *
 * A differenza di `ScegliCartella.vue` (un solo percorso, dentro una
 * pubblicazione già esistente) qui si sceglie **prima** che la pubblicazione
 * esista: si naviga la condivisione NFS grezza, e le selezioni fatte a
 * profondità diverse restano tutte insieme, non solo quella dell'ultimo
 * livello visitato.
 */
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { mountsApi } from '@/api/mounts'

const props = defineProps<{
  mountId: number
  /** Percorsi già selezionati, anche a profondità diverse. */
  modelValue: string[]
}>()

const emit = defineEmits<{ 'update:modelValue': [valori: string[]] }>()

const { t } = useI18n()

const percorsoAttuale = ref('')
const cartelle = ref<{ nome: string; percorso: string }[]>([])
const caricando = ref(false)
const errore = ref(false)

async function leggi(): Promise<void> {
  caricando.value = true
  errore.value = false
  try {
    cartelle.value = await mountsApi.cartelle(props.mountId, percorsoAttuale.value)
  } catch {
    cartelle.value = []
    errore.value = true
  } finally {
    caricando.value = false
  }
}

watch(() => [props.mountId, percorsoAttuale.value], () => void leggi(), { immediate: true })

function apri(percorso: string): void {
  percorsoAttuale.value = percorso
}

function risali(): void {
  const parti = percorsoAttuale.value.split('/').filter(Boolean)
  parti.pop()
  percorsoAttuale.value = parti.join('/')
}

function selezionata(percorso: string): boolean {
  return props.modelValue.includes(percorso)
}

function alterna(percorso: string): void {
  emit(
    'update:modelValue',
    selezionata(percorso)
      ? props.modelValue.filter((p) => p !== percorso)
      : [...props.modelValue, percorso],
  )
}

function rimuovi(percorso: string): void {
  emit(
    'update:modelValue',
    props.modelValue.filter((p) => p !== percorso),
  )
}
</script>

<template>
  <div class="sfoglia">
    <div class="sfoglia__contenitore">
      <div class="sfoglia__barra">
        <button
          type="button"
          class="sfoglia__su"
          :disabled="percorsoAttuale === ''"
          :title="t('scegliCartella.risali')"
          @click="risali"
        >
          ↑
        </button>
        <span class="sfoglia__briciole">
          <template
            v-for="(parte, indice) in percorsoAttuale.split('/').filter(Boolean)"
            :key="indice"
          >
            <span class="sep">/</span>
            <span>{{ parte }}</span>
          </template>
        </span>
      </div>

      <p
        v-if="caricando"
        class="sfoglia__stato"
      >
        {{ t('comune.carico') }}
      </p>
      <p
        v-else-if="errore"
        class="sfoglia__stato"
      >
        {{ t('scegliCartella.nonLeggibile') }}
      </p>
      <p
        v-else-if="cartelle.length === 0"
        class="sfoglia__stato"
      >
        {{ t('scegliCartella.nessuna') }}
      </p>
      <div
        v-else
        class="sfoglia__righe"
      >
        <div
          v-for="c in cartelle"
          :key="c.percorso"
          class="sfoglia__riga"
          :class="{ 'sfoglia__riga--selezionata': selezionata(c.percorso) }"
        >
          <input
            type="checkbox"
            :checked="selezionata(c.percorso)"
            @change="alterna(c.percorso)"
          >
          <span
            class="sfoglia__nome"
            @click="apri(c.percorso)"
          >{{ c.nome }}</span>
          <button
            type="button"
            class="sfoglia__apri"
            @click="apri(c.percorso)"
          >
            {{ t('sfogliaMount.apri') }} ›
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="modelValue.length"
      class="sfoglia__selezione"
    >
      <span class="sfoglia__selezione-etichetta">
        {{ t('sfogliaMount.selezionate', { n: modelValue.length }, modelValue.length) }}
      </span>
      <span
        v-for="p in modelValue"
        :key="p"
        class="chip"
      >
        {{ p }}
        <button
          type="button"
          :title="t('comune.elimina')"
          @click="rimuovi(p)"
        >
          ✕
        </button>
      </span>
    </div>
    <p class="sfoglia__aiuto">
      {{ t('sfogliaMount.aiuto') }}
    </p>
  </div>
</template>

<style scoped>
.sfoglia {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sfoglia__contenitore {
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  overflow: hidden;
  background: var(--superficie);
}

.sfoglia__barra {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.65rem;
  background: var(--superficie-alt);
  border-bottom: 1px solid var(--bordo);
  font-size: 0.82rem;
}

.sfoglia__su {
  inline-size: 26px;
  block-size: 26px;
  flex: none;
  display: grid;
  place-items: center;
  font: inherit;
  color: var(--testo);
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: 6px;
  cursor: pointer;
}

.sfoglia__su:disabled {
  opacity: 0.4;
  cursor: default;
}

.sfoglia__briciole {
  overflow-wrap: anywhere;
}

.sfoglia__briciole .sep {
  color: var(--testo-tenue);
  margin-inline-end: 0.25rem;
}

.sfoglia__stato {
  margin: 0;
  padding: 0.65rem;
  font-size: 0.8125rem;
  font-style: italic;
  color: var(--testo-tenue);
}

.sfoglia__righe {
  max-height: 14rem;
  overflow-y: auto;
}

.sfoglia__riga {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.45rem 0.65rem;
  border-bottom: 1px solid color-mix(in srgb, var(--bordo) 60%, transparent);
}

.sfoglia__riga:last-child {
  border-bottom: none;
}

.sfoglia__riga--selezionata {
  background: color-mix(in srgb, var(--tinta-nfs, var(--accento)) 8%, transparent);
}

.sfoglia__riga input {
  inline-size: 16px;
  block-size: 16px;
  flex: none;
  cursor: pointer;
}

.sfoglia__nome {
  flex: 1;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
}

.sfoglia__nome:hover {
  text-decoration: underline;
}

.sfoglia__apri {
  flex: none;
  padding: 0.15rem 0.5rem;
  font: inherit;
  font-size: 0.75rem;
  color: var(--testo-tenue);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.sfoglia__apri:hover {
  color: var(--accento);
  background: var(--superficie-alt);
}

.sfoglia__selezione {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

.sfoglia__selezione-etichetta {
  font-size: 0.78rem;
  color: var(--testo-tenue);
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.55rem;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--accento);
  background: color-mix(in srgb, var(--accento) 12%, var(--superficie));
  border: 1px solid color-mix(in srgb, var(--accento) 30%, var(--bordo));
  border-radius: 999px;
}

.chip button {
  all: unset;
  cursor: pointer;
  line-height: 1;
  opacity: 0.65;
}

.chip button:hover {
  opacity: 1;
}

.sfoglia__aiuto {
  margin: 0;
  font-size: 0.78rem;
  color: var(--testo-tenue);
}
</style>
