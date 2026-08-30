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
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import SelettoreLingua from '@/components/SelettoreLingua.vue'
import SelettoreTema from '@/components/SelettoreTema.vue'
import { useAppStore } from '@/stores/app'
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

// L'archivio si apre sempre su una pubblicazione: se non ce ne sono, la voce
// porta all'elenco delle pubblicazioni, che e' il posto da cui si comincia.
const primaPubblicazione = computed(() => shares.elenco[0]?.slug)
const { t } = useI18n()

// Tracciati delle icone: linee semplici, disegnate sulla stessa griglia 24×24
// così hanno tutte lo stesso peso ottico.
const ICONE = {
  cartellaRete: 'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z M12 11v3 M9 17h6',
  globo: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z M3 12h18 M12 3c2.5 2.7 2.5 15.3 0 18 M12 3c-2.5 2.7-2.5 15.3 0 18',
  documento: 'M6 3h7l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z M13 3v5h5 M8 13h8 M8 17h5',
  persone: 'M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z M2.5 20a6.5 6.5 0 0 1 13 0 M17 11.5a3 3 0 1 0 0-6 M17.5 14.2a6 6 0 0 1 4 5.8',
  catena: 'M10 13.5a4 4 0 0 0 5.7 0l2.8-2.8a4 4 0 0 0-5.7-5.7L11.5 6.3 M14 10.5a4 4 0 0 0-5.7 0l-2.8 2.8a4 4 0 0 0 5.7 5.7l1.3-1.3',
  battito: 'M3 12h4l2.5-6 4 12 2.5-6h5',
  frecce: 'M7 4v13 M7 17l-3-3 M7 17l3-3 M17 20V7 M17 7l-3 3 M17 7l3 3',
  ingranaggio:
    'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z M19.4 14.5a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.1a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-2.9-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.1-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 2.9-1.2V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 2.9 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.1a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1.2Z',
} as const

const categorie = computed<Categoria[]>(() => [
  {
    titolo: t('menu.archivio'),
    voci: [
      {
        etichetta: t('menu.condivisioni'),
        a: '/condivisioni',
        tinta: 'var(--tinta-nfs)',
        icona: ICONE.cartellaRete,
      },
      {
        etichetta: t('menu.pubblicazioni'),
        a: '/pubblicazioni',
        tinta: 'var(--tinta-pubblicazioni)',
        icona: ICONE.globo,
      },
      // L'archivio si apre da una pubblicazione, perche' e' la pubblicazione a
      // decidere cosa si vede: una voce di menu slegata dovrebbe chiedere
      // "quale?" prima di mostrare qualcosa.
      {
        etichetta: t('menu.file'),
        a: primaPubblicazione.value ? `/archivio/${primaPubblicazione.value}` : '/pubblicazioni',
        tinta: 'var(--tinta-file)',
        icona: ICONE.documento,
      },
    ],
  },
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
])
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

.categoria__titolo {
  margin: 0 0 0.5rem;
  padding-inline: 0.65rem;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--testo-tenue);
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
  margin-block-start: auto;
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
