<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const app = useAppStore()
const auth = useAuthStore()
const { t } = useI18n()
</script>

<template>
  <div class="pagina">
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

    <section class="avviso">
      <h2>{{ t('menu.condivisioni') }}</h2>
      <p>{{ t('home.condivisioniDescrizione') }}</p>
      <RouterLink
        class="collegamento"
        to="/condivisioni"
      >
        {{ t('home.vaiCondivisioni') }}
      </RouterLink>
    </section>

    <section class="avviso">
      <h2>{{ t('home.inArrivoTitolo') }}</h2>
      <p>{{ t('home.inArrivoDescrizione') }}</p>
    </section>
  </div>
</template>

<style scoped>
.pagina {
  flex: 1;
  width: min(760px, 100% - 2.5rem);
  margin-inline: auto;
  padding-block: 3rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

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
</style>
