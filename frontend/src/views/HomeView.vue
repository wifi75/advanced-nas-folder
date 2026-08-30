<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useMountsStore } from '@/stores/mounts'
import { useSharesStore } from '@/stores/shares'

const app = useAppStore()
const auth = useAuthStore()
const mounts = useMountsStore()
const shares = useSharesStore()
const { t } = useI18n()

/** La prima pubblicazione, come esempio da aprire nel terzo passo. */
const primaPubblicazione = computed(() => shares.elenco[0])

// I conteggi servono a rispondere alla domanda vera di chi arriva qui — «a che
// punto sono?» — invece di descrivere il prodotto a chi lo sta gia usando.
onMounted(() => {
  if (auth.utente?.is_admin) {
    void mounts.carica()
    void shares.carica()
  }
})
</script>

<template>
  <div class="pagina pagina--stretta">
    <header class="testata">
      <h1>{{ app.name }}</h1>
      <p class="sottotitolo">
        {{ t('home.sottotitolo') }}
      </p>
    </header>

    <p
      v-if="auth.passwordPredefinita"
      class="allarme"
      role="alert"
    >
      <strong>{{ t('home.passwordIniziale') }}</strong>
      {{ t('home.passwordInizialeDettaglio') }}
    </p>

    <section
      class="stato"
      aria-live="polite"
    >
      <span
        class="pallino"
        :class="app.online ? 'pallino--ok' : 'pallino--ko'"
        aria-hidden="true"
      />
      <span>{{ app.online ? t('home.servizioAttivo') : t('home.servizioNonRaggiungibile') }}</span>
      <span
        v-if="auth.utente"
        class="chi"
      >
        {{ auth.utente.username
        }}<template v-if="auth.utente.is_admin"> · {{ t('comune.amministratore') }}</template>
      </span>
    </section>

    <section
      v-if="auth.utente?.is_admin"
      class="percorso"
    >
      <h2>{{ t('home.comeFunziona') }}</h2>
      <p class="introduzione">
        {{ t('home.comeFunzionaIntro') }}
      </p>

      <ol class="passi">
        <li class="passo">
          <h3>{{ t('home.passo1') }}</h3>
          <p>{{ t('home.passo1Testo') }}</p>
          <p class="conteggio">
            {{ t('home.statoMount', { count: mounts.elenco.length }, mounts.elenco.length) }}
          </p>
          <RouterLink
            class="collegamento"
            to="/condivisioni"
          >
            {{ t('home.passo1Vai') }}
          </RouterLink>
        </li>

        <li class="passo">
          <h3>{{ t('home.passo2') }}</h3>
          <p>{{ t('home.passo2Testo') }}</p>
          <p class="conteggio">
            {{ t('home.statoShare', { count: shares.elenco.length }, shares.elenco.length) }}
          </p>
          <RouterLink
            class="collegamento"
            to="/pubblicazioni"
          >
            {{ t('home.passo2Vai') }}
          </RouterLink>
        </li>

        <li class="passo">
          <h3>{{ t('home.passo3') }}</h3>
          <p>{{ t('home.passo3Testo') }}</p>
          <RouterLink
            v-if="primaPubblicazione"
            class="collegamento"
            :to="`/archivio/${primaPubblicazione.slug}`"
          >
            {{ t('home.passo3Vai') }}
          </RouterLink>
        </li>
      </ol>
    </section>
  </div>
</template>

<style scoped>

.testata h1 {
  margin: 0 0 0.35rem;
  font-size: clamp(1.75rem, 4vw, 2.35rem);
  letter-spacing: -0.02em;
}

.sottotitolo {
  margin: 0;
  color: var(--testo-tenue);
  max-width: 52ch;
}

.allarme {
  margin: 0;
  padding: 0.85rem 1.1rem;
  font-size: 0.9375rem;
  color: var(--testo);
  background: var(--superficie);
  border: 1px solid var(--attenzione);
  border-left-width: 3px;
  border-radius: var(--raggio);
}

.stato {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.85rem 1.1rem;
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  font-size: 0.9375rem;
}

.chi {
  margin-inline-start: auto;
  color: var(--testo-tenue);
  font-size: 0.875rem;
}

.pallino {
  inline-size: 0.55rem;
  block-size: 0.55rem;
  border-radius: 50%;
  flex: none;
}

.pallino--ok {
  background: var(--ok);
}

.pallino--ko {
  background: var(--errore);
}

.avviso {
  padding: 1.1rem 1.25rem;
  background: var(--superficie-alt);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

.avviso h2 {
  margin: 0 0 0.4rem;
  font-size: 1rem;
}

.avviso p {
  margin: 0 0 0.5rem;
  color: var(--testo-tenue);
  font-size: 0.9375rem;
}

.collegamento {
  font-size: 0.9375rem;
}
.percorso h2 {
  margin: 0 0 0.35rem;
  font-size: 1.15rem;
}

.introduzione {
  margin: 0 0 1rem;
  color: var(--testo-tenue);
}

/* La numerazione non e decorativa: i passi sono davvero in sequenza, e senza
   il primo il secondo non e possibile. */
.passi {
  list-style: none;
  counter-reset: passo;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.passo {
  counter-increment: passo;
  position: relative;
  padding-left: 2.6rem;
}

.passo::before {
  content: counter(passo);
  position: absolute;
  left: 0;
  top: 0;
  width: 1.9rem;
  height: 1.9rem;
  display: grid;
  place-items: center;
  border: 1px solid var(--bordo);
  border-radius: 50%;
  font-variant-numeric: tabular-nums;
  color: var(--testo-tenue);
}

.passo h3 {
  margin: 0 0 0.25rem;
  font-size: 1rem;
}

.passo p {
  margin: 0 0 0.35rem;
  color: var(--testo-tenue);
  max-width: 60ch;
  /* Una parola lunga — un percorso, un indirizzo — non deve poter allargare la
     pagina oltre lo schermo: il testo va a capo, e la pagina non scorre di
     lato. */
  overflow-wrap: anywhere;
}

.conteggio {
  font-variant-numeric: tabular-nums;
}
</style>
