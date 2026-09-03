<script setup lang="ts">
/**
 * Montaggi NFS già presenti in `/etc/fstab`, da far gestire al pannello.
 *
 * Serve a chi installa il pannello su una macchina che i mount ce li ha già:
 * ricopiarli a mano significa riscrivere server, percorsi e opzioni senza
 * sbagliare, e poi accorgersi di aver dimenticato una riga.
 *
 * L'importazione e la disattivazione della riga in fstab sono **due azioni
 * separate**, e in quest'ordine: finché entrambe sono attive il sistema prova
 * a montare due volte lo stesso percorso, ma disattivare prima di aver
 * verificato che il mount del pannello funzioni lascerebbe la cartella
 * irraggiungibile.
 */
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import { mountsApi, type MontaggioPreesistente } from '@/api/mounts'

const emit = defineEmits<{ importato: [] }>()

const { t } = useI18n()

const trovati = ref<MontaggioPreesistente[]>([])
const carico = ref(true)
const errore = ref('')
const avviso = ref('')
const inCorso = ref<string | null>(null)
const importati = ref<Set<string>>(new Set())

async function carica(): Promise<void> {
  carico.value = true
  errore.value = ''
  avviso.value = ''
  try {
    trovati.value = await mountsApi.preesistenti()
  } catch (e) {
    // L'agent gira solo su Linux: altrove non c'è nulla da leggere, e non è
    // un guasto da mostrare in rosso.
    if (e instanceof ApiError && e.status === 503) avviso.value = t('fstab.nonDisponibile')
    else errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    carico.value = false
  }
}

onMounted(carica)

/** Legge dalle opzioni di fstab la versione NFS, che il pannello deve conoscere. */
function versione(opzioni: string, tipo: string): string {
  const trovata = /(?:vers|nfsvers)=([0-9.]+)/.exec(opzioni)
  if (trovata) return trovata[1]!
  return tipo === 'nfs4' ? '4.1' : '3'
}

function soloLettura(opzioni: string): boolean {
  return opzioni.split(',').includes('ro')
}

async function importa(voce: MontaggioPreesistente): Promise<void> {
  inCorso.value = voce.mountpoint
  errore.value = ''
  try {
    await mountsApi.crea({
      slug: voce.slug_proposto,
      label: voce.export.split('/').pop() || voce.slug_proposto,
      server: voce.server,
      export_path: voce.export,
      nfs_version: versione(voce.opzioni, voce.tipo),
      automount: true,
      idle_timeout: 600,
      // Si importa in sola lettura se lo era, ma anche se non lo era: la
      // scrittura si concede di proposito, non per eredità.
      consenti_scrittura: false,
    })
    importati.value = new Set(importati.value).add(voce.mountpoint)
    await carica()
    emit('importato')
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    inCorso.value = null
  }
}

async function disattiva(voce: MontaggioPreesistente): Promise<void> {
  inCorso.value = voce.mountpoint
  errore.value = ''
  try {
    const esito = await mountsApi.disattivaFstab(voce.mountpoint)
    avviso.value = t('fstab.disattivata', { copia: esito.copia })
    await carica()
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    inCorso.value = null
  }
}
</script>

<template>
  <section
    v-if="carico || trovati.length || errore || avviso"
    class="blocco"
  >
    <h2>{{ t('fstab.titolo') }}</h2>
    <p class="spiega">
      {{ t('fstab.descrizione') }}
    </p>

    <p
      v-if="errore"
      class="avviso avviso--errore"
      role="alert"
    >
      {{ errore }}
    </p>

    <p
      v-else-if="avviso"
      class="avviso"
    >
      {{ avviso }}
    </p>

    <p
      v-if="carico"
      class="avviso"
    >
      {{ t('comune.carico') }}
    </p>

    <ul
      v-else-if="trovati.length"
      class="elenco"
    >
      <li
        v-for="v in trovati"
        :key="v.mountpoint"
        class="voce"
      >
        <div class="riga">
          <span class="origine">{{ v.server }}:{{ v.export }}</span>
          <span class="freccia">→</span>
          <span class="punto">{{ v.mountpoint }}</span>
          <span
            v-if="soloLettura(v.opzioni)"
            class="etichetta"
          >{{ t('fstab.solaLettura') }}</span>
          <span class="etichetta">NFS {{ versione(v.opzioni, v.tipo) }}</span>
        </div>

        <div class="azioni">
          <button
            v-if="!v.gia_gestito"
            class="bottone bottone--principale"
            type="button"
            :disabled="inCorso === v.mountpoint"
            @click="importa(v)"
          >
            {{ t('fstab.importa') }}
          </button>
          <template v-else>
            <span class="etichetta etichetta--ok">{{ t('fstab.giaGestito') }}</span>
            <button
              type="button"
              class="bottone bottone--tenue"
              :disabled="inCorso === v.mountpoint"
              @click="disattiva(v)"
            >
              {{ t('fstab.disattiva') }}
            </button>
          </template>
        </div>

        <p
          v-if="v.gia_gestito"
          class="nota"
        >
          {{ t('fstab.notaDisattiva') }}
        </p>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.blocco {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--superficie);
}

.blocco h2 {
  margin: 0;
  font-size: 1rem;
}

.spiega,
.nota,
.avviso {
  margin: 0;
  color: var(--testo-tenue);
  font-size: 0.85rem;
}

.avviso--errore {
  color: var(--errore);
}

.elenco {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.voce {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding-top: 0.6rem;
  border-top: 1px solid var(--bordo);
}

.riga {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.origine,
.punto {
  font-family: var(--font-mono);
  font-size: 0.8rem;
}

.freccia {
  color: var(--testo-tenue);
}

.etichetta {
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: var(--superficie-alt);
  color: var(--testo-tenue);
  font-size: 0.72rem;
}

.etichetta--ok {
  background: color-mix(in srgb, var(--ok) 20%, transparent);
  color: var(--ok);
}

.azioni {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}



</style>
