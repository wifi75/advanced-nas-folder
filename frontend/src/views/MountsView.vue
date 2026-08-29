<script setup lang="ts">
/**
 * Elenco delle condivisioni NFS.
 *
 * Per ogni mount si mostrano sia lo stato richiesto sia quello effettivo:
 * mostrare solo il primo significherebbe dire all'utente che la scrittura è
 * attiva anche quando il NAS la sta negando.
 */
import { onMounted, ref } from 'vue'

import type { Mount } from '@/api/mounts'
import NuovoMount from '@/components/NuovoMount.vue'
import { useMountsStore } from '@/stores/mounts'

const mounts = useMountsStore()
const nuovoAperto = ref(false)
const daEliminare = ref<Mount | null>(null)

onMounted(() => mounts.carica())

function etichettaStato(m: Mount): string {
  switch (m.state) {
    case 'montato':
      return 'Montato'
    case 'smontato':
      return 'Non montato'
    case 'errore':
      return 'Errore'
    default:
      return 'Configurato'
  }
}

/** Vero quando è stata chiesta la scrittura ma il NAS la nega. */
function scritturaNegata(m: Mount): boolean {
  return m.requested_access === 'rw' && m.effective_read_write === false
}

async function conferma(): Promise<void> {
  if (!daEliminare.value) return
  await mounts.elimina(daEliminare.value.id)
  daEliminare.value = null
}

function creato(): void {
  nuovoAperto.value = false
  void mounts.carica()
}
</script>

<template>
  <div class="pagina">
    <header class="testata">
      <div>
        <h1>Condivisioni NFS</h1>
        <p class="sottotitolo">
          Monta le cartelle del NAS senza toccare file di configurazione.
        </p>
      </div>
      <button
        type="button"
        @click="nuovoAperto = true"
      >
        Nuova condivisione
      </button>
    </header>

    <p
      v-if="mounts.errore"
      class="errore"
      role="alert"
    >
      {{ mounts.errore }}
    </p>

    <p
      v-if="mounts.caricamento"
      class="vuoto"
    >
      Carico…
    </p>

    <p
      v-else-if="mounts.elenco.length === 0"
      class="vuoto"
    >
      Nessuna condivisione configurata. Comincia da <em>Nuova condivisione</em>:
      il pannello legge dal NAS l'elenco delle cartelle disponibili.
    </p>

    <ul
      v-else
      class="elenco"
    >
      <li
        v-for="m in mounts.elenco"
        :key="m.id"
        class="scheda"
      >
        <div class="intestazione">
          <div>
            <h2>{{ m.label }}</h2>
            <p class="origine">
              {{ m.server }}:{{ m.export_path }}
            </p>
          </div>
          <span
            class="stato"
            :class="`stato--${m.state}`"
          >
            {{ etichettaStato(m) }}
          </span>
        </div>

        <dl class="dettagli">
          <div>
            <dt>Percorso</dt>
            <dd class="mono">
              {{ m.mountpoint }}
            </dd>
          </div>
          <div>
            <dt>Versione</dt>
            <dd>NFS {{ m.nfs_version }}</dd>
          </div>
          <div>
            <dt>Accesso richiesto</dt>
            <dd>{{ m.requested_access === 'rw' ? 'Lettura e scrittura' : 'Sola lettura' }}</dd>
          </div>
          <div>
            <dt>Accesso effettivo</dt>
            <dd>
              <template v-if="m.effective_read_write === null">
                Non rilevato
              </template>
              <template v-else-if="m.effective_read_write">
                Lettura e scrittura
              </template>
              <template v-else>
                Sola lettura
              </template>
            </dd>
          </div>
        </dl>

        <p
          v-if="scritturaNegata(m)"
          class="allarme"
          role="alert"
        >
          <strong>Il NAS sta negando la scrittura.</strong>
          Hai richiesto lettura e scrittura, ma la condivisione risulta in sola
          lettura. Va abilitata anche nei permessi NFS della cartella sul NAS.
        </p>

        <p
          v-else-if="m.state === 'errore' && m.last_error"
          class="allarme"
          role="alert"
        >
          {{ m.last_error }}
        </p>

        <div class="azioni">
          <button
            type="button"
            class="secondario"
            :disabled="mounts.inCorso.has(m.id)"
            @click="mounts.dettaglio(m.id)"
          >
            Rileggi stato
          </button>
          <button
            v-if="m.state !== 'montato'"
            type="button"
            :disabled="mounts.inCorso.has(m.id)"
            @click="mounts.avvia(m.id)"
          >
            Monta
          </button>
          <button
            v-else
            type="button"
            class="secondario"
            :disabled="mounts.inCorso.has(m.id)"
            @click="mounts.ferma(m.id)"
          >
            Smonta
          </button>
          <button
            type="button"
            class="pericolo"
            :disabled="mounts.inCorso.has(m.id)"
            @click="daEliminare = m"
          >
            Elimina
          </button>
        </div>
      </li>
    </ul>

    <NuovoMount
      v-if="nuovoAperto"
      @chiudi="nuovoAperto = false"
      @creato="creato"
    />

    <div
      v-if="daEliminare"
      class="velo"
      @click.self="daEliminare = null"
    >
      <section
        class="conferma"
        role="alertdialog"
      >
        <h2>Eliminare «{{ daEliminare.label }}»?</h2>
        <p>
          La condivisione viene smontata e la sua configurazione rimossa dal
          server. <strong>I file sul NAS non vengono toccati.</strong>
        </p>
        <div class="azioni">
          <button
            type="button"
            class="secondario"
            @click="daEliminare = null"
          >
            Annulla
          </button>
          <button
            type="button"
            class="pericolo"
            @click="conferma"
          >
            Elimina
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.pagina {
  flex: 1;
  width: min(880px, 100% - 2.5rem);
  margin-inline: auto;
  padding-block: 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.testata {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

h1 {
  margin: 0 0 0.3rem;
  font-size: clamp(1.5rem, 3.5vw, 2rem);
  letter-spacing: -0.02em;
}

.sottotitolo {
  margin: 0;
  color: var(--testo-tenue);
  font-size: 0.9375rem;
}

.elenco {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.scheda {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  padding: 1.15rem 1.25rem;
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

.intestazione {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.intestazione h2 {
  margin: 0 0 0.15rem;
  font-size: 1.05rem;
}

.origine {
  margin: 0;
  font-family: ui-monospace, monospace;
  font-size: 0.8125rem;
  color: var(--testo-tenue);
}

.stato {
  flex: none;
  padding: 0.2rem 0.6rem;
  font-size: 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--bordo);
  color: var(--testo-tenue);
}

.stato--montato {
  color: var(--ok);
  border-color: var(--ok);
}

.stato--errore {
  color: var(--errore);
  border-color: var(--errore);
}

.dettagli {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin: 0;
}

.dettagli dt {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--testo-tenue);
}

.dettagli dd {
  margin: 0.15rem 0 0;
  font-size: 0.875rem;
}

.mono {
  font-family: ui-monospace, monospace;
  font-size: 0.8125rem;
  overflow-wrap: anywhere;
}

.allarme {
  margin: 0;
  padding: 0.75rem 0.95rem;
  font-size: 0.875rem;
  background: var(--superficie-alt);
  border: 1px solid var(--attenzione);
  border-left-width: 3px;
  border-radius: var(--raggio);
}

.azioni {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

button {
  padding: 0.45rem 0.85rem;
  font: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--accento-testo);
  background: var(--accento);
  border: none;
  border-radius: var(--raggio);
  cursor: pointer;
}

button:disabled {
  opacity: 0.55;
  cursor: default;
}

button.secondario {
  color: var(--testo);
  background: transparent;
  border: 1px solid var(--bordo);
}

button.pericolo {
  color: var(--errore);
  background: transparent;
  border: 1px solid var(--errore);
}

.vuoto {
  margin: 0;
  padding: 2rem 1.25rem;
  text-align: center;
  color: var(--testo-tenue);
  background: var(--superficie);
  border: 1px dashed var(--bordo);
  border-radius: var(--raggio);
}

.errore {
  margin: 0;
  padding: 0.75rem 0.95rem;
  font-size: 0.875rem;
  color: var(--errore);
  border: 1px solid var(--errore);
  border-radius: var(--raggio);
}

.velo {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgb(0 0 0 / 45%);
  z-index: 10;
}

.conferma {
  width: min(420px, 100%);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  box-shadow: var(--ombra);
}

.conferma h2 {
  margin: 0;
  font-size: 1.05rem;
}

.conferma p {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--testo-tenue);
}

.conferma .azioni {
  justify-content: flex-end;
}
</style>
