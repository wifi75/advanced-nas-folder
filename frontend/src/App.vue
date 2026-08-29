<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'

import AppFooter from '@/components/AppFooter.vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const app = useAppStore()
const auth = useAuthStore()
const router = useRouter()

async function esci(): Promise<void> {
  auth.esci()
  await router.push({ name: 'login' })
}
</script>

<template>
  <header
    v-if="auth.autenticato"
    class="barra"
  >
    <nav class="navigazione">
      <RouterLink
        to="/"
        class="marchio"
      >
        {{ app.name }}
      </RouterLink>
      <RouterLink to="/condivisioni">
        Condivisioni
      </RouterLink>
    </nav>
    <div class="utente">
      <span v-if="auth.utente">{{ auth.utente.username }}</span>
      <button
        type="button"
        @click="esci"
      >
        Esci
      </button>
    </div>
  </header>

  <main class="contenuto">
    <RouterView />
  </main>
  <AppFooter />
</template>

<style scoped>
.barra {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  background: var(--superficie);
  border-block-end: 1px solid var(--bordo);
}

.navigazione {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  font-size: 0.9375rem;
}

.navigazione a {
  color: var(--testo-tenue);
  text-decoration: none;
}

.navigazione a:hover,
.navigazione a.router-link-active {
  color: var(--testo);
}

.marchio {
  font-weight: 600;
  color: var(--testo) !important;
}

.utente {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
  color: var(--testo-tenue);
}

.utente button {
  padding: 0.35rem 0.75rem;
  font: inherit;
  font-size: 0.8125rem;
  color: var(--testo);
  background: transparent;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  cursor: pointer;
}

.contenuto {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
