<script setup lang="ts">
/**
 * Impostazioni del pannello e spazio sui dischi.
 *
 * Lo spazio del disco del pannello sta accanto a quello delle condivisioni di
 * proposito: è quello che ci si dimentica, e se si riempie il pannello smette
 * di funzionare anche con il NAS mezzo vuoto.
 */
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { impostazioniApi, type SpazioDisco } from '@/api/impostazioni'
import { useImpostazioniStore } from '@/stores/impostazioni'

const { t, locale } = useI18n()
const impostazioni = useImpostazioniStore()

const titolo = ref('')
const sottotitolo = ref('')
const logo = ref('')
const nascosti = ref(false)

const dischi = ref<SpazioDisco[]>([])
const pannello = ref<SpazioDisco | null>(null)
const carico = ref(true)
const errore = ref('')
const salvato = ref(false)

onMounted(async () => {
  await impostazioni.carica()
  titolo.value = impostazioni.valori.titolo
  sottotitolo.value = impostazioni.valori.sottotitolo ?? ''
  logo.value = impostazioni.valori.logo_url ?? ''
  nascosti.value = impostazioni.valori.mostra_nascosti

  try {
    dischi.value = await impostazioniApi.spazio()
    pannello.value = await impostazioniApi.spazioPannello()
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    carico.value = false
  }
})

async function salva(): Promise<void> {
  errore.value = ''
  salvato.value = false
  try {
    await impostazioni.salva({
      titolo: titolo.value,
      sottotitolo: sottotitolo.value,
      logo_url: logo.value,
      mostra_nascosti: nascosti.value,
    })
    salvato.value = true
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  }
}

const UNITA = ['B', 'kB', 'MB', 'GB', 'TB'] as const

function dimensione(byte: number | null): string {
  if (byte === null) return '—'
  let valore = byte
  let unita = 0
  while (valore >= 1000 && unita < UNITA.length - 1) {
    valore /= 1000
    unita += 1
  }
  return `${valore.toLocaleString(locale.value, { maximumFractionDigits: 1 })} ${UNITA[unita]}`
}

function usato(disco: SpazioDisco): number | null {
  if (disco.totale === null || disco.libero === null || disco.totale === 0) return null
  return Math.round(((disco.totale - disco.libero) / disco.totale) * 100)
}
</script>

<template>
  <section class="pagina">
    <header>
      <h1>{{ t('impostazioni.titolo') }}</h1>
      <p class="spiega">
        {{ t('impostazioni.descrizione') }}
      </p>
    </header>

    <p
      v-if="errore"
      class="avviso avviso--errore"
      role="alert"
    >
      {{ errore }}
    </p>

    <form
      class="blocco"
      @submit.prevent="salva"
    >
      <h2>{{ t('impostazioni.marchio') }}</h2>

      <label class="campo">
        {{ t('impostazioni.nome') }}
        <input
          v-model="titolo"
          type="text"
        >
      </label>

      <label class="campo">
        {{ t('impostazioni.sottotitolo') }}
        <input
          v-model="sottotitolo"
          type="text"
        >
      </label>

      <label class="campo">
        {{ t('impostazioni.logo') }}
        <input
          v-model="logo"
          type="text"
          placeholder="/pannello/logo.png"
        >
        <span class="nota">{{ t('impostazioni.logoNota') }}</span>
      </label>

      <label class="interruttore">
        <input
          v-model="nascosti"
          type="checkbox"
        >
        {{ t('impostazioni.nascosti') }}
      </label>
      <p class="nota">
        {{ t('impostazioni.nascostiNota') }}
      </p>

      <div class="azioni">
        <button
          class="bottone bottone--principale"
          type="submit"
        >
          {{ t('comune.salva') }}
        </button>
        <span
          v-if="salvato"
          class="fatto"
          role="status"
        >{{ t('impostazioni.salvato') }}</span>
      </div>
    </form>

    <section class="blocco">
      <h2>{{ t('impostazioni.spazio') }}</h2>

      <p
        v-if="carico"
        class="avviso"
      >
        {{ t('comune.carico') }}
      </p>

      <ul
        v-else
        class="dischi"
      >
        <li
          v-for="d in [...(pannello ? [pannello] : []), ...dischi]"
          :key="d.mountpoint"
          class="disco"
        >
          <div class="disco__testa">
            <span class="disco__nome">{{
              d.mount_id === null ? t('impostazioni.discoPannello') : d.label
            }}</span>
            <span class="disco__numeri">
              <template v-if="d.libero !== null">
                {{ t('impostazioni.liberi', { libero: dimensione(d.libero) }) }}
                / {{ dimensione(d.totale) }}
              </template>
              <template v-else>{{ t('impostazioni.nonRaggiungibile') }}</template>
            </span>
          </div>

          <div
            v-if="usato(d) !== null"
            class="barra"
            role="progressbar"
            :aria-valuenow="usato(d) ?? 0"
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div
              class="barra__pieno"
              :class="{ 'barra__pieno--pieno': (usato(d) ?? 0) >= 90 }"
              :style="{ width: `${usato(d)}%` }"
            />
          </div>

          <span class="disco__percorso">{{ d.mountpoint }}</span>
        </li>
      </ul>
    </section>
  </section>
</template>

<style scoped>

h1 {
  margin: 0;
  font-size: 1.5rem;
}

h2 {
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

.blocco {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  padding: 1rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--superficie);
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.875rem;
}

.campo input {
  padding: 0.55rem 0.7rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--sfondo);
  color: var(--testo);
  font: inherit;
}

.interruttore {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.875rem;
}

.azioni {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}


.fatto {
  color: var(--ok);
  font-size: 0.85rem;
}

.dischi {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.disco {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.disco__testa {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.disco__nome {
  font-size: 0.9rem;
  font-weight: 500;
}

.disco__numeri {
  color: var(--testo-tenue);
  font-size: 0.82rem;
  font-variant-numeric: tabular-nums;
}

.disco__percorso {
  color: var(--testo-tenue);
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
}

.barra {
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--superficie-alt);
}

.barra__pieno {
  height: 100%;
  background: var(--accento);
}

/* Sopra il 90% il colore cambia: è la soglia oltre la quale un caricamento
   può fallire a metà, e va vista prima che succeda. */
.barra__pieno--pieno {
  background: var(--errore);
}
</style>
