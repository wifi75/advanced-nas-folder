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
defineProps<{ titolo: string; descrizione?: string; tinta?: string; icona?: string }>()
</script>

<template>
  <fieldset class="gruppo">
    <legend class="gruppo__testa">
      <span
        v-if="icona"
        class="gruppo__pastiglia"
        :style="{ '--tinta': tinta ?? 'var(--accento)' }"
        aria-hidden="true"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path :d="icona" />
        </svg>
      </span>
      <span class="gruppo__titolo">{{ titolo }}</span>
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
  /* Non un riquadro dentro un riquadro: un titolo e sotto una pila di schede,
     come una categoria della barra laterale. */
  margin: 0;
  padding: 0;
  border: 0;
}

.gruppo__testa {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0;
}

.gruppo__pastiglia {
  flex: none;
  inline-size: 22px;
  block-size: 22px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  color: #fff;
  background:
    linear-gradient(
      165deg,
      color-mix(in srgb, var(--tinta) 100%, white 18%),
      color-mix(in srgb, var(--tinta) 78%, black 22%)
    );
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 45%),
    0 2px 5px -1px color-mix(in srgb, var(--tinta) 55%, transparent);
}

.gruppo__pastiglia svg {
  width: 14px;
  height: 14px;
}

.gruppo__titolo {
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--testo-tenue);
}

.gruppo__descrizione {
  margin: 0.3rem 0 0.7rem;
  padding-left: 0.15rem;
  font-size: 0.85rem;
  color: var(--testo-tenue);
  max-width: 60ch;
}

.gruppo__campi {
  /* In griglia, non impilati: un campo per il nome non deve essere largo
     quanto la pagina. I campi corti stanno affiancati, quelli che hanno
     bisogno di spazio lo chiedono con `.campo--largo`. */
  display: grid;
  /* `auto-fill` e non `auto-fit`: con `auto-fit` le colonne vuote collassano e
     un gruppo con un solo campo lo allarga per tutta la pagina — che e'
     esattamente il difetto che si voleva togliere. */
  grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: 0.55rem;
  align-items: start;
}
</style>
