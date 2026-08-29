<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')

async function accedi(): Promise<void> {
  if (await auth.accedi(username.value, password.value)) {
    await router.push('/')
  }
}
</script>

<template>
  <div class="pagina">
    <form
      class="riquadro"
      @submit.prevent="accedi"
    >
      <h1>Accedi</h1>

      <label class="campo">
        <span>Nome utente</span>
        <input
          v-model="username"
          type="text"
          autocomplete="username"
          required
          autofocus
        >
      </label>

      <label class="campo">
        <span>Password</span>
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
        >
      </label>

      <p
        v-if="auth.errore"
        class="errore"
        role="alert"
      >
        {{ auth.errore }}
      </p>

      <button
        type="submit"
        :disabled="auth.inCorso"
      >
        {{ auth.inCorso ? 'Accesso in corso…' : 'Accedi' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.pagina {
  flex: 1;
  display: grid;
  place-items: center;
  padding: 2rem 1.25rem;
}

.riquadro {
  width: min(380px, 100%);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.75rem;
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  box-shadow: var(--ombra);
}

h1 {
  margin: 0;
  font-size: 1.35rem;
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.875rem;
}

.campo input {
  padding: 0.6rem 0.7rem;
  font: inherit;
  color: var(--testo);
  background: var(--sfondo);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

button {
  padding: 0.65rem 1rem;
  font: inherit;
  font-weight: 500;
  color: var(--accento-testo);
  background: var(--accento);
  border: none;
  border-radius: var(--raggio);
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: default;
}

.errore {
  margin: 0;
  font-size: 0.875rem;
  color: var(--errore);
}
</style>
