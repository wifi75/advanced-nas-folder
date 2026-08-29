<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const app = useAppStore()
</script>

<template>
  <div class="pagina">
    <header class="testata">
      <h1>{{ app.name }}</h1>
      <p class="sottotitolo">
        Monta condivisioni NFS, pubblica cartelle con permessi per sottocartella,
        gestisci i file.
      </p>
    </header>

    <section
      class="stato"
      aria-live="polite"
    >
      <span
        class="pallino"
        :class="app.online ? 'pallino--ok' : 'pallino--ko'"
        aria-hidden="true"
      />
      <span v-if="app.online">Servizio attivo</span>
      <span v-else>Servizio non raggiungibile</span>
    </section>

    <section class="avviso">
      <h2>Fase 0 — fondamenta</h2>
      <p>
        Il pannello è in costruzione. La gestione dei mount arriva nella fase 1,
        la pubblicazione e i permessi nella fase 2.
      </p>
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
  gap: 1.75rem;
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
  margin: 0;
  color: var(--testo-tenue);
  font-size: 0.9375rem;
}
</style>
