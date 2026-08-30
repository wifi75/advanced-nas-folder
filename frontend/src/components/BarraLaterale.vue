<script setup lang="ts">
/**
 * Navigazione principale, raggruppata per categoria.
 *
 * Le voci non sono un elenco unico: ogni categoria risponde a una domanda
 * diversa — cosa pubblico, chi può accedere, come sta il sistema — e tenerle
 * separate è ciò che rende il menu leggibile quando le voci cresceranno.
 *
 * Non ci sono piu' voci disattivate «in arrivo»: annunciavano come future
 * funzioni che nel frattempo erano state realizzate, ed erano la prima cosa
 * che si leggeva aprendo il menu. Una voce che non porta da nessuna parte e'
 * peggio di una voce assente.
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'

import SelettoreLingua from '@/components/SelettoreLingua.vue'
import SelettoreTema from '@/components/SelettoreTema.vue'
import { sharesApi, type Share } from '@/api/shares'
import { useAppStore } from '@/stores/app'
import { useMountsStore } from '@/stores/mounts'
import { useSharesStore } from '@/stores/shares'
import { useImpostazioniStore } from '@/stores/impostazioni'
import { useAuthStore } from '@/stores/auth'

interface Voce {
  etichetta: string
  a: string
  tinta: string
  icona: string
}

interface Categoria {
  titolo: string
  voci: Voce[]
}

defineProps<{ aperta?: boolean }>()
const emit = defineEmits<{ naviga: []; esci: [] }>()

const app = useAppStore()
const impostazioni = useImpostazioniStore()
const auth = useAuthStore()
const shares = useSharesStore()
const mounts = useMountsStore()
const route = useRoute()

// L'archivio si apre sempre su una pubblicazione: se non ce ne sono, la voce
// porta all'elenco delle pubblicazioni, che e' il posto da cui si comincia.
/**
 * L'albero delle condivisioni: ognuna con sotto le proprie cartelle pubblicate.
 *
 * E' la struttura vera del sistema — una cartella pubblicata nasce sempre da
 * una condivisione — e mostrarla nel menu evita di doverla ricostruire a mente
 * saltando fra due elenchi separati.
 */
// La barra carica i propri dati invece di aspettare che lo faccia una pagina:
// nell'archivio nessuno lo faceva, e l'albero delle condivisioni compariva
// vuoto proprio dove serve di piu' per tornare indietro.
onMounted(() => {
  if (auth.utente?.is_admin) {
    if (mounts.elenco.length === 0) void mounts.carica()
    if (shares.elenco.length === 0) void shares.carica()
    return
  }
  // Chi non amministra non puo' chiedere l'elenco completo — l'API glielo
  // rifiuta — ma un menu vuoto sarebbe peggio: non gli direbbe come arrivare
  // alle cartelle a cui ha diritto. Si chiedono quelle, e solo quelle.
  void caricaLeMie()
})

/** Le pubblicazioni raggiungibili da chi non e' amministratore. */
const leMie = ref<Share[]>([])

async function caricaLeMie(): Promise<void> {
  try {
    leMie.value = await sharesApi.mie()
  } catch {
    leMie.value = []
  }
}

const albero = computed(() =>
  mounts.elenco.map((m) => ({
    mount: m,
    pubblicazioni: shares.elenco.filter((s) => s.mount_id === m.id),
  })),
)

/** Se la voce aperta appartiene a questa condivisione, i figli si vedono. */
function espansa(idMount: number): boolean {
  if (route.path === `/condivisioni/${idMount}`) return true
  const pubblicata = shares.elenco.find((s) => route.path === `/pubblicazioni/${s.id}`)
  return pubblicata?.mount_id === idMount
}
const { t } = useI18n()

// Tracciati delle icone: linee semplici, disegnate sulla stessa griglia 24×24
// così hanno tutte lo stesso peso ottico.
const ICONE = {
  cartellaRete: 'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z M12 11v3 M9 17h6',
  // Una cartella, non un mappamondo: nel menu di chi non amministra queste
  // voci sono cartelle, e il globo suggeriva un indirizzo pubblico.
  cartella: 'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z',
  globo: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z M3 12h18 M12 3c2.5 2.7 2.5 15.3 0 18 M12 3c-2.5 2.7-2.5 15.3 0 18',
  documento: 'M6 3h7l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z M13 3v5h5 M8 13h8 M8 17h5',
  persone: 'M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z M2.5 20a6.5 6.5 0 0 1 13 0 M17 11.5a3 3 0 1 0 0-6 M17.5 14.2a6 6 0 0 1 4 5.8',
  catena: 'M10 13.5a4 4 0 0 0 5.7 0l2.8-2.8a4 4 0 0 0-5.7-5.7L11.5 6.3 M14 10.5a4 4 0 0 0-5.7 0l-2.8 2.8a4 4 0 0 0 5.7 5.7l1.3-1.3',
  battito: 'M3 12h4l2.5-6 4 12 2.5-6h5',
  frecce: 'M7 4v13 M7 17l-3-3 M7 17l3-3 M17 20V7 M17 7l-3 3 M17 7l3 3',
  ingranaggio:
    'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z M19.4 14.5a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.1a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-2.9-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.1-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 2.9-1.2V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 2.9 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.1a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1.2Z',
} as const

// Tutte queste pagine sono riservate all'amministratore: l'API le rifiuta a
// chiunque altro. Mostrarle a un utente normale non gli da' un permesso in
// piu', gli da' solo cinque modi di sbattere contro un errore.
const categorie = computed<Categoria[]>(() =>
  !auth.utente?.is_admin
    ? []
    : [
  {
    titolo: t('menu.accessi'),
    voci: [
      {
        etichetta: t('menu.utenti'),
        a: '/utenti',
        tinta: 'var(--tinta-utenti)',
        icona: ICONE.persone,
      },
    ],
  },
  {
    titolo: t('menu.sistema'),
    voci: [
      { etichetta: t('menu.stato'), a: '/', tinta: 'var(--tinta-stato)', icona: ICONE.battito },
      {
        etichetta: t('menu.webserver'),
        a: '/webserver',
        tinta: 'var(--tinta-webserver)',
        icona: ICONE.globo,
      },
      {
        etichetta: t('menu.trasferimenti'),
        a: '/trasferimenti',
        tinta: 'var(--tinta-trasferimenti)',
        icona: ICONE.frecce,
      },
      {
        etichetta: t('menu.impostazioni'),
        a: '/impostazioni',
        tinta: 'var(--tinta-impostazioni)',
        icona: ICONE.ingranaggio,
      },
    ],
  },
      ],
)
</script>

<template>
  <aside
    class="barra"
    :class="{ 'barra--aperta': aperta }"
  >
    <div class="marchio">
      <img
        v-if="impostazioni.valori.logo_url"
        :src="impostazioni.valori.logo_url"
        :alt="impostazioni.valori.titolo"
        class="marchio__logo"
      >
      <span
        v-else
        class="marchio__nome"
      >{{ impostazioni.valori.titolo }}</span>
      <span
        v-if="impostazioni.valori.sottotitolo"
        class="marchio__sottotitolo"
      >{{ impostazioni.valori.sottotitolo }}</span>
      <span class="marchio__versione">v{{ app.version }}</span>
    </div>

    <nav class="menu">
      <!-- Chi non amministra vede solo le proprie cartelle: e' tutto cio' che
           il pannello ha da offrirgli, e senza questo elenco non avrebbe alcun
           modo di raggiungerle se non conoscendone l'indirizzo a memoria. -->
      <section
        v-if="!auth.utente?.is_admin"
        class="categoria"
      >
        <h2 class="categoria__titolo">
          {{ t('menu.leMieCartelle') }}
        </h2>
        <ul
          v-if="leMie.length"
          class="voci"
        >
          <li
            v-for="s in leMie"
            :key="s.id"
          >
            <RouterLink
              :to="`/archivio/${s.slug}`"
              class="voce"
              @click="emit('naviga')"
            >
              <span
                class="pastiglia"
                :style="{ '--tinta': 'var(--tinta-file)' }"
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
                  <path :d="ICONE.cartella" />
                </svg>
              </span>
              <span class="voce__testo">{{ s.label }}</span>
            </RouterLink>
          </li>
        </ul>
        <p
          v-else
          class="niente"
        >
          {{ t('menu.nessunaMiaCartella') }}
        </p>
      </section>

      <section
        v-if="auth.utente?.is_admin"
        class="categoria"
      >
        <h2 class="categoria__titolo">
          {{ t('menu.condivisioni') }}
        </h2>
        <ul class="voci">
          <li
            v-for="ramo in albero"
            :key="ramo.mount.id"
          >
            <RouterLink
              class="voce"
              :to="`/condivisioni/${ramo.mount.id}`"
              @click="emit('naviga')"
            >
              <span
                class="pastiglia"
                :style="{ '--tinta': 'var(--tinta-nfs)' }"
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
                  <path :d="ICONE.cartellaRete" />
                </svg>
              </span>
              <span class="voce__testo">{{ ramo.mount.label }}</span>
            </RouterLink>

            <!-- I figli compaiono solo per la condivisione aperta: mostrarli
                 tutti sempre allungherebbe il menu oltre lo schermo appena le
                 condivisioni diventano qualcuna in piu'. -->
            <ul
              v-if="espansa(ramo.mount.id)"
              class="voci voci--figlie"
            >
              <li
                v-for="p in ramo.pubblicazioni"
                :key="p.id"
              >
                <RouterLink
                  class="voce voce--figlia"
                  :to="`/pubblicazioni/${p.id}`"
                  @click="emit('naviga')"
                >
                  <span class="punto" />
                  <span class="voce__testo">{{ p.label }}</span>
                </RouterLink>
              </li>
              <li>
                <RouterLink
                  class="voce voce--figlia voce--aggiungi"
                  :to="`/pubblicazioni?nuova=${ramo.mount.id}`"
                  @click="emit('naviga')"
                >
                  <span class="punto punto--vuoto" />
                  <span class="voce__testo">{{ t('menu.pubblica') }}</span>
                </RouterLink>
              </li>
            </ul>
          </li>

          <!-- L'elenco di tutte le cartelle pubblicate, di qualunque
               condivisione: nell'albero si vedono solo quelle della
               condivisione aperta, e senza questa voce la pagina non era
               raggiungibile da nessuna parte. -->
          <li>
            <RouterLink
              class="voce"
              to="/pubblicazioni"
              @click="emit('naviga')"
            >
              <span
                class="pastiglia"
                :style="{ '--tinta': 'var(--tinta-pubblicazioni)' }"
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
                  <path :d="ICONE.globo" />
                </svg>
              </span>
              <span class="voce__testo">{{ t('menu.tuttePubblicazioni') }}</span>
            </RouterLink>
          </li>

          <li>
            <RouterLink
              class="voce voce--aggiungi"
              to="/condivisioni"
              @click="emit('naviga')"
            >
              <span
                class="pastiglia pastiglia--vuota"
                aria-hidden="true"
              />
              <span class="voce__testo">{{ t('menu.tutteCondivisioni') }}</span>
            </RouterLink>
          </li>
        </ul>
      </section>

      <section
        v-for="c in categorie"
        :key="c.titolo"
        class="categoria"
      >
        <h2 class="categoria__titolo">
          {{ c.titolo }}
        </h2>
        <ul class="voci">
          <li
            v-for="v in c.voci"
            :key="v.etichetta"
          >
            <RouterLink
              :to="v.a"
              class="voce"
              @click="emit('naviga')"
            >
              <span
                class="pastiglia"
                :style="{ '--tinta': v.tinta }"
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
                  <path :d="v.icona" />
                </svg>
              </span>
              <span class="voce__testo">{{ v.etichetta }}</span>
            </RouterLink>
          </li>
        </ul>
      </section>
    </nav>

    <div class="fondo">
      <SelettoreTema />
      <SelettoreLingua />

      <div
        v-if="auth.utente"
        class="piede"
      >
        <span class="piede__utente">
          {{ auth.utente.username }}
          <em v-if="auth.utente.is_admin">{{ t('comune.amministratore') }}</em>
        </span>
        <button
          type="button"
          class="esci"
          @click="emit('esci')"
        >
          {{ t('comune.esci') }}
        </button>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.marchio__logo {
  max-width: 100%;
  max-height: 2.2rem;
  object-fit: contain;
}

.marchio__sottotitolo {
  color: var(--testo-tenue);
  font-size: 0.72rem;
}

.barra {
  flex: none;
  inline-size: 264px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.25rem 0.9rem;
  background: var(--barra-fondo);
  border-inline-end: 1px solid var(--bordo);
  overflow-y: auto;
}

/* --- marchio --- */

.marchio {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding-inline: 0.6rem;
}

.marchio__nome {
  font-size: 0.95rem;
  font-weight: 650;
  letter-spacing: -0.01em;
}

.marchio__versione {
  font-size: 0.7rem;
  color: var(--testo-tenue);
  font-variant-numeric: tabular-nums;
}

/* --- categorie --- */

.menu {
  display: flex;
  flex-direction: column;
  gap: 1.4rem;
}

/* Un utente senza permessi deve capire che il pannello funziona e che il
   vuoto e' una scelta di chi amministra, non un guasto. */
.niente {
  margin: 0;
  padding: 0.5rem 0.15rem;
  font-size: 0.8125rem;
  color: var(--testo-tenue);
}

.categoria__titolo {
  margin: 0 0 0.5rem;
  padding-inline: 0.65rem;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--testo-tenue);
}

.voci--figlie {
  margin: .1rem 0 .3rem;
  padding-left: 1.5rem;
  border-left: 1px solid var(--bordo);
  margin-left: .85rem;
}

.voce--figlia {
  font-size: .82rem;
  padding-block: .25rem;
}

.punto {
  flex: none;
  width: .5rem;
  height: .5rem;
  border-radius: 2px;
  background: var(--tinta-pubblicazioni);
}

.punto--vuoto {
  background: none;
  border: 1px dashed var(--bordo);
}

.voce--aggiungi {
  color: var(--testo-tenue);
}

.pastiglia--vuota {
  background: none;
  border: 1px dashed var(--bordo);
  box-shadow: none;
}

.voci {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

/* --- pulsante di vetro --- */

.voce {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.5rem 0.7rem;
  border-radius: 11px;
  text-decoration: none;
  color: var(--testo);
  font-size: 0.875rem;
  background: var(--vetro-sfondo);
  border: 1px solid var(--vetro-bordo);
  /* La sfocatura di ciò che sta dietro è ciò che rende il vetro traslucido
     invece che semplicemente semitrasparente. */
  backdrop-filter: blur(14px) saturate(180%);
  -webkit-backdrop-filter: blur(14px) saturate(180%);
  box-shadow:
    inset 0 1px 0 var(--vetro-luce),
    var(--vetro-ombra);
}

@media (prefers-reduced-motion: no-preference) {
  .voce {
    transition:
      transform 0.16s ease,
      box-shadow 0.16s ease,
      background 0.16s ease;
  }
}

a.voce:hover {
  background: var(--vetro-attivo);
  transform: translateY(-1px);
}

a.voce:active {
  transform: translateY(0);
  box-shadow: inset 0 1px 3px rgb(0 0 0 / 18%);
}

a.voce.router-link-exact-active {
  background: var(--vetro-attivo);
  border-color: color-mix(in srgb, var(--accento) 45%, var(--vetro-bordo));
  font-weight: 600;
}


.voce__testo {
  flex: 1;
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* --- pastiglia colorata dell'icona --- */

.pastiglia {
  flex: none;
  inline-size: 28px;
  block-size: 28px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  /* Non un colore piatto: sfumatura dalla tinta a una sua versione più cupa,
     più un filo di luce in alto che simula il riflesso. */
  background:
    linear-gradient(
      165deg,
      color-mix(in srgb, var(--tinta) 100%, white 18%),
      color-mix(in srgb, var(--tinta) 78%, black 22%)
    );
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 45%),
    0 2px 5px -1px color-mix(in srgb, var(--tinta) 55%, transparent);
}

.pastiglia svg {
  inline-size: 16px;
  block-size: 16px;
}


/* --- fondo: lingua e utente --- */

.fondo {
  /* Attaccato all'ultima voce del menu, non spinto in fondo alla barra: con
     `margin-block-start: auto` restava un vuoto in mezzo che faceva sembrare
     questi comandi scollegati dal resto. */
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.piede {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.6rem 0.7rem;
  border-radius: 11px;
  background: var(--vetro-sfondo);
  border: 1px solid var(--vetro-bordo);
  backdrop-filter: blur(14px) saturate(180%);
  -webkit-backdrop-filter: blur(14px) saturate(180%);
  box-shadow: inset 0 1px 0 var(--vetro-luce);
}

.piede__utente {
  display: flex;
  flex-direction: column;
  font-size: 0.8125rem;
  min-inline-size: 0;
}

.piede__utente em {
  font-style: normal;
  font-size: 0.68rem;
  color: var(--testo-tenue);
}

.esci {
  flex: none;
  padding: 0.3rem 0.6rem;
  font: inherit;
  font-size: 0.75rem;
  color: var(--testo);
  background: transparent;
  border: 1px solid var(--bordo);
  border-radius: 7px;
  cursor: pointer;
}

/* --- schermi stretti: la barra scorre da sinistra --- */

@media (max-width: 860px) {
  .barra {
    position: fixed;
    inset-block: 0;
    inset-inline-start: 0;
    z-index: 20;
    transform: translateX(-100%);
    box-shadow: 0 0 40px rgb(0 0 0 / 30%);
  }

  @media (prefers-reduced-motion: no-preference) {
    .barra {
      transition: transform 0.22s ease;
    }
  }

  .barra--aperta {
    transform: translateX(0);
  }
}
</style>
