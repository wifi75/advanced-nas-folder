<script setup lang="ts">
/**
 * Piede di pagina con versione e attribuzione.
 *
 * Presente in ogni vista, comprese quelle a schermo intero senza la shell:
 * per questo e un componente e non parte del solo layout autenticato.
 */
import { useAppStore } from '@/stores/app'

const app = useAppStore()
</script>

<template>
  <footer class="piede">
    <span v-if="app.footer">{{ app.footer }}</span>
  </footer>
</template>

<style scoped>
.piede {
  padding: 1rem 1.25rem;
  text-align: center;
  font-size: 0.8125rem;
  color: var(--testo-tenue);
  border-top: 1px solid var(--bordo);
}
</style>
