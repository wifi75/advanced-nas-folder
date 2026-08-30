<script setup lang="ts">
/** Elenco delle cartelle pubblicate. */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import type { Share, Visibilita } from '@/api/shares'
import DettaglioShare from '@/components/DettaglioShare.vue'
import GruppoCampi from '@/components/GruppoCampi.vue'
import IndirizziPubblicazione from '@/components/IndirizziPubblicazione.vue'
import { useMountsStore } from '@/stores/mounts'
import { useSharesStore } from '@/stores/shares'

const { t } = useI18n()
const shares = useSharesStore()
const mounts = useMountsStore()

const VISIBILITA: Visibilita[] = ['pubblica', 'password', 'utenti', 'utenti_scelti', 'negata']

const nuovoAperto = ref(false)
const daEliminare = ref<Share | null>(null)

// Modifica di una pubblicazione esistente. Il nome nell'indirizzo resta fuori
// di proposito: cambiarlo romperebbe i collegamenti gia condivisi, che e
// esattamente cio che una pubblicazione serve a produrre.
const inModifica = ref<Share | null>(null)
const modifiche = ref({
  label: '',
  description: null as string | null,
  default_visibility: 'utenti' as Visibilita,
})

function apriModifica(s: Share): void {
  inModifica.value = s
  modifiche.value = {
    label: s.label,
    description: s.description,
    default_visibility: s.default_visibility,
  }
}

async function salvaModifiche(): Promise<void> {
  if (!inModifica.value) return
  salvataggio.value = true
  await shares.modifica(inModifica.value.id, modifiche.value)
  salvataggio.value = false
  inModifica.value = null
}
const salvataggio = ref(false)

const form = ref({
  slug: '',
  label: '',
  mount_id: 0,
  subpath: '',
  description: null as string | null,
  default_visibility: 'utenti' as Visibilita,
  is_enabled: true,
})

onMounted(async () => {
  await Promise.all([shares.carica(), mounts.carica()])
})

const puoCreare = computed(
  () => form.value.slug !== '' && form.value.label !== '' && form.value.mount_id > 0,
)

function apriNuovo(): void {
  form.value.mount_id = mounts.elenco[0]?.id ?? 0
  nuovoAperto.value = true
}

/**
 * L'indirizzo che uscira dall'identificatore scritto finora.
 *
 * Mostrarlo mentre si scrive e l'unico modo di rendere evidente che quel campo
 * *e* l'indirizzo: chiamarlo «identificatore» e lasciarlo lì non lo diceva, e
 * il collegamento fra i due si scopriva solo dopo aver salvato.
 */
const indirizzoPrevisto = computed(() =>
  form.value.slug ? `${window.location.origin}/${form.value.slug}` : '',
)

function proponiIdentificatore(): void {
  if (form.value.slug) return
  form.value.slug = form.value.label
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 63)
}

async function salva(): Promise<void> {
  salvataggio.value = true
  const fatto = await shares.crea(form.value)
  salvataggio.value = false
  if (fatto) {
    nuovoAperto.value = false
    form.value = {
      slug: '',
      label: '',
      mount_id: mounts.elenco[0]?.id ?? 0,
      subpath: '',
      description: null,
      default_visibility: 'utenti',
      is_enabled: true,
    }
  }
}

async function conferma(): Promise<void> {
  if (!daEliminare.value) return
  await shares.elimina(daEliminare.value.id)
  daEliminare.value = null
}

function alterna(s: Share): void {
  if (shares.aperta?.id === s.id) shares.chiudi()
  else void shares.apri(s.id)
}
</script>

<template>
  <div class="pagina">
    <header class="testata">
      <div>
        <h1>{{ t('share.titolo') }}</h1>
        <p class="sottotitolo">
          {{ t('share.sottotitolo') }}
        </p>
      </div>
      <button
        class="bottone bottone--principale"
        type="button"
        :disabled="mounts.elenco.length === 0"
        @click="apriNuovo"
      >
        {{ t('share.nuova') }}
      </button>
    </header>

    <p
      v-if="shares.errore"
      class="errore"
      role="alert"
    >
      {{ shares.errore }}
    </p>

    <p
      v-if="mounts.elenco.length === 0 && !mounts.caricamento"
      class="vuoto"
    >
      {{ t('share.servonoMount') }}
      <RouterLink to="/condivisioni">
        {{ t('menu.condivisioni') }}
      </RouterLink>
    </p>

    <p
      v-else-if="shares.caricamento"
      class="vuoto"
    >
      {{ t('comune.carico') }}
    </p>

    <p
      v-else-if="shares.elenco.length === 0"
      class="vuoto"
    >
      {{ t('share.vuoto') }}
    </p>

    <ul
      v-else
      class="elenco"
    >
      <li
        v-for="s in shares.elenco"
        :key="s.id"
        class="scheda"
      >
        <div class="intestazione">
          <div class="titoli">
            <h2>{{ s.label }}</h2>
            <p class="origine">
              /{{ s.slug }}<template v-if="s.subpath">
                · {{ s.subpath }}
              </template>
            </p>
          </div>
          <span class="stato">{{ t(`visibilita.breve_${s.default_visibility}`) }}</span>
          <span
            v-if="!s.is_enabled"
            class="stato stato--spenta"
          >{{ t('share.disattivata') }}</span>
        </div>

        <IndirizziPubblicazione :slug="s.slug" />

        <div class="azioni">
          <RouterLink
            class="bottone"
            :to="`/archivio/${s.slug}`"
          >
            {{ t('archivio.apri') }}
          </RouterLink>
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="alterna(s)"
          >
            {{ shares.aperta?.id === s.id ? t('comune.chiudi') : t('regole.titolo') }}
          </button>
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="apriModifica(s)"
          >
            {{ t('share.modifica') }}
          </button>
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="shares.modifica(s.id, { is_enabled: !s.is_enabled })"
          >
            {{ s.is_enabled ? t('share.disattivaAzione') : t('share.attivaAzione') }}
          </button>
          <button
            type="button"
            class="bottone bottone--pericolo"
            @click="daEliminare = s"
          >
            {{ t('comune.elimina') }}
          </button>
        </div>

        <DettaglioShare
          v-if="shares.aperta?.id === s.id"
          :id="s.id"
        />
      </li>
    </ul>

    <!-- nuova pubblicazione -->
    <div
      v-if="nuovoAperto"
      class="velo"
      @click.self="nuovoAperto = false"
    >
      <section
        class="pannello"
        role="dialog"
      >
        <h2>{{ t('share.nuova') }}</h2>

        <GruppoCampi
          :titolo="t('share.gruppoCosa')"
          :descrizione="t('share.gruppoCosaAiuto')"
        >
          <label class="campo">
            <span>{{ t('share.condivisione') }}</span>
            <select v-model.number="form.mount_id">
              <option
                v-for="m in mounts.elenco"
                :key="m.id"
                :value="m.id"
              >
                {{ m.label }}
              </option>
            </select>
          </label>
          <label class="campo">
            <span>{{ t('share.sottopercorso') }}</span>
            <input
              v-model="form.subpath"
              type="text"
              :placeholder="t('share.sottopercorsoAiuto')"
            >
          </label>
        </GruppoCampi>

        <GruppoCampi
          :titolo="t('share.gruppoNome')"
          :descrizione="t('share.gruppoNomeAiuto')"
        >
          <label class="campo">
            <span>{{ t('share.nome') }}</span>
            <input
              v-model="form.label"
              type="text"
              maxlength="128"
              @blur="proponiIdentificatore"
            >
          </label>
          <label class="campo">
            <span>{{ t('share.identificatore') }}</span>
            <input
              v-model="form.slug"
              type="text"
              maxlength="63"
            >
            <small class="aiuto">{{ t('share.identificatoreAiuto') }}</small>
          </label>
          <p
            v-if="indirizzoPrevisto"
            class="previsto"
          >
            {{ t('share.anteprimaIndirizzo') }}
            <span class="previsto__valore">{{ indirizzoPrevisto }}</span>
          </p>
        </GruppoCampi>

        <GruppoCampi
          :titolo="t('share.gruppoAccesso')"
          :descrizione="t('share.gruppoAccessoAiuto')"
        >
          <label class="campo">
            <span>{{ t('share.visibilitaPredefinita') }}</span>
            <select v-model="form.default_visibility">
              <option
                v-for="v in VISIBILITA"
                :key="v"
                :value="v"
              >
                {{ t(`visibilita.${v}`) }}
              </option>
            </select>
          </label>
        </GruppoCampi>





        <p
          v-if="shares.errore"
          class="errore"
          role="alert"
        >
          {{ shares.errore }}
        </p>

        <footer class="azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="nuovoAperto = false"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            class="bottone bottone--principale"
            type="button"
            :disabled="!puoCreare || salvataggio"
            @click="salva"
          >
            {{ salvataggio ? t('share.creando') : t('comune.crea') }}
          </button>
        </footer>
      </section>
    </div>

    <!-- modifica di una pubblicazione -->
    <div
      v-if="inModifica"
      class="velo"
      @click.self="inModifica = null"
    >
      <section class="pannello">
        <h2>{{ t('share.modificaTitolo', { nome: inModifica.label }) }}</h2>

        <label class="campo">
          <span>{{ t('share.nome') }}</span>
          <input
            v-model="modifiche.label"
            type="text"
            maxlength="128"
          >
        </label>

        <label class="campo">
          <span>{{ t('share.descrizione') }}</span>
          <input
            v-model="modifiche.description"
            type="text"
          >
        </label>

        <label class="campo">
          <span>{{ t('share.visibilitaPredefinita') }}</span>
          <select v-model="modifiche.default_visibility">
            <option
              v-for="v in VISIBILITA"
              :key="v"
              :value="v"
            >
              {{ t(`visibilita.${v}`) }}
            </option>
          </select>
        </label>

        <p class="aiuto">
          {{ t('share.identificatoreImmutabile') }}
        </p>

        <p
          v-if="shares.errore"
          class="errore"
          role="alert"
        >
          {{ shares.errore }}
        </p>

        <footer class="azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="inModifica = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            class="bottone bottone--principale"
            type="button"
            :disabled="!modifiche.label || salvataggio"
            @click="salvaModifiche"
          >
            {{ salvataggio ? t('comune.carico') : t('comune.salva') }}
          </button>
        </footer>
      </section>
    </div>

    <!-- conferma eliminazione -->
    <div
      v-if="daEliminare"
      class="velo"
      @click.self="daEliminare = null"
    >
      <section
        class="pannello conferma"
        role="alertdialog"
      >
        <h2>{{ t('share.confermaTitolo', { nome: daEliminare.label }) }}</h2>
        <p>{{ t('share.confermaTesto') }}</p>
        <footer class="azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="daEliminare = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="button"
            class="bottone bottone--pericolo"
            @click="conferma"
          >
            {{ t('comune.elimina') }}
          </button>
        </footer>
      </section>
    </div>
  </div>
</template>

<style scoped>

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
  gap: 0.6rem;
}

.titoli {
  flex: 1;
  min-inline-size: 0;
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

.stato--spenta {
  color: var(--attenzione);
  border-color: var(--attenzione);
}

.azioni {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}



/* Un collegamento, non un bottone: deve poter essere aperto in una nuova
   scheda: e' il modo naturale di consultare una cartella mentre se ne
   configurano i permessi. */




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

.pannello {
  width: min(520px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.75rem;
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  box-shadow: var(--ombra);
}

.pannello h2 {
  margin: 0;
  font-size: 1.15rem;
}

.conferma p {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--testo-tenue);
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.875rem;
}

.doppio {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.9rem;
}

.campo input,
.campo select {
  padding: 0.55rem 0.7rem;
  font: inherit;
  color: var(--testo);
  background: var(--sfondo);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

.pannello .azioni {
  justify-content: flex-end;
}




.aiuto {
  color: var(--testo-tenue);
  font-size: 0.78rem;
}

.previsto {
  margin: 0.15rem 0 0;
  font-size: 0.85rem;
  color: var(--testo-tenue);
}

.previsto__valore {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--testo);
  word-break: break-all;
}
</style>
