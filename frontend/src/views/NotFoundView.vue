<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="pagina">
    <h1>Pagina non trovata</h1>
    <p>L'indirizzo richiesto non esiste in questo pannello.</p>
    <RouterLink to="/">
      Torna al pannello
    </RouterLink>
  </div>
</template>

<style scoped>
.pagina {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  padding: 3rem 1.25rem;
  text-align: center;
}

h1 {
  margin: 0;
  font-size: 1.5rem;
}

p {
  margin: 0;
  color: var(--testo-tenue);
}
</style>
