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

    <header class="testata">
      <div>
        <h1>{{ mount?.label ?? t('comune.carico') }}</h1>
        <p v-if="mount">
          {{ mount.server }}:{{ mount.export_path }}
        </p>
      </div>
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
        <dl class="dettagli">
          <div>
            <dt>{{ t('mount.percorso') }}</dt>
            <dd class="mono">
              {{ mount.mountpoint }}
            </dd>
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
                to="/pubblicazioni"
              >
                {{ t('condivisione.gestisci') }}
              </RouterLink>
            </div>
          </li>
        </ul>

        <div class="azioni">
          <RouterLink
            class="bottone bottone--principale"
            to="/pubblicazioni"
          >
            {{ t('share.nuova') }}
          </RouterLink>
        </div>
      </template>

      <template v-else>
        <GruppoCampi
          :titolo="t('condivisione.zonaPericolosa')"
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
.briciole {
  display: flex;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.875rem;
  color: var(--testo-tenue);
}

.dettagli {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: 0.9rem;
  margin: 0;
}

.dettagli dt {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--testo-tenue);
}

.dettagli dd {
  margin: 0.15rem 0 0;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  word-break: break-all;
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

.stato {
  font-size: 0.8rem;
  color: var(--testo-tenue);
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
