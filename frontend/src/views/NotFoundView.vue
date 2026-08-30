<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

const { t } = useI18n()
</script>

<template>
  <div class="pagina">
    <h1>{{ t('nonTrovata.titolo') }}</h1>
    <p>{{ t('nonTrovata.testo') }}</p>
    <RouterLink to="/">
      {{ t('nonTrovata.torna') }}
    </RouterLink>
  </div>
</template>

<style scoped>

h1 {
  margin: 0;
  font-size: 1.5rem;
}

p {
  margin: 0;
  color: var(--testo-tenue);
}
</style>
