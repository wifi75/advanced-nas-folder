<script setup lang="ts">
/**
 * Pubblicazione del pannello su Apache o Nginx.
 *
 * L'anteprima non è un dettaglio: chi amministra un server vuole vedere cosa
 * sta per finire in `sites-available` prima che ci finisca, e la
 * configurazione generata contiene le direttive delicate — quelle che fanno
 * funzionare i download — che è giusto poter leggere.
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import { vhostsApi, type VHost, type WebServer } from '@/api/vhosts'

const { t } = useI18n()

const elenco = ref<VHost[]>([])
const installati = ref<WebServer[]>([])
const carico = ref(true)
const errore = ref('')
const avviso = ref('')

const form = ref({ hostname: '', webserver: 'apache' as WebServer, prefisso: '/' })
const anteprima = ref<string | null>(null)
const inCorso = ref(false)
const daEliminare = ref<VHost | null>(null)

const puoProcedere = computed(() => form.value.hostname.trim() !== '' && !inCorso.value)

function racconta(e: unknown): void {
  errore.value = e instanceof Error ? e.message : t('errori.generico')
}

async function carica(): Promise<void> {
  carico.value = true
  errore.value = ''
  try {
    elenco.value = await vhostsApi.elenca()
  } catch (e) {
    racconta(e)
  }

  try {
    installati.value = (await vhostsApi.disponibili()).installati
    if (installati.value.length > 0 && !installati.value.includes(form.value.webserver)) {
      form.value.webserver = installati.value[0]!
    }
  } catch (e) {
    // L'agent gira solo su Linux: in sviluppo non risponde, e non è un errore
    // da mostrare in rosso — l'elenco dei vhost si vede lo stesso.
    if (!(e instanceof ApiError && e.status === 503)) racconta(e)
    avviso.value = t('webserver.agentAssente')
  } finally {
    carico.value = false
  }
}

onMounted(carica)

async function vediAnteprima(): Promise<void> {
  inCorso.value = true
  errore.value = ''
  try {
    anteprima.value = (await vhostsApi.anteprima(form.value)).configurazione
  } catch (e) {
    anteprima.value = null
    racconta(e)
  } finally {
    inCorso.value = false
  }
}

async function pubblica(): Promise<void> {
  inCorso.value = true
  errore.value = ''
  try {
    await vhostsApi.crea(form.value)
    form.value.hostname = ''
    anteprima.value = null
    await carica()
  } catch (e) {
    racconta(e)
  } finally {
    inCorso.value = false
  }
}

async function elimina(): Promise<void> {
  if (daEliminare.value === null) return
  inCorso.value = true
  try {
    await vhostsApi.elimina(daEliminare.value.id)
    daEliminare.value = null
    await carica()
  } catch (e) {
    racconta(e)
  } finally {
    inCorso.value = false
  }
}

async function mostraScritta(vhost: VHost): Promise<void> {
  try {
    anteprima.value = (await vhostsApi.configurazione(vhost.id)).configurazione
  } catch (e) {
    racconta(e)
  }
}
</script>

<template>
  <section class="pagina">
    <header class="testa">
      <div>
        <h1>{{ t('webserver.titolo') }}</h1>
        <p class="spiega">
          {{ t('webserver.descrizione') }}
        </p>
      </div>
    </header>

    <p
      v-if="errore"
      class="avviso avviso--errore"
      role="alert"
    >
      {{ errore }}
    </p>

    <p
      v-else-if="avviso"
      class="avviso"
    >
      {{ avviso }}
    </p>

    <p
      v-if="carico"
      class="avviso"
    >
      {{ t('comune.carico') }}
    </p>

    <ul
      v-else-if="elenco.length"
      class="elenco"
    >
      <li
        v-for="v in elenco"
        :key="v.id"
        class="scheda"
      >
        <div class="riga">
          <span class="host">{{ v.hostname }}</span>
          <span class="etichetta">{{ v.webserver }}</span>
          <span class="prefisso">{{ v.path_prefix }}</span>
        </div>
        <p
          v-if="v.last_error"
          class="avviso avviso--errore"
        >
          {{ v.last_error }}
        </p>
        <div class="azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="mostraScritta(v)"
          >
            {{ t('webserver.vediConfigurazione') }}
          </button>
          <button
            type="button"
            class="bottone bottone--pericolo"
            @click="daEliminare = v"
          >
            {{ t('comune.elimina') }}
          </button>
        </div>
      </li>
    </ul>

    <p
      v-else
      class="avviso"
    >
      {{ t('webserver.nessuno') }}
    </p>

    <section class="blocco">
      <h2>{{ t('webserver.pubblica') }}</h2>
      <p class="spiega">
        {{ t('webserver.nonGestiamo') }}
      </p>

      <div class="riga-form">
        <input
          v-model="form.hostname"
          type="text"
          :placeholder="t('webserver.hostname')"
        >
        <select v-model="form.webserver">
          <option
            v-for="w in installati.length ? installati : (['apache', 'nginx'] as WebServer[])"
            :key="w"
            :value="w"
          >
            {{ w }}
          </option>
        </select>
        <input
          v-model="form.prefisso"
          type="text"
          :placeholder="t('webserver.prefisso')"
        >
        <button
          type="button"
          class="bottone bottone--tenue"
          :disabled="!puoProcedere"
          @click="vediAnteprima"
        >
          {{ t('webserver.anteprima') }}
        </button>
        <button
          class="bottone bottone--principale"
          type="button"
          :disabled="!puoProcedere"
          @click="pubblica"
        >
          {{ t('webserver.applica') }}
        </button>
      </div>

      <pre
        v-if="anteprima"
        class="configurazione"
      >{{ anteprima }}</pre>
    </section>

    <div
      v-if="daEliminare"
      class="velo"
      @click.self="daEliminare = null"
    >
      <section
        class="pannello"
        role="dialog"
      >
        <h2>{{ t('webserver.confermaTitolo') }}</h2>
        <p>{{ t('webserver.confermaTesto', { host: daEliminare.hostname }) }}</p>
        <div class="azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="daEliminare = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="button"
            class="bottone bottone--pericolo"
            :disabled="inCorso"
            @click="elimina"
          >
            {{ t('comune.elimina') }}
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>

.testa h1 {
  margin: 0;
  font-size: 1.5rem;
}

.spiega {
  margin: 0.25rem 0 0;
  color: var(--testo-tenue);
  font-size: 0.9rem;
}

.elenco {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.scheda,
.blocco {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--superficie);
}

.blocco h2 {
  margin: 0;
  font-size: 1rem;
}

.riga {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
}

.host {
  font-weight: 500;
}

.etichetta {
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: var(--superficie-alt);
  color: var(--testo-tenue);
  font-size: 0.75rem;
}

.prefisso {
  color: var(--testo-tenue);
  font-family: ui-monospace, monospace;
  font-size: 0.8rem;
}

.riga-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.riga-form input,
.riga-form select {
  flex: 1 1 8rem;
  min-width: 0;
  padding: 0.5rem 0.65rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--sfondo);
  color: var(--testo);
  font: inherit;
  font-size: 0.875rem;
}

.configurazione {
  max-height: 24rem;
  margin: 0;
  padding: 0.75rem;
  overflow: auto;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--superficie-alt);
  font-size: 0.78rem;
  line-height: 1.45;
}

.azioni {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}





.avviso {
  margin: 0;
  color: var(--testo-tenue);
  font-size: 0.9rem;
}

.avviso--errore {
  color: var(--errore);
}

.velo {
  position: fixed;
  display: grid;
  padding: 1rem;
  background: rgb(0 0 0 / 45%);
  inset: 0;
  place-items: center;
}

.pannello {
  display: flex;
  flex-direction: column;
  width: min(28rem, 100%);
  gap: 0.75rem;
  padding: 1.25rem;
  border-radius: var(--raggio);
  background: var(--superficie);
}

.pannello h2 {
  margin: 0;
  font-size: 1.05rem;
}

.pannello p {
  margin: 0;
  color: var(--testo-tenue);
}
</style>
