<script setup lang="ts">
/**
 * La schermata che chiede le credenziali per entrare in una cartella protetta.
 *
 * È deliberatamente diversa dall'accesso al pannello: chi arriva qui ha
 * ricevuto un indirizzo, non è un amministratore, e spesso non sa nemmeno che
 * esista un pannello dietro. Vedersi davanti la stessa pagina con cui entra
 * chi amministra il server confonde, e fa sembrare di essere finiti nel posto
 * sbagliato.
 *
 * Cambiano il colore, il tono e ciò che si chiede: qui si parla della
 * *cartella*, non del sistema.
 */
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  /** Il nome della cartella, per dire dove si sta entrando. */
  cartella: string
  /** `password`: basta la parola d'ordine. `utenti`: serve un account. */
  modo: 'password' | 'utenti'
}>()

const emit = defineEmits<{ password: [valore: string]; entrato: [] }>()

const { t } = useI18n()
const auth = useAuthStore()

const utente = ref('')
const password = ref('')
const inCorso = ref(false)
const errore = ref('')

const puoProcedere = computed(() => password.value !== '')

async function invia(): Promise<void> {
  errore.value = ''

  // Senza nome utente si prova la parola d'ordine della cartella: chi ha
  // ricevuto un indirizzo un account non ce l'ha, e obbligarlo a inventarne
  // uno chiuderebbe la porta proprio a chi doveva entrare.
  if (utente.value === '') {
    if (props.modo === 'password') {
      emit('password', password.value)
    } else {
      errore.value = t('accessoCartella.serveNomeUtente')
    }
    return
  }

  inCorso.value = true
  const riuscito = await auth.accedi(utente.value, password.value)
  inCorso.value = false

  if (riuscito) emit('entrato')
  else errore.value = t('accessoCartella.credenzialiErrate')
}
</script>

<template>
  <div class="accesso">
    <form
      class="riquadro"
      @submit.prevent="invia"
    >
      <span
        class="lucchetto"
        aria-hidden="true"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M6 10h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1Z" />
          <path d="M8 10V7a4 4 0 0 1 8 0v3" />
        </svg>
      </span>

      <h1>{{ t('accessoCartella.titolo') }}</h1>
      <p class="cartella">
        {{ cartella }}
      </p>
      <p class="spiega">
        {{ modo === 'password' ? t('accessoCartella.servePassword') : t('accessoCartella.serveAccount') }}
      </p>

      <label class="campo">
        <span>{{ modo === 'password' ? t('accessoCartella.utenteFacoltativo') : t('accesso.utente') }}</span>
        <input
          v-model="utente"
          type="text"
          autocomplete="username"
          autocapitalize="none"
          spellcheck="false"
        >
      </label>

      <label class="campo">
        <span>{{ t('accesso.password') }}</span>
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
        >
      </label>

      <p
        v-if="errore"
        class="errore"
        role="alert"
      >
        {{ errore }}
      </p>

      <button
        type="submit"
        class="bottone bottone--principale entra"
        :disabled="!puoProcedere || inCorso"
      >
        {{ inCorso ? t('accesso.inCorso') : t('accessoCartella.entra') }}
      </button>
    </form>
  </div>
</template>

<style scoped>
/* Una tinta propria, diversa dall'azzurro del pannello: chi arriva qui non sta
   amministrando niente, sta aprendo una cartella che qualcuno gli ha
   mandato. */
.accesso {
  --tinta-accesso: #8a5a2b;
  flex: 1;
  display: grid;
  place-items: center;
  padding: 2rem 1.25rem;
}

/* Il selettore giusto e' "data-tema" (italiano), non "data-theme": con
   quello sbagliato la variante scura non scattava mai, ne' dalla preferenza
   di sistema ne' dalla scelta esplicita — trovato verificando davvero nel
   browser durante la revisione grafica del pannello. */
@media (prefers-color-scheme: dark) {
  :root:not([data-tema='chiaro']) .accesso {
    --tinta-accesso: #d9a066;
  }
}

:root[data-tema='scuro'] .accesso {
  --tinta-accesso: #d9a066;
}

/* Vetro ambrato, non piu' una card piena: stessa identita' a vetro del resto
   della pagina pubblica (--vetro-*-pub, definiti su ".archivio" in
   ArchivioView.vue — sempre l'antenato di questo componente nel DOM), tinta
   di ambra invece che neutra, per restare la tinta propria di questa
   schermata. */
.riquadro {
  width: min(24rem, 100%);
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  padding: 1.6rem 1.4rem;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--tinta-accesso) 35%, var(--vetro-bordo-pub));
  background:
    linear-gradient(
      158deg,
      color-mix(in srgb, var(--tinta-accesso) 16%, var(--vetro-sfondo-pub)),
      var(--vetro-sfondo-pub)
    );
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  box-shadow: inset 0 1px 0 var(--vetro-luce-pub), var(--vetro-ombra);
  text-align: center;
}

.lucchetto {
  inline-size: 44px;
  block-size: 44px;
  margin-inline: auto;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: #fff;
  background:
    linear-gradient(
      165deg,
      color-mix(in srgb, var(--tinta-accesso) 100%, white 16%),
      color-mix(in srgb, var(--tinta-accesso) 80%, black 20%)
    );
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 40%);
}

.lucchetto svg {
  width: 24px;
  height: 24px;
}

h1 {
  margin: 0;
  font-size: 1.25rem;
  letter-spacing: -0.015em;
}

.cartella {
  margin: 0;
  font-weight: 600;
  color: var(--tinta-accesso);
  overflow-wrap: anywhere;
}

.spiega {
  margin: 0 0 0.3rem;
  font-size: 0.875rem;
  color: var(--testo-tenue);
}

.campo {
  text-align: left;
}

.entra {
  margin-top: 0.3rem;
  justify-content: center;
  background:
    linear-gradient(
      165deg,
      color-mix(in srgb, var(--tinta-accesso) 100%, white 14%),
      color-mix(in srgb, var(--tinta-accesso) 82%, black 18%)
    );
  border-color: transparent;
}

.errore {
  margin: 0;
  color: var(--errore);
  font-size: 0.875rem;
}
</style>
