<script setup lang="ts">
/** Elenco delle cartelle pubblicate. */
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { chiudiConEsc } from '@/composables/finestra'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import type { Visibilita } from '@/api/shares'
import GruppoCampi from '@/components/GruppoCampi.vue'
import IndirizziPubblicazione from '@/components/IndirizziPubblicazione.vue'
import SfogliaMount from '@/components/SfogliaMount.vue'
import { useMountsStore } from '@/stores/mounts'
import { useSharesStore } from '@/stores/shares'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const shares = useSharesStore()
const mounts = useMountsStore()

const VISIBILITA: Visibilita[] = ['pubblica', 'password', 'utenti', 'utenti_scelti', 'negata']

const nuovoAperto = ref(false)

/** Da quale condivisione arriva: in un elenco che le mischia tutte serve. */
function nomeOrigine(idMount: number): string {
  return mounts.elenco.find((m) => m.id === idMount)?.label ?? ''
}

// Modifica di una pubblicazione esistente. Il nome nell'indirizzo resta fuori
// di proposito: cambiarlo romperebbe i collegamenti gia condivisi, che e
// esattamente cio che una pubblicazione serve a produrre.


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

// --- sfoglia e pubblica in blocco ---
//
// Scrivere il percorso a mano resta possibile: questa e' un'alternativa per
// chi preferisce vedere l'albero della condivisione invece di ricordarselo.
const modalitaSottopercorso = ref<'scrivi' | 'sfoglia'>('scrivi')
const percorsiSelezionati = ref<string[]>([])
const pubblicandoBlocco = ref(false)
const erroreBlocco = ref('')

function apriNuovo(mountId?: number): void {
  form.value.mount_id = mountId ?? mounts.elenco[0]?.id ?? 0
  modalitaSottopercorso.value = 'scrivi'
  percorsiSelezionati.value = []
  erroreBlocco.value = ''
  nuovoAperto.value = true
}

// `?nuova=<id>` apre la creazione gia' legata a quella condivisione: e' il
// «+ pubblica» dell'albero, che deve creare la cartella dove e' stato premuto
// senza far riscegliere l'origine.
watch(
  () => route.query.nuova,
  async (valore) => {
    if (valore === undefined) return
    if (mounts.elenco.length === 0) await mounts.carica()
    apriNuovo(Number(valore))
    await router.replace({ query: {} })
  },
  { immediate: true },
)

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

function slugifica(testo: string): string {
  return testo
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 63)
}

function proponiIdentificatore(): void {
  if (form.value.slug) return
  form.value.slug = slugifica(form.value.label)
}

function nomeCartella(percorso: string): string {
  const parti = percorso.split('/').filter(Boolean)
  return parti[parti.length - 1] ?? percorso
}

async function pubblicaSelezionate(): Promise<void> {
  pubblicandoBlocco.value = true
  erroreBlocco.value = ''
  let falliti = 0
  // Uno per volta, non in parallelo: due percorsi con lo stesso nome
  // finale produrrebbero lo stesso slug, e il secondo deve vedere l'errore
  // del primo restando comunque selezionato per essere rinominato a mano.
  for (const percorso of [...percorsiSelezionati.value]) {
    const nome = nomeCartella(percorso)
    const fatto = await shares.crea({
      slug: slugifica(nome),
      label: nome,
      mount_id: form.value.mount_id,
      subpath: percorso,
      description: null,
      default_visibility: form.value.default_visibility,
      is_enabled: true,
    })
    if (fatto) {
      percorsiSelezionati.value = percorsiSelezionati.value.filter((p) => p !== percorso)
    } else {
      falliti += 1
    }
  }
  pubblicandoBlocco.value = false
  if (falliti > 0) {
    erroreBlocco.value = t('share.pubblicazioneBloccoErrore', { n: falliti }, falliti)
  } else {
    nuovoAperto.value = false
  }
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

// Le finestre si chiudono con Esc, non cliccando sullo sfondo: un clic di
// troppo faceva perdere quello che si stava scrivendo.
chiudiConEsc(
  () => nuovoAperto.value,
  () => {
    nuovoAperto.value = false
  },
)
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
        @click="apriNuovo()"
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
            <h2>
              <RouterLink :to="`/pubblicazioni/${s.id}`">
                {{ s.label }}
              </RouterLink>
            </h2>
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

        <!-- Modifica, permessi, link e rimozione stanno nella pagina della
             pubblicazione: ripeterli qui significava mantenere due volte le
             stesse funzioni, e nasconderle a chi arriva dall'albero. -->
        <div class="azioni">
          <RouterLink
            class="bottone bottone--principale"
            :to="`/pubblicazioni/${s.id}`"
          >
            {{ t('share.gestisci') }}
          </RouterLink>
          <RouterLink
            class="bottone"
            :to="`/archivio/${s.slug}`"
          >
            {{ t('archivio.apri') }}
          </RouterLink>
          <span class="origine-nome">{{ nomeOrigine(s.mount_id) }}</span>
        </div>
      </li>
    </ul>

    <!-- nuova pubblicazione -->
    <div
      v-if="nuovoAperto"
      class="velo"
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
          <div class="campo">
            <div class="schede-modalita">
              <button
                type="button"
                class="scheda-modalita"
                :class="{ 'scheda-modalita--attiva': modalitaSottopercorso === 'scrivi' }"
                @click="modalitaSottopercorso = 'scrivi'"
              >
                {{ t('share.modalitaScrivi') }}
              </button>
              <button
                type="button"
                class="scheda-modalita"
                :class="{ 'scheda-modalita--attiva': modalitaSottopercorso === 'sfoglia' }"
                :disabled="!form.mount_id"
                @click="modalitaSottopercorso = 'sfoglia'"
              >
                {{ t('share.modalitaSfoglia') }}
              </button>
            </div>

            <label
              v-if="modalitaSottopercorso === 'scrivi'"
              class="campo"
            >
              <span>{{ t('share.sottopercorso') }}</span>
              <input
                v-model="form.subpath"
                type="text"
                :placeholder="t('share.sottopercorsoAiuto')"
              >
            </label>
            <template v-else>
              <span>{{ t('sfogliaMount.titolo') }}</span>
              <SfogliaMount
                v-model="percorsiSelezionati"
                :mount-id="form.mount_id"
              />
            </template>
          </div>
        </GruppoCampi>

        <GruppoCampi
          v-if="modalitaSottopercorso === 'scrivi'"
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
          v-if="shares.errore || erroreBlocco"
          class="errore"
          role="alert"
        >
          {{ erroreBlocco || shares.errore }}
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
            v-if="modalitaSottopercorso === 'scrivi'"
            class="bottone bottone--principale"
            type="button"
            :disabled="!puoCreare || salvataggio"
            @click="salva"
          >
            {{ salvataggio ? t('share.creando') : t('comune.crea') }}
          </button>
          <button
            v-else
            class="bottone bottone--principale"
            type="button"
            :disabled="percorsiSelezionati.length === 0 || pubblicandoBlocco"
            @click="pubblicaSelezionate"
          >
            {{
              pubblicandoBlocco
                ? t('share.creando')
                : t(
                  'share.pubblicaSelezionate',
                  { n: percorsiSelezionati.length },
                  percorsiSelezionati.length,
                )
            }}
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
  font-family: var(--font-mono);
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

.campo {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.875rem;
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

.schede-modalita {
  display: flex;
  gap: 0.35rem;
  margin-bottom: 0.15rem;
}

.scheda-modalita {
  padding: 0.35rem 0.75rem;
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--testo-tenue);
  background: transparent;
  border: 1px solid var(--bordo);
  border-radius: 999px;
  cursor: pointer;
}

.scheda-modalita--attiva {
  color: var(--accento);
  border-color: color-mix(in srgb, var(--accento) 40%, var(--bordo));
  background: color-mix(in srgb, var(--accento) 12%, transparent);
}

.scheda-modalita:disabled {
  opacity: 0.5;
  cursor: default;
}




.origine-nome {
  margin-left: auto;
  font-size: 0.82rem;
  color: var(--testo-tenue);
}

.aiuto {
  color: var(--testo-tenue);
  font-size: 0.78rem;
}

/* L'avviso compare solo quando il nome e' stato davvero cambiato: mostrarlo
   sempre lo renderebbe sfondo, e nessuno lo leggerebbe nel momento in cui
   conta. */
.aiuto--attenzione {
  color: var(--attenzione);
}

.previsto {
  margin: 0.15rem 0 0;
  font-size: 0.85rem;
  color: var(--testo-tenue);
}

.previsto__valore {
  font-family: var(--font-mono);
  color: var(--testo);
  word-break: break-all;
}
</style>
