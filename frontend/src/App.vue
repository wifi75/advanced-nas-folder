<script setup lang="ts">
import AppFooter from '@/components/AppFooter.vue'
</script>

<template>
  <main class="contenuto">
    <RouterView />
  </main>
  <AppFooter />
</template>

<style scoped>
.contenuto {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
