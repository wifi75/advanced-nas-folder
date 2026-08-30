<script setup lang="ts">
/**
 * Creazione di una condivisione.
 *
 * Il percorso esportato si sceglie da un elenco letto dal NAS, non si digita:
 * indovinarlo a memoria è il modo più comune di sbagliare.
 */
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { mountsApi, type Esportazione, type NuovoMount } from '@/api/mounts'
import { ApiError } from '@/api/client'
import { useMountsStore } from '@/stores/mounts'

const emit = defineEmits<{ chiudi: []; creato: [] }>()

const mounts = useMountsStore()
const { t } = useI18n()

const server = ref('')
const esportazioni = ref<Esportazione[]>([])
const versioni = ref<string[]>([])
const scopertaInCorso = ref(false)
const erroreScoperta = ref('')

const form = ref<NuovoMount>({
  slug: '',
  label: '',
  server: '',
  export_path: '',
  nfs_version: '3',
  automount: true,
  idle_timeout: 600,
  consenti_scrittura: false,
})

const salvataggio = ref(false)

/** Il NAS espone la versione 4? Se no, chiederla farebbe fallire il mount. */
const supportaV4 = computed(() => versioni.value.some((v) => v.startsWith('4')))

const puoSalvare = computed(
  () => form.value.slug !== '' && form.value.label !== '' && form.value.export_path !== '',
)

async function scopri(): Promise<void> {
  if (!server.value) return
  scopertaInCorso.value = true
  erroreScoperta.value = ''
  esportazioni.value = []
  try {
    const risultato = await mountsApi.scopri(server.value)
    esportazioni.value = risultato.esportazioni
    versioni.value = risultato.versioni
    form.value.server = risultato.server
    if (risultato.esportazioni.length === 0) {
      erroreScoperta.value = t('nuovoMount.nessunaEsportazione')
    }
  } catch (e) {
    erroreScoperta.value = e instanceof ApiError ? e.message : t('errori.imprevisto')
  } finally {
    scopertaInCorso.value = false
  }
}

function scegli(percorso: string): void {
  form.value.export_path = percorso
  if (!form.value.slug) {
    // Proposta di identificatore ricavata dal nome della cartella.
    form.value.slug = (percorso.split('/').pop() ?? '')
      .toLowerCase()
      .replace(/[^a-z0-9-]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 63)
  }
  if (!form.value.label) form.value.label = percorso.split('/').pop() ?? percorso
}

async function salva(): Promise<void> {
  salvataggio.value = true
  const fatto = await mounts.crea(form.value)
  salvataggio.value = false
  if (fatto) emit('creato')
}
</script>

<template>
  <div
    class="velo"
    @click.self="emit('chiudi')"
  >
    <section
      class="pannello"
      role="dialog"
      aria-labelledby="titolo-nuovo"
    >
      <h2 id="titolo-nuovo">
        {{ t('nuovoMount.titolo') }}
      </h2>

      <!-- 1. scoperta -->
      <div class="passo">
        <label class="campo">
          <span>{{ t('nuovoMount.indirizzoNas') }}</span>
          <div class="riga">
            <input
              v-model="server"
              type="text"
              placeholder="192.168.1.10"
              @keydown.enter.prevent="scopri"
            >
            <button
              class="bottone bottone--principale"
              type="button"
              :disabled="!server || scopertaInCorso"
              @click="scopri"
            >
              {{ scopertaInCorso ? t('nuovoMount.cercando') : t('nuovoMount.cerca') }}
            </button>
          </div>
        </label>

        <p
          v-if="erroreScoperta"
          class="errore"
          role="alert"
        >
          {{ erroreScoperta }}
        </p>

        <ul
          v-if="esportazioni.length"
          class="esportazioni"
        >
          <li
            v-for="e in esportazioni"
            :key="e.percorso"
          >
            <button
              type="button"
              class="esportazione"
              :class="{ scelta: form.export_path === e.percorso }"
              @click="scegli(e.percorso)"
            >
              <span class="percorso">{{ e.percorso }}</span>
              <span class="client">{{ t('nuovoMount.consentitoA', { client: e.client }) }}</span>
            </button>
          </li>
        </ul>

        <p
          v-if="versioni.length && !supportaV4"
          class="nota"
        >
          {{ t('nuovoMount.soloVersioni', { versioni: versioni.join(', ') }) }}
        </p>
      </div>

      <!-- 2. dettagli -->
      <div
        v-if="form.export_path"
        class="passo"
      >
        <div class="doppio">
          <label class="campo">
            <span>{{ t('nuovoMount.nome') }}</span>
            <input
              v-model="form.label"
              type="text"
              maxlength="128"
            >
          </label>
          <label class="campo">
            <span>{{ t('nuovoMount.identificatore') }}</span>
            <input
              v-model="form.slug"
              type="text"
              pattern="[a-z0-9][a-z0-9-]*"
              maxlength="63"
            >
          </label>
        </div>

        <div class="doppio">
          <label class="campo">
            <span>{{ t('nuovoMount.versioneNfs') }}</span>
            <select v-model="form.nfs_version">
              <option value="3">
                3
              </option>
              <option
                value="4.1"
                :disabled="versioni.length > 0 && !supportaV4"
              >
                4.1
              </option>
              <option
                value="4.2"
                :disabled="versioni.length > 0 && !supportaV4"
              >
                4.2
              </option>
            </select>
          </label>
          <label class="campo interruttore">
            <input
              v-model="form.automount"
              type="checkbox"
            >
            <span>{{ t('nuovoMount.montaARichiesta') }}</span>
          </label>
        </div>

        <label class="campo interruttore rischio">
          <input
            v-model="form.consenti_scrittura"
            type="checkbox"
          >
          <span>
            <strong>{{ t('nuovoMount.consentiScrittura') }}</strong>
            <em>{{ t('nuovoMount.consentiScritturaDettaglio') }}</em>
          </span>
        </label>
      </div>

      <p
        v-if="mounts.errore"
        class="errore"
        role="alert"
      >
        {{ mounts.errore }}
      </p>

      <footer class="azioni">
        <button
          type="button"
          class="bottone bottone--tenue"
          @click="emit('chiudi')"
        >
          {{ t('comune.annulla') }}
        </button>
        <button
          class="bottone bottone--principale"
          type="button"
          :disabled="!puoSalvare || salvataggio"
          @click="salva"
        >
          {{ salvataggio ? t('nuovoMount.creando') : t('comune.crea') }}
        </button>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.velo {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgb(0 0 0 / 45%);
  z-index: 10;
}

.pannello {
  width: min(600px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 1.75rem;
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  box-shadow: var(--ombra);
}

h2 {
  margin: 0;
  font-size: 1.2rem;
}

.passo {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.875rem;
}

.doppio {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.9rem;
}

.riga {
  display: flex;
  gap: 0.5rem;
}

.riga input {
  flex: 1;
}

input[type='text'],
select {
  padding: 0.55rem 0.7rem;
  font: inherit;
  color: var(--testo);
  background: var(--sfondo);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}




.esportazioni {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 220px;
  overflow-y: auto;
}

.esportazione {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
  padding: 0.6rem 0.75rem;
  color: var(--testo);
  background: var(--sfondo);
  border: 1px solid var(--bordo);
  text-align: start;
  font-weight: 400;
}

.esportazione.scelta {
  border-color: var(--accento);
  background: var(--superficie-alt);
}

.percorso {
  font-family: ui-monospace, monospace;
  font-size: 0.875rem;
}

.client {
  font-size: 0.75rem;
  color: var(--testo-tenue);
}

.interruttore {
  flex-direction: row;
  align-items: flex-start;
  gap: 0.6rem;
}

.interruttore input {
  margin-block-start: 0.2rem;
}

.rischio {
  padding: 0.85rem 1rem;
  border: 1px solid var(--attenzione);
  border-left-width: 3px;
  border-radius: var(--raggio);
}

.rischio em {
  display: block;
  margin-block-start: 0.25rem;
  font-style: normal;
  font-size: 0.8125rem;
  color: var(--testo-tenue);
}

.nota {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--testo-tenue);
}

.errore {
  margin: 0;
  font-size: 0.875rem;
  color: var(--errore);
}

.azioni {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
}
</style>
