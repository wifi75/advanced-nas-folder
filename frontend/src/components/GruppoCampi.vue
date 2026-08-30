<script setup lang="ts">
/**
 * Un gruppo di campi con un titolo e una spiegazione.
 *
 * I moduli erano elenchi piatti di campi: chi non conosce gia' il pannello non
 * aveva modo di capire quali decisioni stesse prendendo, ne' quante ne
 * restassero. Raggruppare risponde alla domanda «questa parte a cosa serve?»
 * una volta per gruppo, invece di lasciarla aperta campo per campo.
 *
 * E' un `fieldset` e non un `div`: il titolo diventa cosi' il nome del gruppo
 * anche per chi naviga con la tastiera o con un lettore di schermo.
 */
defineProps<{ titolo: string; descrizione?: string }>()
</script>

<template>
  <fieldset class="gruppo">
    <legend class="gruppo__titolo">
      {{ titolo }}
    </legend>
    <p
      v-if="descrizione"
      class="gruppo__descrizione"
    >
      {{ descrizione }}
    </p>
    <div class="gruppo__campi">
      <slot />
    </div>
  </fieldset>
</template>

<style scoped>
.gruppo {
  margin: 0;
  padding: 0.9rem 1rem 1rem;
  border: 0;
}

.gruppo__titolo {
  padding: 0 0.35rem;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--testo-tenue);
}

.gruppo__descrizione {
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
  color: var(--testo-tenue);
  max-width: 60ch;
}

.gruppo__campi {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>
