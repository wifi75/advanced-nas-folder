<script setup lang="ts">
/**
 * Tutto quello che riguarda **una** condivisione NFS, in un posto solo.
 *
 * Prima era sparso: lo stato del montaggio nell'elenco delle condivisioni, le
 * cartelle pubblicate da questa condivisione in un'altra pagina insieme a
 * quelle di tutte le altre. Chi arrivava senza conoscere il pannello non aveva
 * modo di capire che erano parti della stessa cosa.
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import GruppoCampi from '@/components/GruppoCampi.vue'
import IndirizziPubblicazione from '@/components/IndirizziPubblicazione.vue'
import Schede from '@/components/Schede.vue'
import { useMountsStore } from '@/stores/mounts'
import { useSharesStore } from '@/stores/shares'

const route = useRoute()
const router = useRouter()
const mounts = useMountsStore()
const shares = useSharesStore()
const { t } = useI18n()

const id = computed(() => Number(route.params.id))
const mount = computed(() => mounts.elenco.find((m) => m.id === id.value))

/** Le pubblicazioni che partono da questa condivisione, e solo quelle. */
const pubblicazioni = computed(() => shares.elenco.filter((s) => s.mount_id === id.value))

const schede = computed(() => [
  { chiave: 'panoramica', etichetta: t('condivisione.panoramica') },
  { chiave: 'montaggio', etichetta: t('condivisione.montaggio') },
  { chiave: 'pubblicazioni', etichetta: t('condivisione.pubblicazioni') },
  { chiave: 'avanzate', etichetta: t('condivisione.avanzate') },
])

const opzioni = ref({ label: '', nfs_version: '3', automount: true, consenti_scrittura: false })
const salvato = ref(false)

function ricarica(): void {
  if (!mount.value) return
  opzioni.value = {
    label: mount.value.label,
    nfs_version: mount.value.nfs_version,
    automount: mount.value.automount,
    consenti_scrittura: mount.value.requested_access === 'rw',
  }
}

watch(mount, ricarica, { immediate: true })

onMounted(async () => {
  if (mounts.elenco.length === 0) await mounts.carica()
  if (shares.elenco.length === 0) await shares.carica()
  void mounts.dettaglio(id.value)
})

async function salva(): Promise<void> {
  salvato.value = false
  if (await mounts.modifica(id.value, opzioni.value)) salvato.value = true
}

/** Lo stato del montaggio, che mancava del tutto in questa pagina: era
 *  visibile solo nell'elenco, cioe' nel posto da cui si e' appena usciti. */
const etichettaStato = computed(() => {
  switch (mount.value?.state) {
    case 'montato':
      return t('mount.statoMontato')
    case 'smontato':
      return t('mount.statoSmontato')
    case 'errore':
      return t('mount.statoErrore')
    default:
      return t('mount.statoInCorso')
  }
})

const classeStato = computed(() => {
  switch (mount.value?.state) {
    case 'montato':
      return 'stato-pillola--ok'
    case 'errore':
      return 'stato-pillola--errore'
    default:
      return 'stato-pillola--attesa'
  }
})

const daEliminare = ref(false)

async function elimina(): Promise<void> {
  if (await mounts.elimina(id.value)) await router.push('/condivisioni')
}
</script>

<template>
  <div class="pagina">
    <p class="briciole">
      <RouterLink to="/condivisioni">
        {{ t('menu.condivisioni') }}
      </RouterLink>
      <span aria-hidden="true">&rsaquo;</span>
      <span>{{ mount?.label ?? '...' }}</span>
    </p>

    <header
      class="testata-tinta"
      :style="{ '--tinta': 'var(--tinta-nfs)' }"
    >
      <div class="testata-tinta__riga">
        <span
          class="pastiglia-titolo"
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
            <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z M12 11v3 M9 17h6" />
          </svg>
        </span>
        <h1>{{ mount?.label ?? t('comune.carico') }}</h1>
        <span
          v-if="mount"
          class="stato-pillola"
          :class="classeStato"
        >{{ etichettaStato }}</span>
      </div>
      <p
        v-if="mount"
        class="testata-tinta__nota mono"
      >
        {{ mount.server }}:{{ mount.export_path }}
      </p>
    </header>

    <p
      v-if="mounts.errore"
      class="errore"
      role="alert"
    >
      {{ mounts.errore }}
    </p>

    <Schede
      v-if="mount"
      v-slot="{ attiva }"
      :schede="schede"
    >
      <template v-if="attiva === 'panoramica'">
        <dl class="dati">
          <div>
            <dt>{{ t('mount.percorso') }}</dt>
            <dd><code class="percorso">{{ mount.mountpoint }}</code></dd>
          </div>
          <div>
            <dt>{{ t('mount.versione') }}</dt>
            <dd>NFS {{ mount.nfs_version }}</dd>
          </div>
          <div>
            <dt>{{ t('mount.accessoRichiesto') }}</dt>
            <dd>
              {{
                mount.requested_access === 'rw'
                  ? t('mount.letturaScrittura')
                  : t('mount.solaLettura')
              }}
            </dd>
          </div>
          <div>
            <dt>{{ t('mount.accessoEffettivo') }}</dt>
            <dd>
              {{
                mount.effective_read_write === null
                  ? t('mount.nonRilevato')
                  : mount.effective_read_write
                    ? t('mount.letturaScrittura')
                    : t('mount.solaLettura')
              }}
            </dd>
          </div>
        </dl>

        <p
          v-if="mount.last_error"
          class="errore"
        >
          {{ mount.last_error }}
        </p>

        <div class="azioni">
          <button
            v-if="mount.state !== 'montato'"
            type="button"
            class="bottone bottone--principale"
            :disabled="mounts.inCorso.has(mount.id)"
            @click="mounts.avvia(mount.id)"
          >
            {{ t('mount.monta') }}
          </button>
          <button
            v-else
            type="button"
            class="bottone bottone--tenue"
            :disabled="mounts.inCorso.has(mount.id)"
            @click="mounts.ferma(mount.id)"
          >
            {{ t('mount.smonta') }}
          </button>
          <button
            type="button"
            class="bottone bottone--tenue"
            :disabled="mounts.inCorso.has(mount.id)"
            @click="mounts.dettaglio(mount.id)"
          >
            {{ t('mount.rileggi') }}
          </button>
        </div>
      </template>

      <template v-else-if="attiva === 'montaggio'">
        <GruppoCampi
          :titolo="t('nuovoMount.gruppoNome')"
          tinta="var(--tinta-nfs)"
          icona="M3 7a2 2 0 0 1 2-2h6l9 9-8 8-9-9Z M7.5 9.5h.01"
          :descrizione="t('nuovoMount.gruppoNomeAiuto')"
        >
          <label class="campo">
            <span>{{ t('nuovoMount.nome') }}</span>
            <input
              v-model="opzioni.label"
              type="text"
              maxlength="128"
            >
          </label>
        </GruppoCampi>

        <GruppoCampi
          :titolo="t('nuovoMount.gruppoMontaggio')"
          tinta="var(--tinta-nfs)"
          icona="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z M12 11v3 M9 17h6"
          :descrizione="t('nuovoMount.gruppoMontaggioAiuto')"
        >
          <label class="campo">
            <span>{{ t('nuovoMount.versioneNfs') }}</span>
            <select v-model="opzioni.nfs_version">
              <option value="3">
                3
              </option>
              <option value="4.1">
                4.1
              </option>
              <option value="4.2">
                4.2
              </option>
            </select>
          </label>
          <label class="campo interruttore">
            <input
              v-model="opzioni.automount"
              type="checkbox"
            >
            <span>{{ t('nuovoMount.montaARichiesta') }}</span>
          </label>
          <label class="campo interruttore">
            <input
              v-model="opzioni.consenti_scrittura"
              type="checkbox"
            >
            <span>
              <strong>{{ t('nuovoMount.consentiScrittura') }}</strong>
              <em>{{ t('nuovoMount.consentiScritturaDettaglio') }}</em>
            </span>
          </label>
        </GruppoCampi>

        <div class="azioni">
          <button
            type="button"
            class="bottone bottone--principale"
            :disabled="mounts.inCorso.has(mount.id)"
            @click="salva"
          >
            {{ t('comune.salva') }}
          </button>
          <span
            v-if="salvato"
            class="fatto"
            role="status"
          >{{ t('condivisione.salvato') }}</span>
        </div>
      </template>

      <template v-else-if="attiva === 'pubblicazioni'">
        <p
          v-if="pubblicazioni.length === 0"
          class="vuoto"
        >
          {{ t('condivisione.nessunaPubblicazione') }}
        </p>

        <ul
          v-else
          class="elenco"
        >
          <li
            v-for="p in pubblicazioni"
            :key="p.id"
            class="scheda"
          >
            <div class="intestazione">
              <h2>{{ p.label }}</h2>
              <span class="stato">{{ t(`visibilita.breve_${p.default_visibility}`) }}</span>
            </div>
            <IndirizziPubblicazione :slug="p.slug" />
            <div class="azioni">
              <RouterLink
                class="bottone"
                :to="`/archivio/${p.slug}`"
              >
                {{ t('archivio.apri') }}
              </RouterLink>
              <RouterLink
                class="bottone bottone--tenue"
                :to="`/pubblicazioni/${p.id}`"
              >
                {{ t('condivisione.gestisci') }}
              </RouterLink>
            </div>
          </li>
        </ul>

        <div class="azioni">
          <!-- `?nuova=` apre direttamente la creazione con questa condivisione
               gia' scelta. Portare all'elenco faceva ricomparire un secondo
               pulsante «Nuova pubblicazione» da premere di nuovo, e
               ricominciare da capo la scelta dell'origine. -->
          <RouterLink
            class="bottone bottone--principale"
            :to="`/pubblicazioni?nuova=${mount.id}`"
          >
            {{ t('share.nuova') }}
          </RouterLink>
        </div>
      </template>

      <template v-else>
        <GruppoCampi
          :titolo="t('condivisione.zonaPericolosa')"
          tinta="var(--errore)"
          icona="M4 7h16 M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2 M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13"
          :descrizione="t('condivisione.zonaPericolosaAiuto')"
        >
          <p
            v-if="pubblicazioni.length > 0"
            class="avviso"
          >
            {{ t('condivisione.haPubblicazioni', { n: pubblicazioni.length }) }}
          </p>
          <div class="azioni">
            <button
              type="button"
              class="bottone bottone--pericolo"
              @click="daEliminare = true"
            >
              {{ t('comune.elimina') }}
            </button>
          </div>
        </GruppoCampi>
      </template>
    </Schede>

    <div
      v-if="daEliminare"
      class="velo"
      @click.self="daEliminare = false"
    >
      <section class="pannello">
        <h2>{{ t('mount.confermaTitolo', { nome: mount?.label ?? '' }) }}</h2>
        <p>{{ t('condivisione.confermaEliminazione') }}</p>
        <footer class="azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="daEliminare = false"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="button"
            class="bottone bottone--pericolo"
            @click="elimina"
          >
            {{ t('comune.elimina') }}
          </button>
        </footer>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* La scheda dello stato prende la tinta di cio' che dice: montato, in attesa,
   errore. Prima era una pillola in alto a destra, lontana dai dati che
   descrive e facile da non guardare. */
.dato-stato dd {
  font-weight: 600;
}

.dato-stato--ok {
  border-color: color-mix(in srgb, var(--ok) 45%, var(--vetro-bordo)) !important;
  background:
    linear-gradient(
      158deg,
      color-mix(in srgb, var(--ok) 20%, transparent),
      color-mix(in srgb, var(--ok) 8%, transparent)
    ) !important;
}

.dato-stato--ok dd {
  color: var(--ok);
}

.dato-stato--attesa {
  border-color: color-mix(in srgb, var(--attenzione) 45%, var(--vetro-bordo)) !important;
  background:
    linear-gradient(
      158deg,
      color-mix(in srgb, var(--attenzione) 20%, transparent),
      color-mix(in srgb, var(--attenzione) 8%, transparent)
    ) !important;
}

.dato-stato--attesa dd {
  color: var(--attenzione);
}

.dato-stato--errore {
  border-color: color-mix(in srgb, var(--errore) 45%, var(--vetro-bordo)) !important;
  background:
    linear-gradient(
      158deg,
      color-mix(in srgb, var(--errore) 20%, transparent),
      color-mix(in srgb, var(--errore) 8%, transparent)
    ) !important;
}

.dato-stato--errore dd {
  color: var(--errore);
}

.stato-pillola {
  margin-left: auto;
  background: var(--superficie);
}

.identita {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.briciole {
  display: flex;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.875rem;
  color: var(--testo-tenue);
}





.elenco {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.intestazione {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
}

.intestazione h2 {
  margin: 0;
  font-size: 1.05rem;
}


.avviso {
  margin: 0;
  color: var(--attenzione);
}

.errore {
  margin: 0;
  color: var(--errore);
}

.fatto {
  font-size: 0.875rem;
  color: var(--ok);
}
</style>
