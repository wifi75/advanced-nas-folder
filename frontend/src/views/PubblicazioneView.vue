<script setup lang="ts">
/**
 * Una cartella pubblicata, con tutto quello che la riguarda.
 *
 * Ha un indirizzo proprio perché è raggiungibile dall'albero del menu: cliccare
 * una cartella lì dentro deve portare a una pagina, non aprire un pannello che
 * sparisce al primo aggiornamento.
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import type { Visibilita } from '@/api/shares'
import DettaglioShare from '@/components/DettaglioShare.vue'
import GruppoCampi from '@/components/GruppoCampi.vue'
import IndirizziPubblicazione from '@/components/IndirizziPubblicazione.vue'
import Schede from '@/components/Schede.vue'
import { useMountsStore } from '@/stores/mounts'
import { useSharesStore } from '@/stores/shares'

const route = useRoute()
const router = useRouter()
const shares = useSharesStore()
const mounts = useMountsStore()
const { t } = useI18n()

const VISIBILITA: Visibilita[] = ['pubblica', 'password', 'utenti', 'utenti_scelti', 'negata']

const id = computed(() => Number(route.params.id))
const share = computed(() => shares.elenco.find((s) => s.id === id.value))
const origine = computed(() => mounts.elenco.find((m) => m.id === share.value?.mount_id))

const schede = computed(() => [
  { chiave: 'indirizzo', etichetta: t('pubblicazione.indirizzo') },
  { chiave: 'accesso', etichetta: t('pubblicazione.accesso') },
  { chiave: 'contenuto', etichetta: t('pubblicazione.contenuto') },
])

const form = ref({
  slug: '',
  label: '',
  description: null as string | null,
  mount_id: 0,
  subpath: '',
  hidden_patterns: '',
  default_visibility: 'utenti' as Visibilita,
})
const salvato = ref(false)

function ricarica(): void {
  const s = share.value
  if (!s) return
  form.value = {
    slug: s.slug,
    label: s.label,
    description: s.description,
    mount_id: s.mount_id,
    subpath: s.subpath ?? '',
    hidden_patterns: s.hidden_patterns ?? '',
    default_visibility: s.default_visibility,
  }
}

watch(share, ricarica, { immediate: true })

onMounted(async () => {
  if (shares.elenco.length === 0) await shares.carica()
  if (mounts.elenco.length === 0) await mounts.carica()
})

const nomeCambiato = computed(() => share.value !== undefined && form.value.slug !== share.value.slug)

const origineCambiata = computed(
  () =>
    share.value !== undefined &&
    (form.value.mount_id !== share.value.mount_id ||
      form.value.subpath !== (share.value.subpath ?? '')),
)

async function salva(): Promise<void> {
  salvato.value = false
  if (await shares.modifica(id.value, form.value)) salvato.value = true
}

const daEliminare = ref(false)

async function elimina(): Promise<void> {
  if (await shares.elimina(id.value)) await router.push('/condivisioni')
}
</script>

<template>
  <div class="pagina">
    <p class="briciole">
      <RouterLink
        v-if="origine"
        :to="`/condivisioni/${origine.id}`"
      >
        {{ origine.label }}
      </RouterLink>
      <span aria-hidden="true">&rsaquo;</span>
      <span>{{ share?.label ?? '...' }}</span>
    </p>

    <!-- L'unico riquadro della pagina: identita', indirizzo e sottomenu. Sono
         le cose che si guardano sempre, e tenerle insieme evita di disegnare un
         secondo riquadro piu' sotto per il solo indirizzo. -->
    <header
      class="testata-tinta"
      :style="{ '--tinta': 'var(--tinta-pubblicazioni)' }"
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
            <path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z M3 12h18 M12 3c2.5 2.7 2.5 15.3 0 18 M12 3c-2.5 2.7-2.5 15.3 0 18" />
          </svg>
        </span>
        <h1>{{ share?.label ?? t('comune.carico') }}</h1>
        <span
          v-if="share"
          class="etichetta-visibilita"
        >{{ t(`visibilita.breve_${share.default_visibility}`) }}</span>
        <span
          v-if="share && !share.is_enabled"
          class="spenta"
        >{{ t('share.disattivata') }}</span>
      </div>

      <IndirizziPubblicazione
        v-if="share"
        :slug="share.slug"
        nudo
      />
    </header>

    <p
      v-if="shares.errore"
      class="errore"
      role="alert"
    >
      {{ shares.errore }}
    </p>

    <Schede
      v-if="share"
      v-slot="{ attiva }"
      :schede="schede"
    >
      <!-- indirizzo e identità -->
      <template v-if="attiva === 'indirizzo'">
        <GruppoCampi
          :titolo="t('share.gruppoNome')"
          tinta="var(--tinta-pubblicazioni)"
          icona="M3 7a2 2 0 0 1 2-2h6l9 9-8 8-9-9Z M7.5 9.5h.01"
          :descrizione="t('share.gruppoNomeAiuto')"
        >
          <label class="campo">
            <span>{{ t('share.nome') }}</span>
            <input
              v-model="form.label"
              type="text"
              maxlength="128"
            >
          </label>
          <label class="campo">
            <span>{{ t('share.identificatore') }}</span>
            <input
              v-model="form.slug"
              type="text"
              maxlength="63"
            >
            <small
              v-if="nomeCambiato"
              class="aiuto aiuto--attenzione"
            >{{ t('share.identificatoreAvviso') }}</small>
          </label>
          <label class="campo">
            <span>{{ t('share.descrizione') }}</span>
            <input
              v-model="form.description"
              type="text"
            >
          </label>
        </GruppoCampi>

        <GruppoCampi
          :titolo="t('share.gruppoCosa')"
          tinta="var(--tinta-nfs)"
          icona="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z M12 11v3 M9 17h6"
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
          <p
            v-if="origineCambiata"
            class="aiuto aiuto--attenzione"
          >
            {{ t('share.origineAvviso') }}
          </p>
        </GruppoCampi>

        <div class="azioni">
          <button
            type="button"
            class="bottone bottone--principale"
            :disabled="!form.label || !form.slug"
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

      <!-- chi accede -->
      <template v-else-if="attiva === 'accesso'">
        <GruppoCampi
          :titolo="t('share.gruppoAccesso')"
          tinta="var(--tinta-utenti)"
          icona="M15 7a4 4 0 1 1-3.9 5H7v3H4v-3l3.1-3H11a4 4 0 0 1 4-2Z"
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
          <label class="campo interruttore">
            <input
              :checked="share.is_enabled"
              type="checkbox"
              @change="shares.modifica(share.id, { is_enabled: !share.is_enabled })"
            >
            <span>{{ t('share.attiva') }}</span>
          </label>
          <div class="azioni">
            <button
              type="button"
              class="bottone bottone--principale"
              @click="salva"
            >
              {{ t('comune.salva') }}
            </button>
          </div>
        </GruppoCampi>

        <DettaglioShare :id="share.id" />
      </template>

      <!-- contenuto -->
      <template v-else>
        <GruppoCampi
          :titolo="t('share.gruppoNascosti')"
          tinta="var(--tinta-file)"
          icona="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6Z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
          :descrizione="t('share.gruppoNascostiAiuto')"
        >
          <label class="campo">
            <span>{{ t('share.nascosti') }}</span>
            <textarea
              v-model="form.hidden_patterns"
              rows="6"
              spellcheck="false"
              class="elenco-nascosti"
            />
          </label>
          <div class="azioni">
            <button
              type="button"
              class="bottone bottone--principale"
              @click="salva"
            >
              {{ t('comune.salva') }}
            </button>
            <RouterLink
              class="bottone"
              :to="`/archivio/${share.slug}`"
            >
              {{ t('archivio.apri') }}
            </RouterLink>
          </div>
        </GruppoCampi>

        <GruppoCampi
          :titolo="t('condivisione.zonaPericolosa')"
          tinta="var(--errore)"
          icona="M4 7h16 M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2 M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13"
          :descrizione="t('pubblicazione.rimozioneAiuto')"
        >
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
        <h2>{{ t('share.confermaTitolo', { nome: share?.label ?? '' }) }}</h2>
        <p>{{ t('pubblicazione.rimozioneAiuto') }}</p>
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
.etichetta-visibilita {
  margin-left: auto;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--tinta-pubblicazioni) 45%, transparent);
  background: var(--superficie);
  font-size: 0.8rem;
  color: var(--tinta-pubblicazioni);
  white-space: nowrap;
}

.briciole {
  display: flex;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.875rem;
  color: var(--testo-tenue);
}

.spenta {
  font-size: 0.8rem;
  color: var(--attenzione);
}

.elenco-nascosti {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.82rem;
  resize: vertical;
}

.aiuto {
  color: var(--testo-tenue);
  font-size: 0.78rem;
}

.aiuto--attenzione {
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
