<script setup lang="ts">
/**
 * Utenti del pannello.
 *
 * I permessi qui sono generali — cosa può fare una persona ovunque. *Dove*
 * può farlo si decide nella pubblicazione, con i permessi per cartella: le
 * due cose sono separate di proposito, perché rispondono a domande diverse e
 * mescolarle renderebbe illeggibili entrambe.
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { utentiApi, type NuovoUtente, type Utente } from '@/api/utenti'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()

const elenco = ref<Utente[]>([])
const carico = ref(true)
const errore = ref('')
const inCorso = ref(false)

const nuovoAperto = ref(false)
const daEliminare = ref<Utente | null>(null)

/** I permessi generali, nell'ordine in cui hanno senso letti di seguito. */
const PERMESSI = [
  'can_download',
  'can_upload',
  'can_create',
  'can_rename',
  'can_modify',
  'can_delete',
  'can_share',
] as const

function vuoto(): NuovoUtente {
  return {
    username: '',
    password: '',
    email: null,
    is_admin: false,
    scope: '',
    can_create: false,
    can_delete: false,
    can_modify: false,
    can_rename: false,
    can_share: false,
    can_download: true,
    can_upload: false,
  }
}

const form = ref<NuovoUtente>(vuoto())

const puoCreare = computed(
  () => form.value.username.trim() !== '' && form.value.password.length >= 10 && !inCorso.value,
)

function racconta(e: unknown): void {
  errore.value = e instanceof Error ? e.message : t('errori.generico')
}

async function carica(): Promise<void> {
  carico.value = true
  errore.value = ''
  try {
    elenco.value = await utentiApi.elenca()
  } catch (e) {
    racconta(e)
  } finally {
    carico.value = false
  }
}

onMounted(carica)

async function crea(): Promise<void> {
  inCorso.value = true
  errore.value = ''
  try {
    await utentiApi.crea({ ...form.value, email: form.value.email || null })
    form.value = vuoto()
    nuovoAperto.value = false
    await carica()
  } catch (e) {
    racconta(e)
  } finally {
    inCorso.value = false
  }
}

async function alterna(utente: Utente, campo: keyof Utente): Promise<void> {
  errore.value = ''
  try {
    await utentiApi.modifica(utente.id, { [campo]: !utente[campo] })
    await carica()
  } catch (e) {
    // Il server rifiuta le modifiche che renderebbero il pannello
    // ingestibile, e spiega perché: quel messaggio va mostrato tale e quale.
    racconta(e)
  }
}

async function elimina(): Promise<void> {
  if (daEliminare.value === null) return
  inCorso.value = true
  try {
    await utentiApi.elimina(daEliminare.value.id)
    daEliminare.value = null
    await carica()
  } catch (e) {
    racconta(e)
  } finally {
    inCorso.value = false
  }
}

function sonoIo(utente: Utente): boolean {
  return auth.utente?.id === utente.id
}
</script>

<template>
  <section class="pagina">
    <header class="testa">
      <div>
        <h1>{{ t('utenti.titolo') }}</h1>
        <p class="spiega">
          {{ t('utenti.descrizione') }}
        </p>
      </div>
      <button
        type="button"
        @click="nuovoAperto = true"
      >
        {{ t('utenti.nuovo') }}
      </button>
    </header>

    <p
      v-if="errore"
      class="avviso avviso--errore"
      role="alert"
    >
      {{ errore }}
    </p>

    <p
      v-if="carico"
      class="avviso"
    >
      {{ t('comune.carico') }}
    </p>

    <ul
      v-else
      class="elenco"
    >
      <li
        v-for="u in elenco"
        :key="u.id"
        class="scheda"
      >
        <div class="riga">
          <span class="nome">{{ u.username }}</span>
          <span
            v-if="u.is_admin"
            class="etichetta etichetta--admin"
          >{{ t('comune.amministratore') }}</span>
          <span
            v-if="!u.is_active"
            class="etichetta"
          >{{ t('utenti.disattivato') }}</span>
          <span
            v-if="u.scope"
            class="ambito"
            :title="t('utenti.ambito')"
          >{{ u.scope }}</span>
          <span
            v-if="sonoIo(u)"
            class="etichetta"
          >{{ t('utenti.sonoIo') }}</span>
        </div>

        <div class="permessi">
          <button
            v-for="p in PERMESSI"
            :key="p"
            type="button"
            class="permesso"
            :class="{ 'permesso--attivo': u[p] }"
            :aria-pressed="u[p]"
            @click="alterna(u, p)"
          >
            {{ t(`utenti.${p}`) }}
          </button>
        </div>

        <div class="azioni">
          <button
            type="button"
            class="secondario"
            @click="alterna(u, 'is_admin')"
          >
            {{ u.is_admin ? t('utenti.togliAdmin') : t('utenti.rendiAdmin') }}
          </button>
          <button
            type="button"
            class="secondario"
            @click="alterna(u, 'is_active')"
          >
            {{ u.is_active ? t('utenti.disattiva') : t('utenti.attiva') }}
          </button>
          <button
            type="button"
            class="pericolo"
            @click="daEliminare = u"
          >
            {{ t('comune.elimina') }}
          </button>
        </div>
      </li>
    </ul>

    <!-- nuovo utente -->
    <div
      v-if="nuovoAperto"
      class="velo"
      @click.self="nuovoAperto = false"
    >
      <form
        class="pannello"
        @submit.prevent="crea"
      >
        <h2>{{ t('utenti.nuovo') }}</h2>

        <label class="campo">
          {{ t('accesso.utente') }}
          <input
            v-model="form.username"
            type="text"
            autocomplete="off"
          >
        </label>

        <label class="campo">
          {{ t('accesso.password') }}
          <input
            v-model="form.password"
            type="password"
            autocomplete="new-password"
          >
          <span class="nota">{{ t('utenti.passwordMinima') }}</span>
        </label>

        <label class="campo">
          {{ t('utenti.ambito') }}
          <input
            v-model="form.scope"
            type="text"
            :placeholder="t('utenti.ambitoVuoto')"
          >
          <span class="nota">{{ t('utenti.ambitoNota') }}</span>
        </label>

        <label class="interruttore">
          <input
            v-model="form.is_admin"
            type="checkbox"
          >
          {{ t('utenti.amministratore') }}
        </label>

        <fieldset class="gruppo">
          <legend>{{ t('utenti.permessi') }}</legend>
          <label
            v-for="p in PERMESSI"
            :key="p"
            class="interruttore"
          >
            <input
              v-model="form[p]"
              type="checkbox"
            >
            {{ t(`utenti.${p}`) }}
          </label>
        </fieldset>

        <div class="pannello__azioni">
          <button
            type="button"
            class="secondario"
            @click="nuovoAperto = false"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="submit"
            :disabled="!puoCreare"
          >
            {{ t('comune.crea') }}
          </button>
        </div>
      </form>
    </div>

    <!-- conferma eliminazione -->
    <div
      v-if="daEliminare"
      class="velo"
      @click.self="daEliminare = null"
    >
      <section
        class="pannello"
        role="dialog"
      >
        <h2>{{ t('utenti.confermaTitolo', { nome: daEliminare.username }) }}</h2>
        <p class="nota">
          {{ t('utenti.confermaTesto') }}
        </p>
        <div class="pannello__azioni">
          <button
            type="button"
            class="secondario"
            @click="daEliminare = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="button"
            class="pericolo"
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
.pagina {
  display: flex;
  flex: 1;
  flex-direction: column;
  width: min(880px, 100% - 2.5rem);
  margin-inline: auto;
  gap: 1.25rem;
  padding-block: 1.5rem;
}

.testa {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.testa h1 {
  margin: 0;
  font-size: 1.5rem;
}

.spiega,
.nota {
  margin: 0.25rem 0 0;
  color: var(--testo-tenue);
  font-size: 0.85rem;
}

.elenco {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.scheda {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--superficie);
}

.riga {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.nome {
  font-weight: 500;
}

.etichetta {
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: var(--superficie-alt);
  color: var(--testo-tenue);
  font-size: 0.75rem;
}

.etichetta--admin {
  background: color-mix(in srgb, var(--accento) 22%, transparent);
  color: var(--accento);
}

.ambito {
  color: var(--testo-tenue);
  font-family: ui-monospace, monospace;
  font-size: 0.78rem;
}

.permessi {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

/* I permessi sono pastiglie premibili: si vede a colpo d'occhio quali sono
   accesi, e si cambiano senza aprire una finestra. */
.permesso {
  padding: 0.15rem 0.55rem;
  border: 1px solid var(--bordo);
  border-radius: 999px;
  background: transparent;
  color: var(--testo-tenue);
  cursor: pointer;
  font: inherit;
  font-size: 0.78rem;
}

.permesso--attivo {
  border-color: transparent;
  background: color-mix(in srgb, var(--ok) 20%, transparent);
  color: var(--ok);
}

.azioni,
.pannello__azioni {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.pannello__azioni {
  justify-content: flex-end;
}

button {
  padding: 0.45rem 0.85rem;
  border: none;
  border-radius: var(--raggio);
  background: var(--accento);
  color: var(--accento-testo);
  cursor: pointer;
  font: inherit;
  font-size: 0.875rem;
  font-weight: 500;
}

button:disabled {
  cursor: default;
  opacity: 0.55;
}

button.secondario {
  border: 1px solid var(--bordo);
  background: transparent;
  color: var(--testo);
}

button.pericolo {
  border: 1px solid var(--errore);
  background: transparent;
  color: var(--errore);
}

.velo {
  position: fixed;
  display: grid;
  padding: 1rem;
  overflow: auto;
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

.campo {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.875rem;
}

.campo input {
  padding: 0.55rem 0.7rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--sfondo);
  color: var(--testo);
  font: inherit;
}

.interruttore {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.875rem;
}

.gruppo {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  margin: 0;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

.gruppo legend {
  padding-inline: 0.35rem;
  color: var(--testo-tenue);
  font-size: 0.8rem;
}

.avviso {
  margin: 0;
  color: var(--testo-tenue);
}

.avviso--errore {
  color: var(--errore);
}
</style>
