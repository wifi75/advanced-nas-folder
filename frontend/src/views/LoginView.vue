<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import SelettoreLingua from '@/components/SelettoreLingua.vue'
import SelettoreTema from '@/components/SelettoreTema.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const { t } = useI18n()

const username = ref('')
const password = ref('')

async function accedi(): Promise<void> {
  if (await auth.accedi(username.value, password.value)) {
    await router.push('/')
  }
}
</script>

<template>
  <div class="pagina-accesso">
    <form
      class="riquadro"
      @submit.prevent="accedi"
    >
      <h1>{{ t('accesso.titolo') }}</h1>

      <label class="campo">
        <span>{{ t('accesso.utente') }}</span>
        <input
          v-model="username"
          type="text"
          autocomplete="username"
          required
        >
      </label>

      <label class="campo">
        <span>{{ t('accesso.password') }}</span>
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
        class="bottone bottone--principale"
        type="submit"
        :disabled="auth.inCorso"
      >
        {{ auth.inCorso ? t('accesso.inCorso') : t('accesso.titolo') }}
      </button>

      <!-- Lingua e tema si scelgono anche prima di entrare: chi arriva qui
           deve poter leggere la pagina nella propria lingua. -->
      <div class="preferenze">
        <SelettoreTema compatto />
        <SelettoreLingua compatto />
      </div>
    </form>
  </div>
</template>

<style scoped>
/* Non usa `.pagina` globale: quella impagina un elenco in colonna, larghezza
   fissa e allineata in alto. Qui c'e' un solo riquadro, e va centrato nello
   schermo. Usarle entrambe lo mandava in alto a sinistra. */
.pagina-accesso {
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



.errore {
  margin: 0;
  font-size: 0.875rem;
  color: var(--errore);
}

.preferenze {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding-block-start: 0.4rem;
  border-block-start: 1px solid var(--bordo);
  margin-block-start: 0.15rem;
}
</style>
