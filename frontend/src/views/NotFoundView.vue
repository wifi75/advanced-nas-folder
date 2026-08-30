<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

const { t } = useI18n()
</script>

<template>
  <div class="pagina-centrata">
    <h1>{{ t('nonTrovata.titolo') }}</h1>
    <p>{{ t('nonTrovata.testo') }}</p>
    <RouterLink to="/">
      {{ t('nonTrovata.torna') }}
    </RouterLink>
  </div>
</template>

<style scoped>
/* Un messaggio solo, centrato: `.pagina` globale lo allineerebbe in alto a
   sinistra come se fosse un elenco. */
.pagina-centrata {
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
