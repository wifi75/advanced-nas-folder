<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterView, useRoute, useRouter } from 'vue-router'

import AppFooter from '@/components/AppFooter.vue'
import BarraLaterale from '@/components/BarraLaterale.vue'
import { aggiornaTitolo } from '@/router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const { locale } = useI18n()
const router = useRouter()
const rotta = useRoute()

const barraAperta = ref(false)

// Su schermo stretto la barra copre la pagina: cambiando vista va richiusa,
// altrimenti resta davanti a ciò che si è appena aperto.
watch(() => rotta.fullPath, () => (barraAperta.value = false))

// Il titolo della scheda va rifatto anche quando cambia la lingua: la rotta
// resta la stessa, quindi la guardia di navigazione non scatterebbe.
watch(locale, () => aggiornaTitolo(rotta.meta.titolo))

async function esci(): Promise<void> {
  auth.esci()
  barraAperta.value = false
  await router.push({ name: 'login' })
}
</script>

<template>
  <div
    v-if="auth.autenticato"
    class="guscio"
  >
    <BarraLaterale
      :aperta="barraAperta"
      @naviga="barraAperta = false"
      @esci="esci"
    />

    <div
      v-if="barraAperta"
      class="velo"
      @click="barraAperta = false"
    />

    <div class="colonna">
      <button
        type="button"
        class="apri-menu"
        :aria-expanded="barraAperta"
        aria-label="Apri il menu"
        @click="barraAperta = !barraAperta"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
        >
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </button>

      <main class="contenuto">
        <RouterView />
      </main>
      <AppFooter />
    </div>
  </div>

  <template v-else>
    <main class="contenuto">
      <RouterView />
    </main>
    <AppFooter />
  </template>
</template>

<style scoped>
/* #app è già una colonna flessibile alta almeno quanto la finestra: qui basta
   occupare lo spazio residuo. Ripetere 100vh sommerebbe l'altezza del piede e
   farebbe scorrere la pagina di quel tanto. */
.guscio {
  flex: 1;
  display: flex;
  min-block-size: 0;
}

.colonna {
  flex: 1;
  min-inline-size: 0;
  display: flex;
  flex-direction: column;
}

.contenuto {
  flex: 1;
  display: flex;
  flex-direction: column;
}


.apri-menu {
  display: none;
  align-items: center;
  justify-content: center;
  inline-size: 40px;
  block-size: 40px;
  margin: 0.75rem 0 0 0.75rem;
  color: var(--testo);
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: 10px;
  cursor: pointer;
}

.apri-menu svg {
  inline-size: 20px;
  block-size: 20px;
}

.velo {
  position: fixed;
  inset: 0;
  z-index: 15;
  background: rgb(0 0 0 / 40%);
}

@media (max-width: 860px) {
  .apri-menu {
    display: inline-flex;
  }

  .velo {
    display: block;
  }
}

@media (min-width: 861px) {
  .velo {
    display: none;
  }
}
</style>
