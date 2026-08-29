<script setup lang="ts">
/**
 * Piede di pagina con versione e attribuzione.
 *
 * Presente in ogni vista, comprese quelle a schermo intero senza la barra
 * laterale: per questo è un componente e non parte del solo guscio.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useAppStore } from '@/stores/app'

const app = useAppStore()
const { t } = useI18n()

/** Versione e attribuzione su un'unica riga, come da standard di progetto. */
const riga = computed(() =>
  app.version && app.author
    ? `v${app.version} — ${t('piede.attribuzione', { autore: app.author })}`
    : '',
)
</script>

<template>
  <footer class="piede">
    <span v-if="riga">{{ riga }}</span>
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
