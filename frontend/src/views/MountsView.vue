<script setup lang="ts">
/**
 * Elenco delle condivisioni NFS.
 *
 * Per ogni mount si mostrano sia lo stato richiesto sia quello effettivo:
 * mostrare solo il primo significherebbe dire all'utente che la scrittura è
 * attiva anche quando il NAS la sta negando.
 */
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import type { Mount } from '@/api/mounts'
import ImportaFstab from '@/components/ImportaFstab.vue'
import NuovoMount from '@/components/NuovoMount.vue'
import { useMountsStore } from '@/stores/mounts'
import { useSharesStore } from '@/stores/shares'

const mounts = useMountsStore()
const shares = useSharesStore()
const { t } = useI18n()

// Una cartella montata non e ancora raggiungibile da nessuno: senza dirlo qui,
// il passo successivo resta invisibile e sembra che manchi qualcosa.
function pubblicazioni(idMount: number): number {
  return shares.elenco.filter((s) => s.mount_id === idMount).length
}
const nuovoAperto = ref(false)
const daEliminare = ref<Mount | null>(null)

onMounted(() => {
  void mounts.carica()
  // Serve per sapere quali mount sono gia pubblicati: senza, il conteggio
  // direbbe zero anche quando le pubblicazioni ci sono.
  void shares.carica()
})

function etichettaStato(m: Mount): string {
  switch (m.state) {
    case 'montato':
      return t('mount.statoMontato')
    case 'smontato':
      return t('mount.statoSmontato')
    case 'errore':
      return t('mount.statoErrore')
    default:
      return t('mount.statoConfigurato')
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
        <h1>{{ t('mount.titolo') }}</h1>
        <p class="sottotitolo">
          {{ t('mount.sottotitolo') }}
        </p>
      </div>
      <button
        type="button"
        @click="nuovoAperto = true"
      >
        {{ t('mount.nuova') }}
      </button>
    </header>

    <ImportaFstab @importato="mounts.carica()" />

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
      {{ t('comune.carico') }}
    </p>

    <p
      v-else-if="mounts.elenco.length === 0"
      class="vuoto"
    >
      {{ t('mount.vuoto') }}
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
            <dt>{{ t('mount.percorso') }}</dt>
            <dd class="mono">
              {{ m.mountpoint }}
            </dd>
          </div>
          <div>
            <dt>{{ t('mount.versione') }}</dt>
            <dd>NFS {{ m.nfs_version }}</dd>
          </div>
          <div>
            <dt>{{ t('mount.accessoRichiesto') }}</dt>
            <dd>
              {{ m.requested_access === 'rw' ? t('mount.letturaScrittura') : t('mount.solaLettura') }}
            </dd>
          </div>
          <div>
            <dt>{{ t('mount.accessoEffettivo') }}</dt>
            <dd>
              <template v-if="m.effective_read_write === null">
                {{ t('mount.nonRilevato') }}
              </template>
              <template v-else-if="m.effective_read_write">
                {{ t('mount.letturaScrittura') }}
              </template>
              <template v-else>
                {{ t('mount.solaLettura') }}
              </template>
            </dd>
          </div>
        </dl>

        <p
          v-if="scritturaNegata(m)"
          class="allarme"
          role="alert"
        >
          <strong>{{ t('mount.scritturaNegata') }}</strong>
          {{ t('mount.scritturaNegataDettaglio') }}
        </p>

        <p
          v-else-if="m.state === 'errore' && m.last_error"
          class="allarme"
          role="alert"
        >
          {{ m.last_error }}
        </p>

        <p class="pubblicazioni">
          {{ t('mount.giaPubblicata', { count: pubblicazioni(m.id) }, pubblicazioni(m.id)) }}
          <RouterLink
            v-if="m.state === 'montato'"
            class="pubblica"
            to="/pubblicazioni"
          >
            {{ t('mount.pubblicaQuesta') }}
          </RouterLink>
        </p>

        <div class="azioni">
          <button
            type="button"
            class="secondario"
            :disabled="mounts.inCorso.has(m.id)"
            @click="mounts.dettaglio(m.id)"
          >
            {{ t('mount.rileggi') }}
          </button>
          <button
            v-if="m.state !== 'montato'"
            type="button"
            :disabled="mounts.inCorso.has(m.id)"
            @click="mounts.avvia(m.id)"
          >
            {{ t('mount.monta') }}
          </button>
          <button
            v-else
            type="button"
            class="secondario"
            :disabled="mounts.inCorso.has(m.id)"
            @click="mounts.ferma(m.id)"
          >
            {{ t('mount.smonta') }}
          </button>
          <button
            type="button"
            class="pericolo"
            :disabled="mounts.inCorso.has(m.id)"
            @click="daEliminare = m"
          >
            {{ t('comune.elimina') }}
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
        <h2>{{ t('mount.confermaTitolo', { nome: daEliminare.label }) }}</h2>
        <p>{{ t('mount.confermaTesto') }}</p>
        <div class="azioni">
          <button
            type="button"
            class="secondario"
            @click="daEliminare = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="button"
            class="pericolo"
            @click="conferma"
          >
            {{ t('comune.elimina') }}
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

.pubblicazioni {
  margin: 0.5rem 0 0;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.6rem;
  font-size: 0.9rem;
  color: var(--testo-tenue);
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
