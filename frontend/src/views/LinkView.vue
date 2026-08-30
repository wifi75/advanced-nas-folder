<script setup lang="ts">
/**
 * Cartella aperta da un link di condivisione.
 *
 * Chi arriva qui non ha un account e non lo avrà: il token nell'indirizzo è
 * l'autorizzazione. La vista è deliberatamente spoglia — niente menu, niente
 * accesso al pannello — perché mostra soltanto il ramo che il link concede.
 */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { linkApi, indirizzoDownloadLink, type Contenuto, type Voce } from '@/api/archivio'
import { ApiError } from '@/api/client'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()

const contenuto = ref<Contenuto | null>(null)
const errore = ref<string | null>(null)
const chiedePassword = ref(false)
const password = ref('')
const carico = ref(false)

const token = computed(() => String(route.params.token ?? ''))
const percorso = computed(() => {
  const parti = route.params.percorso
  return Array.isArray(parti) ? parti.join('/') : String(parti ?? '')
})

async function carica(): Promise<void> {
  carico.value = true
  errore.value = null
  try {
    contenuto.value = await linkApi.contenuto(
      token.value,
      percorso.value,
      password.value || undefined,
    )
    chiedePassword.value = false
  } catch (e) {
    contenuto.value = null
    // 401 significa esattamente «serve la password»; qualunque altro errore no.
    chiedePassword.value = e instanceof ApiError && e.status === 401
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    carico.value = false
  }
}

watch([token, percorso], carica, { immediate: true })

function vaiA(p: string): void {
  const coda = p ? `/${p.split('/').map(encodeURIComponent).join('/')}` : ''
  router.push(`/l/${token.value}${coda}`)
}

function apri(voce: Voce): void {
  vaiA(voce.percorso)
}

function scarica(voce: Voce): void {
  window.location.href = indirizzoDownloadLink(
    token.value,
    voce.percorso,
    password.value || undefined,
  )
}

const UNITA = ['B', 'kB', 'MB', 'GB', 'TB'] as const

function dimensione(byte: number | null): string {
  if (byte === null) return ''
  let valore = byte
  let unita = 0
  while (valore >= 1000 && unita < UNITA.length - 1) {
    valore /= 1000
    unita += 1
  }
  const cifre = unita === 0 || valore >= 100 ? 0 : 1
  return `${valore.toLocaleString(locale.value, { maximumFractionDigits: cifre })} ${UNITA[unita]}`
}
</script>

<template>
  <section class="link">
    <header class="intestazione">
      <h1 class="titolo">
        {{ contenuto?.label ?? t('link.titolo') }}
      </h1>

      <nav
        v-if="contenuto && contenuto.briciole.length"
        class="briciole"
        :aria-label="t('archivio.percorso')"
      >
        <button
          type="button"
          class="briciola"
          @click="vaiA('')"
        >
          {{ t('archivio.radice') }}
        </button>
        <template
          v-for="[nome, p] in contenuto.briciole"
          :key="p"
        >
          <span
            class="briciole__separatore"
            aria-hidden="true"
          >/</span>
          <button
            type="button"
            class="briciola"
            @click="vaiA(p)"
          >
            {{ nome }}
          </button>
        </template>
      </nav>
    </header>

    <form
      v-if="chiedePassword"
      class="password"
      @submit.prevent="carica"
    >
      <label
        class="password__etichetta"
        for="anf-password-link"
      >{{ t('link.passwordRichiesta') }}</label>
      <div class="password__riga">
        <input
          id="anf-password-link"
          v-model="password"
          type="password"
          class="campo"
          autocomplete="current-password"
        >
        <button
          type="submit"
          class="bottone"
          :disabled="password === ''"
        >
          {{ t('archivio.sblocca') }}
        </button>
      </div>
    </form>

    <p
      v-if="errore && !carico && !chiedePassword"
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
      v-else-if="contenuto && contenuto.voci.length === 0"
      class="avviso"
    >
      {{ t('archivio.vuota') }}
    </p>

    <ul
      v-else-if="contenuto"
      class="voci"
    >
      <li
        v-for="voce in contenuto.voci"
        :key="voce.percorso"
        class="voce"
      >
        <button
          v-if="voce.cartella"
          type="button"
          class="voce__apri"
          @click="apri(voce)"
        >
          <span class="voce__nome">{{ voce.nome }}</span>
        </button>
        <span
          v-else
          class="voce__nome"
        >{{ voce.nome }}</span>

        <span class="voce__dimensione">{{ dimensione(voce.dimensione) }}</span>

        <button
          v-if="!voce.cartella"
          type="button"
          class="bottone bottone--tenue"
          @click="scarica(voce)"
        >
          {{ t('archivio.scarica') }}
        </button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.link {
  display: flex;
  flex: 1;
  flex-direction: column;
  width: min(680px, 100% - 2.5rem);
  margin-inline: auto;
  gap: 1.25rem;
  padding-block: 2rem;
}

.intestazione {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.titolo {
  margin: 0;
  font-size: 1.5rem;
}

.briciole {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.briciola {
  padding: 0.15rem 0.35rem;
  border: 0;
  border-radius: var(--raggio);
  background: none;
  color: var(--tinta-link);
  cursor: pointer;
  font: inherit;
}

.briciole__separatore {
  color: var(--testo-tenue);
}

.voci {
  display: flex;
  flex-direction: column;
  gap: 1px;
  margin: 0;
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--bordo);
  list-style: none;
}

.voce {
  display: grid;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 0.85rem;
  background: var(--superficie);
  grid-template-columns: minmax(0, 1fr) 5.5rem auto;
}

.voce__apri {
  min-width: 0;
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  cursor: pointer;
  font: inherit;
  text-align: left;
}

.voce__apri:hover .voce__nome {
  text-decoration: underline;
}

.voce__nome {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voce__dimensione {
  color: var(--testo-tenue);
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.campo {
  flex: 1;
  min-width: 0;
  padding: 0.55rem 0.7rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--sfondo);
  color: var(--testo);
  font: inherit;
}




.password {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-width: 24rem;
}

.password__riga {
  display: flex;
  gap: 0.5rem;
}

.password__etichetta {
  color: var(--testo-tenue);
  font-size: 0.9rem;
}

.avviso {
  margin: 0;
  color: var(--testo-tenue);
}

.avviso--errore {
  color: var(--tinta-link);
}
</style>
