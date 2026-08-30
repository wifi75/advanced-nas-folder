<script setup lang="ts">
/**
 * Trasferimenti, con aggiornamento dal vivo.
 *
 * Cosa questa pagina può dire e cosa no, perché la differenza è ciò che la
 * rende utile invece che ingannevole: sa **quando** un download è stato
 * autorizzato, per quale file e da quale indirizzo; i byte davvero arrivati
 * li scrive il web server nel suo log, e compaiono qui solo se quel log è
 * stato indicato nella configurazione. Finché non ci sono, restano vuoti —
 * una percentuale inventata sarebbe peggio di una assente.
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { seguiTrasferimenti, trasferimentiApi, type Trasferimento } from '@/api/trasferimenti'

const { t, locale } = useI18n()

const elenco = ref<Trasferimento[]>([])
const carico = ref(true)
const errore = ref('')
const collegato = ref(false)

let interruttore: AbortController | null = null

const inCorso = computed(() => elenco.value.filter((t) => t.status === 'in_corso').length)

async function carica(): Promise<void> {
  carico.value = true
  errore.value = ''
  try {
    elenco.value = await trasferimentiApi.elenca(200)
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    carico.value = false
  }
}

/** Inserisce o aggiorna una riga senza ricaricare tutto l'elenco. */
function applica(evento: Record<string, unknown>): void {
  const id = evento.id as number
  const esistente = elenco.value.findIndex((t) => t.id === id)

  const riga: Trasferimento = {
    id,
    kind: evento.tipo as Trasferimento['kind'],
    status: evento.stato as Trasferimento['status'],
    share_id: (evento.share_id as number | null) ?? null,
    user_id: (evento.utente_id as number | null) ?? null,
    path: evento.percorso as string,
    size: (evento.dimensione as number | null) ?? null,
    bytes_transferred: (evento.trasferiti as number | null) ?? null,
    client_ip: (evento.client_ip as string | null) ?? null,
    is_resumed: Boolean(evento.ripresa),
    started_at: evento.iniziato as string,
    finished_at: (evento.concluso as string | null) ?? null,
  }

  if (esistente >= 0) elenco.value[esistente] = riga
  else elenco.value = [riga, ...elenco.value].slice(0, 200)
}

async function ascolta(): Promise<void> {
  interruttore = new AbortController()
  try {
    collegato.value = true
    await seguiTrasferimenti(applica, interruttore.signal)
  } catch {
    // Una connessione caduta non è un guasto da mostrare in rosso: l'elenco
    // resta valido, solo non si aggiorna più da solo.
  } finally {
    collegato.value = false
  }
}

onMounted(async () => {
  await carica()
  void ascolta()
})

onUnmounted(() => interruttore?.abort())

const UNITA = ['B', 'kB', 'MB', 'GB', 'TB'] as const

function dimensione(byte: number | null): string {
  if (byte === null) return '—'
  let valore = byte
  let unita = 0
  while (valore >= 1000 && unita < UNITA.length - 1) {
    valore /= 1000
    unita += 1
  }
  const cifre = unita === 0 || valore >= 100 ? 0 : 1
  return `${valore.toLocaleString(locale.value, { maximumFractionDigits: cifre })} ${UNITA[unita]}`
}

function quando(iso: string): string {
  return new Date(iso).toLocaleString(locale.value, { dateStyle: 'short', timeStyle: 'medium' })
}
</script>

<template>
  <section class="pagina pagina--larga">
    <header class="testa">
      <div>
        <h1>{{ t('trasferimenti.titolo') }}</h1>
        <p class="spiega">
          {{ t('trasferimenti.descrizione') }}
        </p>
      </div>
      <span
        class="stato"
        :class="{ 'stato--vivo': collegato }"
      >
        {{ collegato ? t('trasferimenti.dalVivo') : t('trasferimenti.fermo') }}
      </span>
    </header>

    <p
      v-if="errore"
      class="avviso avviso--errore"
      role="alert"
    >
      {{ errore }}
    </p>

    <p
      v-if="carico"
      class="avviso"
    >
      {{ t('comune.carico') }}
    </p>

    <p
      v-else-if="elenco.length === 0"
      class="avviso"
    >
      {{ t('trasferimenti.nessuno') }}
    </p>

    <template v-else>
      <p class="riepilogo">
        {{ t('trasferimenti.riepilogo', { n: elenco.length, corso: inCorso }) }}
      </p>

      <div class="tabella">
        <table>
          <thead>
            <tr>
              <th>{{ t('trasferimenti.quando') }}</th>
              <th>{{ t('trasferimenti.cosa') }}</th>
              <th>{{ t('trasferimenti.file') }}</th>
              <th class="destra">
                {{ t('trasferimenti.dimensione') }}
              </th>
              <th class="destra">
                {{ t('trasferimenti.trasferiti') }}
              </th>
              <th>{{ t('trasferimenti.da') }}</th>
              <th>{{ t('trasferimenti.stato') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="riga in elenco"
              :key="riga.id"
            >
              <td class="numerica">
                {{ quando(riga.started_at) }}
              </td>
              <td>
                {{ t(`trasferimenti.${riga.kind}`) }}
                <span
                  v-if="riga.is_resumed"
                  class="pastiglia"
                >{{ t('trasferimenti.ripresa') }}</span>
              </td>
              <td class="percorso">
                {{ riga.path }}
              </td>
              <td class="numerica destra">
                {{ dimensione(riga.size) }}
              </td>
              <td class="numerica destra">
                {{ dimensione(riga.bytes_transferred) }}
              </td>
              <td class="numerica">
                {{ riga.client_ip ?? '—' }}
              </td>
              <td>
                <span
                  class="pastiglia"
                  :class="`pastiglia--${riga.status}`"
                >{{ t(`trasferimenti.stato_${riga.status}`) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="nota">
        {{ t('trasferimenti.notaByte') }}
      </p>
    </template>
  </section>
</template>

<style scoped>

.testa {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.testa h1 {
  margin: 0;
  font-size: 1.5rem;
}

.spiega,
.nota,
.avviso,
.riepilogo {
  margin: 0;
  color: var(--testo-tenue);
  font-size: 0.875rem;
}

.avviso--errore {
  color: var(--errore);
}

.stato {
  padding: 0.15rem 0.6rem;
  border: 1px solid var(--bordo);
  border-radius: 999px;
  color: var(--testo-tenue);
  font-size: 0.78rem;
}

.stato--vivo {
  border-color: transparent;
  background: color-mix(in srgb, var(--ok) 20%, transparent);
  color: var(--ok);
}

/* La tabella scorre per conto suo: senza, su schermo stretto sarebbe la
   pagina intera a scorrere di lato. */
.tabella {
  overflow-x: auto;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

th,
td {
  padding: 0.45rem 0.7rem;
  text-align: left;
  white-space: nowrap;
}

th {
  background: var(--superficie-alt);
  color: var(--testo-tenue);
  font-weight: 500;
}

tbody tr:nth-child(even) {
  background: var(--superficie-alt);
}

.destra {
  text-align: right;
}

.numerica {
  font-variant-numeric: tabular-nums;
}

.percorso {
  max-width: 22rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pastiglia {
  padding: 0.05rem 0.4rem;
  border-radius: 999px;
  background: var(--superficie-alt);
  color: var(--testo-tenue);
  font-size: 0.72rem;
}

.pastiglia--completato {
  background: color-mix(in srgb, var(--ok) 20%, transparent);
  color: var(--ok);
}

.pastiglia--in_corso {
  background: color-mix(in srgb, var(--accento) 20%, transparent);
  color: var(--accento);
}

.pastiglia--fallito,
.pastiglia--interrotto {
  background: color-mix(in srgb, var(--errore) 18%, transparent);
  color: var(--errore);
}
</style>
