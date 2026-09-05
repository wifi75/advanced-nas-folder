<script setup lang="ts">
/**
 * Navigazione di una cartella pubblicata.
 *
 * È l'unica vista che funziona anche senza aver effettuato l'accesso: chi
 * riceve il collegamento a una cartella pubblica non ha un account, e
 * chiedergliene uno renderebbe quella visibilità inutile.
 */
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { chiudiConEsc } from '@/composables/finestra'
import { useRoute, useRouter } from 'vue-router'

import {
  archivioApi,
  indirizzoDownload,
  indirizzoZip,
  scaricaSelezione,
  type Contenuto,
  type Voce,
} from '@/api/archivio'
import { ApiError, tokenCorrente } from '@/api/client'
import Anteprima from '@/components/Anteprima.vue'
import MiniaturaVoce from '@/components/MiniaturaVoce.vue'
import AccessoCartella from '@/components/AccessoCartella.vue'
import Caricamenti from '@/components/Caricamenti.vue'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()

const contenuto = ref<Contenuto | null>(null)
const errore = ref<string | null>(null)
/** Vero quando il percorso è protetto da password e non l'abbiamo ancora. */
/** Quale schermata di accesso mostrare, se serve. `null` = nessuna. */
const modoAccesso = ref<'password' | 'utenti' | null>(null)
const password = ref('')
const carico = ref(false)
const inPreparazione = ref<string | null>(null)

const slug = computed(() => String(route.params.slug ?? ''))
const percorso = computed(() => {
  const parti = route.params.percorso
  return Array.isArray(parti) ? parti.join('/') : String(parti ?? '')
})

// Prima di `carica`, che legge `vista` per decidere se chiedere anche le date
// di scatto: il controllo che la esegue parte subito, e trovando la
// dichiarazione piu' sotto la pagina moriva con «Cannot access ... before
// initialization».
// --- vista ---
//
// La scelta resta nel browser di chi guarda: e una preferenza di lettura, non
// una proprieta della cartella, e imporla a tutti sarebbe sbagliato.
type Vista = 'elenco' | 'griglia' | 'galleria'
const VISTE: Vista[] = ['elenco', 'griglia', 'galleria']
const CHIAVE_VISTA = 'anf.archivio.vista'

function vistaSalvata(): Vista {
  try {
    const letta = localStorage.getItem(CHIAVE_VISTA)
    if (letta && (VISTE as string[]).includes(letta)) return letta as Vista
  } catch {
    // Finestra privata, dati del sito bloccati: si riparte dalla griglia.
  }
  return 'griglia'
}

const vista = ref<Vista>(vistaSalvata())

function cambiaVista(nuova: Vista): void {
  const servonoDate = nuova === 'galleria' && vista.value !== 'galleria'
  vista.value = nuova
  if (servonoDate) void carica()
  try {
    localStorage.setItem(CHIAVE_VISTA, nuova)
  } catch {
    // La vista funziona lo stesso, semplicemente non viene ricordata.
  }
}

/** Immagini e video: entrambi hanno una miniatura, prodotta dal server. */
function haMiniatura(voce: Voce): boolean {
  return !voce.cartella && /\.(jpe?g|png|gif|webp|avif|bmp|mp4|m4v|mov|mkv|webm|avi)$/i.test(voce.nome)
}

/** Le sole immagini: la presentazione e i dati di scatto valgono per quelle. */
function eImmagine(voce: Voce): boolean {
  return !voce.cartella && /\.(jpe?g|png|gif|webp|avif|bmp)$/i.test(voce.nome)
}

// La ricerca sta qui, prima di tutto cio' che legge `voci`: menu contestuale,
// anteprima e raggruppamenti la usano, e dichiararla piu' sotto la
// renderebbe irraggiungibile nel momento in cui il componente si prepara.

// --- ricerca ---
const termine = ref('')
const risultati = ref<Voce[] | null>(null)
const troncata = ref(false)
const cercando = ref(false)

/** Le voci a schermo: i risultati se si sta cercando, altrimenti la cartella. */
const voci = computed(() => risultati.value ?? contenuto.value?.voci ?? [])

// --- menu contestuale ---
//
// Le stesse azioni della riga, raggiungibili col tasto destro. Nelle viste a
// griglia e galleria i pulsanti per esteso non ci stanno, e senza il menu
// quelle viste sarebbero di sola lettura.
const menu = ref<{ voce: Voce; x: number; y: number } | null>(null)

function apriMenuA(voce: Voce, x: number, y: number): void {
  // Si tiene il menu dentro la finestra: aperto a filo del bordo destro
  // finirebbe fuori schermo, e sui telefoni non ci sarebbe modo di tornarci.
  const larghezza = 200
  const altezza = 190
  menu.value = {
    voce,
    x: Math.min(x, window.innerWidth - larghezza),
    y: Math.min(y, window.innerHeight - altezza),
  }
}

function apriMenu(voce: Voce, evento: MouseEvent): void {
  apriMenuA(voce, evento.clientX, evento.clientY)
}

function chiudiMenu(): void {
  menu.value = null
}

// --- stesso menu, aperto con una pressione prolungata su touch ---
//
// Il tasto destro non esiste su un telefono: senza questo, rinomina/sposta/
// elimina non erano raggiungibili nelle viste a griglia e galleria, dove i
// pulsanti per esteso non ci stanno apposta (restano nel menu).
const DURATA_PRESSIONE = 500
let timerPressione: ReturnType<typeof setTimeout> | null = null
let partenzaTocco: { x: number; y: number } | null = null
let pressioneScattata = false

function iniziaPressione(voce: Voce, evento: TouchEvent): void {
  const tocco = evento.touches[0]
  if (!tocco) return
  partenzaTocco = { x: tocco.clientX, y: tocco.clientY }
  pressioneScattata = false
  timerPressione = setTimeout(() => {
    timerPressione = null
    pressioneScattata = true
    apriMenuA(voce, tocco.clientX, tocco.clientY)
  }, DURATA_PRESSIONE)
}

function spostaPressione(evento: TouchEvent): void {
  // Un dito che scorre stava scorrendo la pagina, non tenendo premuto: si
  // annulla, altrimenti il menu si aprirebbe anche durante uno scroll.
  const tocco = evento.touches[0]
  if (!tocco || !partenzaTocco || !timerPressione) return
  const distanza = Math.hypot(tocco.clientX - partenzaTocco.x, tocco.clientY - partenzaTocco.y)
  if (distanza > 10) annullaPressione()
}

function annullaPressione(): void {
  if (timerPressione) {
    clearTimeout(timerPressione)
    timerPressione = null
  }
  partenzaTocco = null
}

function finePressione(evento: TouchEvent): void {
  // Se il menu si e' appena aperto da questa stessa pressione, il tocco che
  // solleva il dito non deve anche aprire il file sotto: e' lo stesso gesto
  // di apertura, non due separati.
  if (pressioneScattata) {
    evento.preventDefault()
    pressioneScattata = false
  }
  annullaPressione()
}

function sbloccaConPassword(valore: string): void {
  password.value = valore
  void carica()
}

async function carica(): Promise<void> {
  carico.value = true
  errore.value = null
  try {
    // Le date di scatto solo in miniature, dove servono a raggruppare: la
    // prima volta il server deve aprire ogni immagine, e chiederle anche in
    // elenco significherebbe pagarle senza usarle.
    contenuto.value = await archivioApi.contenuto(
      slug.value,
      percorso.value,
      password.value || undefined,
      vista.value === 'galleria',
    )
    modoAccesso.value = null
  } catch (e) {
    contenuto.value = null
    // Il server dice cosa servirebbe: una parola d'ordine o un account. Prima
    // il pannello chiedeva sempre la password, anche dove serviva un accesso —
    // e chi non l'aveva restava in un vicolo cieco.
    if (e instanceof ApiError && e.status === 403 && e.richiede === 'password') {
      modoAccesso.value = 'password'
    } else if (e instanceof ApiError && (e.status === 401 || e.richiede === 'accesso')) {
      modoAccesso.value = 'utenti'
    } else {
      modoAccesso.value = null
    }
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    carico.value = false
  }
}

watch([slug, percorso], carica, { immediate: true })

function apri(voce: Voce): void {
  router.push(`/archivio/${slug.value}/${voce.percorso.split('/').map(encodeURIComponent).join('/')}`)
}

function vaiA(p: string): void {
  const coda = p ? `/${p.split('/').map(encodeURIComponent).join('/')}` : ''
  router.push(`/archivio/${slug.value}${coda}`)
}

async function scarica(voce: Voce): Promise<void> {
  inPreparazione.value = voce.percorso
  try {
    // Una navigazione, non una fetch: è il browser a doversi occupare della
    // barra di avanzamento e della ripresa se la rete cade.
    window.location.href = await indirizzoDownload(
      slug.value,
      voce.percorso,
      password.value || undefined,
    )
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    inPreparazione.value = null
  }
}

// --- anteprima ---
const inAnteprima = ref<Voce | null>(null)

/** Le sole immagini della cartella, nell'ordine in cui si vedono. */
const immagini = computed(() => voci.value.filter(eImmagine))

/**
 * Le voci divise per mese di scatto, come in una raccolta di fotografie.
 *
 * Chi non ha una data finisce in un gruppo a parte in fondo, invece di essere
 * infilato in un mese qualunque: una foto senza data non e' una foto di
 * gennaio.
 */
const gruppi = computed(() => {
  if (vista.value !== 'galleria') return [{ titolo: '', voci: voci.value }]

  const perMese = new Map<string, Voce[]>()
  const senzaData: Voce[] = []

  for (const voce of voci.value) {
    if (!voce.scattata) {
      senzaData.push(voce)
      continue
    }
    const quando = new Date(voce.scattata)
    const chiave = `${quando.getFullYear()}-${String(quando.getMonth() + 1).padStart(2, '0')}`
    const gruppo = perMese.get(chiave)
    if (gruppo) gruppo.push(voce)
    else perMese.set(chiave, [voce])
  }

  const titolo = (chiave: string): string => {
    const [anno, mese] = chiave.split('-')
    const data = new Date(Number(anno), Number(mese) - 1, 1)
    return data.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
  }

  // Dal piu' recente: e' l'ordine in cui si cercano le foto.
  const ordinati = [...perMese.keys()].sort().reverse()
  const elenco = ordinati.map((chiave) => ({ titolo: titolo(chiave), voci: perMese.get(chiave)! }))
  if (senzaData.length > 0) elenco.push({ titolo: t('archivio.senzaData'), voci: senzaData })
  return elenco
})

const posizione = computed(() => {
  if (!inAnteprima.value) return 0
  return immagini.value.findIndex((v) => v.percorso === inAnteprima.value?.percorso) + 1
})

function scorri(passo: number): void {
  const nuova = immagini.value[posizione.value - 1 + passo]
  if (nuova) inAnteprima.value = nuova
}

// --- selezione ---
// Un insieme di percorsi, non di indici: cambiando cartella o cercando,
// l'elenco si rimescola e gli indici punterebbero ad altro.
const scelti = ref<Set<string>>(new Set())

function alternaScelta(voce: Voce): void {
  const prossimi = new Set(scelti.value)
  if (prossimi.has(voce.percorso)) prossimi.delete(voce.percorso)
  else prossimi.add(voce.percorso)
  scelti.value = prossimi
}

function azzeraScelta(): void {
  scelti.value = new Set()
}

async function scaricaScelti(): Promise<void> {
  errore.value = null
  try {
    await scaricaSelezione(
      slug.value,
      [...scelti.value],
      percorso.value.split('/').pop() || 'selezione',
      tokenCorrente(),
    )
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  }
}

// --- icone ---
// Tracciati semplici sulla stessa griglia 24×24, come quelli della barra
// laterale: hanno tutti lo stesso peso ottico.
const TRACCIATI: Record<string, string> = {
  cartella: 'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z',
  immagine: 'M4 5h16v14H4Z M4 16l4-4 3 3 4-4 5 5',
  video: 'M3 6h13v12H3Z M16 10l5-3v10l-5-3',
  audio: 'M10 17V6l8-2v11 M10 17a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0Z M18 15a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0Z',
  archivio: 'M4 7h16v13H4Z M4 7l2-3h12l2 3 M12 11v5 M10 13h4',
  documento: 'M6 3h7l5 5v13H6Z M13 3v5h5 M9 13h6 M9 17h4',
  codice: 'M9 8l-4 4 4 4 M15 8l4 4-4 4',
  file: 'M6 3h7l5 5v13H6Z M13 3v5h5',
}

// Bastano poche famiglie: distinguere il .odt dal .docx non aiuta nessuno a
// trovare un file, distinguere un documento da un video sì.
const FAMIGLIE: Record<string, RegExp> = {
  immagine: /\.(jpe?g|png|gif|webp|avif|heic|bmp|tiff?|svg)$/i,
  video: /\.(mp4|mkv|avi|mov|webm|m4v|mpe?g|wmv)$/i,
  audio: /\.(mp3|flac|wav|aac|ogg|m4a|opus)$/i,
  archivio: /\.(zip|rar|7z|tar|gz|bz2|xz|iso)$/i,
  documento: /\.(pdf|docx?|odt|rtf|txt|md|epub)$/i,
  codice: /\.(ts|js|vue|py|sh|json|ya?ml|toml|html?|css|sql)$/i,
}

function famiglia(voce: Voce): string {
  if (voce.cartella) return 'cartella'
  for (const [nome, schema] of Object.entries(FAMIGLIE)) {
    if (schema.test(voce.nome)) return nome
  }
  return 'file'
}

async function cerca(): Promise<void> {
  const q = termine.value.trim()
  if (q.length < 2) {
    risultati.value = null
    return
  }
  cercando.value = true
  errore.value = null
  try {
    const esito = await archivioApi.cerca(slug.value, percorso.value, q)
    risultati.value = esito.voci
    troncata.value = esito.troncata
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    cercando.value = false
  }
}

function azzeraRicerca(): void {
  termine.value = ''
  risultati.value = null
  troncata.value = false
}

// Cambiando cartella la ricerca precedente non ha più senso.
watch(percorso, () => {
  azzeraRicerca()
  azzeraScelta()
})

async function scaricaCartella(): Promise<void> {
  errore.value = null
  try {
    window.location.href = await indirizzoZip(slug.value, percorso.value)
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  }
}

// --- modifiche ---
// Compaiono solo quando il server dice che questa cartella è scrivibile: il
// controllo vero lo rifà lui a ogni chiamata, ma mostrare pulsanti che
// falliranno di sicuro è solo un modo di far perdere tempo.
const puoScrivere = computed(() => contenuto.value?.scrittura === true)

const nuovaCartella = ref('')
/** Il caricamento e il modulo nuova cartella occupano spazio solo quando
 *  servono davvero: prima stavano sempre aperti, anche a cartella vuota di
 *  cose da fare, ed erano la prima cosa segnalata come disordinata. */
const mostraCaricamento = ref(false)
const mostraNuovaCartella = ref(false)
const inRinomina = ref<Voce | null>(null)
const nomeNuovo = ref('')
const daEliminare = ref<Voce | null>(null)
const daSpostare = ref<Voce | null>(null)
const destinazione = ref('')
const operazione = ref(false)

async function conEsito(azione: () => Promise<unknown>): Promise<void> {
  operazione.value = true
  errore.value = null
  try {
    await azione()
    await carica()
  } catch (e) {
    errore.value = e instanceof Error ? e.message : t('errori.generico')
  } finally {
    operazione.value = false
  }
}

async function creaCartella(): Promise<void> {
  const nome = nuovaCartella.value.trim()
  if (!nome) return
  await conEsito(async () => {
    await archivioApi.creaCartella(slug.value, percorso.value, nome)
    nuovaCartella.value = ''
    mostraNuovaCartella.value = false
  })
}

function apriRinomina(voce: Voce): void {
  inRinomina.value = voce
  nomeNuovo.value = voce.nome
}

async function confermaRinomina(): Promise<void> {
  const voce = inRinomina.value
  if (voce === null || nomeNuovo.value.trim() === '') return
  await conEsito(async () => {
    await archivioApi.rinomina(slug.value, voce.percorso, nomeNuovo.value.trim())
    inRinomina.value = null
  })
}

function apriSposta(voce: Voce): void {
  daSpostare.value = voce
  destinazione.value = percorso.value
}

async function confermaSposta(copiando: boolean): Promise<void> {
  const voce = daSpostare.value
  if (voce === null) return
  await conEsito(async () => {
    const dove = destinazione.value.trim()
    if (copiando) await archivioApi.copia(slug.value, voce.percorso, dove)
    else await archivioApi.sposta(slug.value, voce.percorso, dove)
    daSpostare.value = null
  })
}

async function confermaElimina(ricorsivo: boolean): Promise<void> {
  const voce = daEliminare.value
  if (voce === null) return
  await conEsito(async () => {
    await archivioApi.elimina(slug.value, voce.percorso, ricorsivo)
    daEliminare.value = null
  })
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

function quando(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString(locale.value, { dateStyle: 'medium', timeStyle: 'short' })
}

// Le finestre si chiudono con Esc, non cliccando sullo sfondo: un clic di
// troppo faceva perdere quello che si stava scrivendo.
chiudiConEsc(
  () => inRinomina.value !== null,
  () => {
    inRinomina.value = null
  },
)
chiudiConEsc(
  () => daSpostare.value !== null,
  () => {
    daSpostare.value = null
  },
)
chiudiConEsc(
  () => daEliminare.value !== null,
  () => {
    daEliminare.value = null
  },
)
</script>

<template>
  <!-- O la schermata di accesso, o la cartella: mai le due cose insieme.
       Titolo, ricerca e messaggi d'errore intorno al riquadro facevano
       sembrare la cartella aperta e qualcosa di rotto. -->
  <AccessoCartella
    v-if="modoAccesso"
    :cartella="contenuto?.label ?? slug"
    :modo="modoAccesso"
    @password="sbloccaConPassword"
    @entrato="carica"
  />

  <section
    v-else
    class="archivio"
  >
    <nav
      class="briciole"
      :aria-label="t('archivio.percorso')"
    >
      <div class="briciole__pillole">
        <button
          type="button"
          class="briciola"
          :class="{ 'briciola--attuale': !contenuto?.briciole?.length }"
          @click="vaiA('')"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M3 11l9-8 9 8" />
            <path d="M5 10v10h14V10" />
          </svg>
          {{ t('archivio.radice') }}
        </button>
        <template
          v-for="[nome, p], indice in contenuto?.briciole ?? []"
          :key="p"
        >
          <svg
            class="briciole__freccia"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.4"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
          <button
            type="button"
            class="briciola"
            :class="{ 'briciola--attuale': indice === (contenuto?.briciole?.length ?? 0) - 1 }"
            @click="vaiA(p)"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
            </svg>
            {{ nome }}
          </button>
        </template>
      </div>
      <span
        v-if="contenuto"
        class="meta"
      >{{ t('archivio.elementi') }}: {{ voci.length }}</span>
    </nav>

    <p
      v-if="contenuto?.descrizione"
      class="descrizione"
    >
      {{ contenuto.descrizione }}
    </p>

    <div class="strumenti">
      <form
        class="cerca"
        @submit.prevent="cerca"
      >
        <input
          v-model="termine"
          type="search"
          class="campo"
          :placeholder="t('ricerca.campo')"
          @search="cerca"
          @keyup.enter="cerca"
        >
        <button
          type="submit"
          class="bottone bottone--tenue"
          :disabled="termine.trim().length < 2 || cercando"
        >
          {{ t('ricerca.cerca') }}
        </button>
        <button
          v-if="risultati"
          type="button"
          class="bottone bottone--tenue"
          @click="azzeraRicerca"
        >
          {{ t('ricerca.azzera') }}
        </button>
      </form>

      <div
        v-if="contenuto && voci.length"
        class="viste"
        role="group"
        :aria-label="t('archivio.vista')"
      >
        <button
          v-for="v in VISTE"
          :key="v"
          type="button"
          class="vista"
          :class="{ 'vista--scelta': vista === v }"
          :aria-pressed="vista === v"
          @click="cambiaVista(v)"
        >
          {{ t(`archivio.vista${v.charAt(0).toUpperCase() + v.slice(1)}`) }}
        </button>
      </div>

      <div
        v-if="puoScrivere"
        class="divisore"
      />

      <template v-if="puoScrivere">
        <button
          type="button"
          class="bottone bottone--principale"
          :class="{ 'bottone--scelta': mostraCaricamento }"
          @click="mostraCaricamento = !mostraCaricamento"
        >
          {{ t('caricamento.mostra') }}
        </button>
        <button
          type="button"
          class="bottone bottone--tenue"
          :class="{ 'bottone--scelta': mostraNuovaCartella }"
          @click="mostraNuovaCartella = !mostraNuovaCartella"
        >
          {{ t('operazioni.nuovaCartella') }}
        </button>
      </template>

      <button
        type="button"
        class="bottone bottone--tenue"
        @click="scaricaCartella"
      >
        {{ t('archivio.scaricaCartella') }}
      </button>
    </div>

    <Caricamenti
      v-if="puoScrivere && mostraCaricamento"
      :slug="slug"
      :percorso="percorso"
      @caricato="carica"
    />

    <form
      v-if="puoScrivere && mostraNuovaCartella"
      class="riga-form"
      @submit.prevent="creaCartella"
    >
      <input
        v-model="nuovaCartella"
        type="text"
        class="campo"
        :placeholder="t('operazioni.nuovaCartella')"
      >
      <button
        type="submit"
        class="bottone bottone--tenue"
        :disabled="operazione || nuovaCartella.trim() === ''"
      >
        {{ t('operazioni.crea') }}
      </button>
    </form>

    <p
      v-if="errore && !carico"
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
      v-if="risultati"
      class="avviso"
    >
      {{ t('ricerca.esito', { n: risultati.length }, risultati.length) }}
      <template v-if="troncata">
        — {{ t('ricerca.troncata') }}
      </template>
    </p>

    <p
      v-else-if="contenuto && voci.length === 0"
      class="avviso"
    >
      {{ t('archivio.vuota') }}
    </p>

    <div
      v-if="scelti.size"
      class="selezione"
      role="status"
    >
      <span>{{ t('selezione.scelti', { n: scelti.size }, scelti.size) }}</span>
      <button
        type="button"
        class="bottone bottone--tenue"
        @click="scaricaScelti"
      >
        {{ t('selezione.scarica') }}
      </button>
      <button
        type="button"
        class="bottone bottone--tenue"
        @click="azzeraScelta"
      >
        {{ t('selezione.azzera') }}
      </button>
    </div>

    <p
      v-if="vista !== 'elenco' && contenuto && voci.length"
      class="suggerimento"
    >
      {{ t('archivio.comandiNelMenu') }}
    </p>

    <!-- In miniature le foto sono divise per mese di scatto, come in una
         raccolta: negli altri modi il gruppo e' uno solo e il titolo non
         compare. -->
    <template v-if="contenuto && voci.length">
      <section
        v-for="gruppo in gruppi"
        :key="gruppo.titolo"
        class="gruppo-date"
      >
        <h2
          v-if="gruppo.titolo"
          class="gruppo-date__titolo"
        >
          {{ gruppo.titolo }}
        </h2>
        <ul
          v-if="gruppo.voci.length"
          class="voci"
          :class="`voci--${vista}`"
        >
          <li
            v-for="voce in gruppo.voci"
            :key="voce.percorso"
            class="voce"
            @contextmenu.prevent="apriMenu(voce, $event)"
            @touchstart="iniziaPressione(voce, $event)"
            @touchmove="spostaPressione($event)"
            @touchend="finePressione"
            @touchcancel="annullaPressione"
          >
            <input
              type="checkbox"
              class="voce__scelta"
              :checked="scelti.has(voce.percorso)"
              :aria-label="t('selezione.scegli', { nome: voce.nome })"
              @change="alternaScelta(voce)"
            >

            <button
              v-if="voce.cartella"
              type="button"
              class="voce__apri"
              @click="apri(voce)"
            >
              <svg
                class="voce__icona"
                :class="`voce__icona--${famiglia(voce)}`"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path :d="TRACCIATI[famiglia(voce)]" />
              </svg>
              <span class="voce__nome">{{ risultati ? voce.percorso : voce.nome }}</span>
            </button>

            <button
              v-else
              type="button"
              class="voce__apri"
              @click="inAnteprima = voce"
            >
              <MiniaturaVoce
                v-if="vista !== 'elenco' && haMiniatura(voce)"
                :slug="slug"
                :percorso="voce.percorso"
                :nome="voce.nome"
              >
                <svg
                  class="voce__icona"
                  :class="`voce__icona--${famiglia(voce)}`"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path :d="TRACCIATI[famiglia(voce)]" />
                </svg>
              </MiniaturaVoce>
              <svg
                v-else
                class="voce__icona"
                :class="`voce__icona--${famiglia(voce)}`"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path :d="TRACCIATI[famiglia(voce)]" />
              </svg>
              <span class="voce__nome">{{ risultati ? voce.percorso : voce.nome }}</span>
            </button>

            <span class="voce__dimensione">{{ dimensione(voce.dimensione) }}</span>
            <span class="voce__data">{{ quando(voce.modificato) }}</span>

            <div class="voce__azioni">
              <button
                v-if="!voce.cartella"
                type="button"
                class="bottone bottone--tenue"
                :disabled="inPreparazione === voce.percorso"
                @click="scarica(voce)"
              >
                {{ inPreparazione === voce.percorso ? t('comune.carico') : t('archivio.scarica') }}
              </button>
              <template v-if="puoScrivere">
                <button
                  type="button"
                  class="bottone bottone--tenue"
                  @click="apriRinomina(voce)"
                >
                  {{ t('operazioni.rinomina') }}
                </button>
                <button
                  type="button"
                  class="bottone bottone--tenue"
                  @click="apriSposta(voce)"
                >
                  {{ t('operazioni.sposta') }}
                </button>
                <button
                  type="button"
                  class="bottone bottone--pericolo"
                  @click="daEliminare = voce"
                >
                  {{ t('comune.elimina') }}
                </button>
              </template>
            </div>
          </li>
        </ul>
      </section>
    </template>

    <div
      v-if="menu"
      class="menu-velo"
      @click="chiudiMenu"
      @contextmenu.prevent="chiudiMenu"
    >
      <div
        class="menu"
        :style="{ left: `${menu.x}px`, top: `${menu.y}px` }"
        role="menu"
        :aria-label="t('archivio.azioniSu', { nome: menu.voce.nome })"
      >
        <button
          v-if="menu.voce.cartella"
          type="button"
          role="menuitem"
          @click="apri(menu.voce), chiudiMenu()"
        >
          {{ t('archivio.apriCartella') }}
        </button>
        <template v-else>
          <button
            type="button"
            role="menuitem"
            @click="inAnteprima = menu.voce, chiudiMenu()"
          >
            {{ t('archivio.vediAnteprima') }}
          </button>
          <button
            type="button"
            role="menuitem"
            @click="scarica(menu.voce), chiudiMenu()"
          >
            {{ t('archivio.scarica') }}
          </button>
        </template>
        <template v-if="puoScrivere">
          <button
            type="button"
            role="menuitem"
            @click="apriRinomina(menu.voce), chiudiMenu()"
          >
            {{ t('operazioni.rinomina') }}
          </button>
          <button
            type="button"
            role="menuitem"
            @click="apriSposta(menu.voce), chiudiMenu()"
          >
            {{ t('operazioni.sposta') }}
          </button>
          <button
            type="button"
            role="menuitem"
            class="menu__pericolo"
            @click="daEliminare = menu.voce, chiudiMenu()"
          >
            {{ t('comune.elimina') }}
          </button>
        </template>
      </div>
    </div>

    <Anteprima
      v-if="inAnteprima"
      :slug="slug"
      :voce="inAnteprima"
      :modificabile="puoScrivere"
      :posizione="posizione"
      :quante="immagini.length"
      @chiudi="inAnteprima = null"
      @salvato="carica"
      @precedente="scorri(-1)"
      @successiva="scorri(1)"
      @prima-immagine="inAnteprima = immagini[0] ?? inAnteprima"
    />

    <div
      v-if="inRinomina"
      class="velo"
    >
      <form
        class="pannello"
        @submit.prevent="confermaRinomina"
      >
        <h2>{{ t('operazioni.rinomina') }}</h2>
        <input
          v-model="nomeNuovo"
          type="text"
          class="campo"
        >
        <div class="pannello__azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="inRinomina = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="submit"
            class="bottone"
            :disabled="operazione"
          >
            {{ t('comune.salva') }}
          </button>
        </div>
      </form>
    </div>

    <div
      v-if="daSpostare"
      class="velo"
    >
      <div
        class="pannello"
        role="dialog"
      >
        <h2>{{ t('operazioni.spostaTitolo', { nome: daSpostare.nome }) }}</h2>
        <label
          class="pannello__etichetta"
          for="anf-destinazione"
        >{{ t('operazioni.destinazione') }}</label>
        <input
          id="anf-destinazione"
          v-model="destinazione"
          type="text"
          class="campo"
          :placeholder="t('archivio.radice')"
        >
        <div class="pannello__azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="daSpostare = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="button"
            class="bottone bottone--tenue"
            :disabled="operazione"
            @click="confermaSposta(true)"
          >
            {{ t('operazioni.copia') }}
          </button>
          <button
            type="button"
            class="bottone"
            :disabled="operazione"
            @click="confermaSposta(false)"
          >
            {{ t('operazioni.sposta') }}
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="daEliminare"
      class="velo"
    >
      <div
        class="pannello"
        role="dialog"
      >
        <h2>{{ t('operazioni.eliminaTitolo', { nome: daEliminare.nome }) }}</h2>
        <p class="pannello__testo">
          {{
            daEliminare.cartella ? t('operazioni.eliminaCartella') : t('operazioni.eliminaFile')
          }}
        </p>
        <div class="pannello__azioni">
          <button
            type="button"
            class="bottone bottone--tenue"
            @click="daEliminare = null"
          >
            {{ t('comune.annulla') }}
          </button>
          <button
            type="button"
            class="bottone bottone--pericolo"
            :disabled="operazione"
            @click="confermaElimina(daEliminare.cartella)"
          >
            {{ t('comune.elimina') }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.archivio {
  display: flex;
  flex: 1;
  flex-direction: column;
  /* Stessa larghezza delle altre viste: righe lunghe quanto lo schermo
     rendono difficile seguire la riga fino alla colonna della data. */
  width: min(880px, 100% - 2.5rem);
  margin-inline: auto;
  gap: 1.25rem;
  padding-block: 1.5rem;

  /* Vetro proprio di questa pagina, non quello globale: i --vetro-* di
     main.css sono ritinti di ciano in scuro per l'identita' del pannello
     (v0.28.0). Senza questi, chi apre un link ereditava quel ciano per un
     caso di implementazione, non per scelta — questa pagina ha un'identita'
     apposta, piu' calma, separata da quella di chi amministra. In chiaro
     restano vicini ai --vetro-* di base, gia' neutri li'. */
  /* In chiaro un vetro bianco su una pagina già quasi bianca (--sfondo)
     non si distingue, ombra o non ombra: qui bordo e sfondo diventano
     solidi e visibili invece di restare traslucidi come gli originali
     --vetro-*, pensati per un fondo scuro. Resta "vetro" solo in scuro,
     dove il contrasto con lo sfondo c'è davvero (blocchi sotto). */
  --vetro-sfondo-pub: var(--superficie);
  --vetro-bordo-pub: var(--bordo);
  --vetro-luce-pub: rgb(255 255 255 / 60%);
  --vetro-attivo-pub: var(--superficie-alt);
}

@media (prefers-color-scheme: dark) {
  :root:not([data-tema='chiaro']) .archivio {
    --vetro-sfondo-pub: linear-gradient(158deg, rgb(255 255 255 / 11%), rgb(255 255 255 / 3%));
    --vetro-bordo-pub: rgb(255 255 255 / 16%);
    --vetro-luce-pub: rgb(255 255 255 / 24%);
    --vetro-attivo-pub: linear-gradient(158deg, rgb(255 255 255 / 20%), rgb(255 255 255 / 8%));
  }
}

:root[data-tema='scuro'] .archivio {
  --vetro-sfondo-pub: linear-gradient(158deg, rgb(255 255 255 / 11%), rgb(255 255 255 / 3%));
  --vetro-bordo-pub: rgb(255 255 255 / 16%);
  --vetro-luce-pub: rgb(255 255 255 / 24%);
  --vetro-attivo-pub: linear-gradient(158deg, rgb(255 255 255 / 20%), rgb(255 255 255 / 8%));
}

/* .intestazione, .titolo, .descrizione, .briciole* e .viste* sono ora in
   assets/archivio-comune.css: le 5 intestazioni (components/archivio/) le
   usano tutte, e lo stile scoped di questo file non le raggiungerebbe. */

/* Il velo copre la pagina per intercettare il clic che chiude il menu, ovunque
   cada: senza, il menu resterebbe aperto cliccando su un'altra riga. */
.menu-velo {
  position: fixed;
  inset: 0;
  z-index: 40;
}

.menu {
  position: fixed;
  min-width: 11rem;
  display: flex;
  flex-direction: column;
  padding: 0.25rem;
  border: 1px solid var(--vetro-bordo-pub);
  border-radius: var(--raggio);
  background: var(--vetro-sfondo-pub);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  box-shadow:
    inset 0 1px 0 var(--vetro-luce-pub),
    0 0.5rem 1.5rem rgb(0 0 0 / 0.18);
}

.menu button {
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  text-align: left;
  padding: 0.4rem 0.6rem;
  border-radius: var(--raggio);
  cursor: pointer;
}

.menu button:hover {
  background: var(--superficie-alt);
}

.menu__pericolo {
  color: var(--errore);
}

/* Il mese come intestazione, non come etichetta su ogni foto: si legge una
   volta e vale per tutte quelle che seguono. */
.gruppo-date + .gruppo-date {
  margin-top: 1.4rem;
}

.gruppo-date__titolo {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--testo-tenue);
  text-transform: capitalize;
}

.suggerimento {
  margin: -0.3rem 0 0.2rem;
  font-size: 0.78rem;
  color: var(--testo-tenue);
}

/* Griglia e galleria: le stesse voci disposte in schede invece che in righe.
   Dimensione e data restano fuori — in una scheda stretta finirebbero a capo
   e renderebbero le colonne irregolari, che e proprio cio che una griglia
   dovrebbe evitare. */
/* La regola di base deve precedere i modificatori: hanno la stessa
   specificita', quindi a parita' vince l'ultima scritta. Messa dopo,
   `display: flex` annullava il `display: grid` di griglia e galleria e
   ogni voce diventava una riga larga quanto la pagina. */
.voci {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.voci--griglia,
.voci--galleria {
  display: grid;
  background: none;
  border: 0;
  overflow: visible;
}

.voci--griglia {
  gap: 0.6rem;
}

.voci--griglia {
  grid-template-columns: repeat(auto-fill, minmax(11rem, 1fr));
}

/* La galleria e' un mosaico di immagini, non un elenco con le miniature
   dentro: quadrati affiancati, nessun nome, nessun pulsante. E' il modo in cui
   si guardano le foto — il nome di uno scatto non dice niente, la foto si'. */
.voci--galleria {
  grid-template-columns: repeat(auto-fill, minmax(7.5rem, 1fr));
  gap: 3px;
}

.voci--galleria .voce {
  position: relative;
  aspect-ratio: 1;
  padding: 0;
  gap: 0;
  border: 0;
  border-radius: 4px;
  background: var(--superficie-alt);
  box-shadow: none;
  overflow: hidden;
  grid-template-columns: 1fr;
}

.voci--galleria .voce:hover {
  border: 0;
}

/* Il pulsante copre l'intero riquadro: si clicca la foto, non un'etichetta. */
.voci--galleria .voce__apri {
  position: absolute;
  inset: 0;
  padding: 0;
  flex-direction: column;
  justify-content: flex-end;
  align-items: stretch;
  gap: 0;
}

.voci--galleria .miniatura {
  position: absolute;
  inset: 0;
  aspect-ratio: auto;
  border-radius: 0;
}

/* Il nome resta, ma solo al passaggio del mouse e solo per le cartelle, che
   senza non si distinguerebbero l'una dall'altra. */
.voci--galleria .voce__nome {
  position: relative;
  z-index: 1;
  padding: 1.5rem 0.4rem 0.35rem;
  font-size: 0.72rem;
  color: #fff;
  text-align: left;
  background: linear-gradient(to top, rgb(0 0 0 / 68%), transparent);
  opacity: 0;
  transition: opacity 0.12s ease;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voci--galleria .voce:hover .voce__nome,
.voci--galleria .voce__apri:focus-visible .voce__nome {
  opacity: 1;
}

/* Le cartelle non hanno miniatura: il nome deve restare sempre leggibile.
   E la sfumatura scura non ha senso qui — esiste per staccare il testo bianco
   da una fotografia, e sopra il riquadro chiaro di una cartella resta solo una
   macchia grigia. Il nome torna del colore del testo, sotto l'icona. */
.voci--galleria .voce:has(.voce__icona--cartella) .voce__nome {
  opacity: 1;
  padding: 0.35rem 0.4rem;
  color: var(--testo);
  background: none;
  text-align: center;
}

.voci--galleria .voce__icona {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 42%;
  height: 42%;
}

.voci--galleria .voce__dimensione,
.voci--galleria .voce__data,
.voci--galleria .voce__azioni {
  display: none;
}

/* La casella di selezione compare al passaggio, o resta se e' gia' scelta. */
.voci--galleria .voce__scelta {
  position: absolute;
  top: 0.3rem;
  left: 0.3rem;
  z-index: 2;
  opacity: 0;
  accent-color: var(--accento);
}

.voci--galleria .voce:hover .voce__scelta,
.voci--galleria .voce__scelta:checked,
.voci--galleria .voce__scelta:focus-visible {
  opacity: 1;
}

.voci--griglia .voce,
.voci--galleria .voce {
  grid-template-columns: 1fr;
  align-content: start;
  gap: 0.4rem;
  padding: 0.6rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
}

/* In griglia l'icona ha lo stesso spazio di una miniatura: prima era grande
   come quella di un elenco, persa in una scheda alta il triplo, e il nome
   restava schiacciato in fondo. */
.voci--griglia .voce__apri {
  display: grid;
  grid-template-rows: 1fr auto;
  gap: 0.45rem;
  width: 100%;
  padding: 0;
  text-align: center;
}

.voci--griglia .voce__icona {
  width: 100%;
  height: auto;
  aspect-ratio: 4 / 3;
  max-height: 5.5rem;
  justify-self: center;
  align-self: center;
}

/* Due righe e poi i puntini: un nome lungo non deve allungare la scheda e
   sfalsare la griglia. */
.voci--griglia .voce__nome {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
  font-size: 0.85rem;
  line-height: 1.3;
}

/* In griglia la miniatura non riempie la scheda: accanto al nome ci deve
   stare anche il resto, e una foto quadrata a tutta larghezza spingerebbe il
   nome fuori dallo schermo su una colonna stretta. */
.voci--griglia .miniatura {
  aspect-ratio: 4 / 3;
}

.voci--galleria .voce__nome {
  overflow-wrap: anywhere;
}

/* In griglia i comandi per esteso occupavano piu' spazio della cartella
   stessa: tre pulsanti impilati sotto ogni scheda, su un telefono meta'
   schermo. Restano nel menu contestuale, che li ha tutti. */
.voci--griglia .voce__data,
.voci--griglia .voce__dimensione,
.voci--griglia .voce__azioni,
.voci--galleria .voce__data,
.voci--galleria .voce__dimensione {
  display: none;
}

/* La casella di selezione sta sopra la miniatura invece che accanto: in una
   scheda stretta rubberebbe larghezza al nome. */
.voci--griglia .voce__scelta {
  position: absolute;
  top: 0.45rem;
  left: 0.45rem;
  z-index: 1;
}

.voci--griglia .voce {
  position: relative;
}

.voci--galleria .voce__scelta {
  justify-self: start;
}


.voce {
  display: grid;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.85rem;
  border-radius: 11px;
  background: var(--vetro-sfondo-pub);
  border: 1px solid var(--vetro-bordo-pub);
  backdrop-filter: blur(14px) saturate(180%);
  -webkit-backdrop-filter: blur(14px) saturate(180%);
  box-shadow:
    inset 0 1px 0 var(--vetro-luce-pub),
    var(--vetro-ombra);
  /* Casella, poi nome elastico, poi dimensione e data a larghezza fissa così
     le colonne restano allineate anche quando i nomi sono molto diversi. */
  grid-template-columns: auto minmax(0, 1fr) 5.5rem 11rem auto;
}

.voce:hover {
  /* Non l'accento del pannello (in scuro e' ciano, identita' del pannello):
     qui l'enfasi resta neutra, sul colore del testo stesso. */
  border-color: color-mix(in srgb, var(--testo) 28%, var(--vetro-bordo-pub));
}

.voce__scelta {
  margin: 0;
}

/* Fissa in basso invece che nel flusso: comparendo fra le voci sposterebbe
   l'elenco a ogni prima selezione, e la casella successiva finirebbe sotto il
   dito di chi sta selezionando. */
.selezione {
  position: fixed;
  left: 50%;
  /* Sopra il pie' di pagina, non addosso: quello sta nel flusso e su una
     cartella corta finisce proprio al fondo dello schermo, dove questa barra
     e' fissa. Si sovrapponevano, e meta' dei comandi restava illeggibile. */
  bottom: var(--fondo-sicuro);
  z-index: 10;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.7rem 0.55rem 1rem;
  border: 1px solid var(--vetro-bordo-pub);
  border-radius: 12px;
  background: var(--vetro-sfondo-pub);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  box-shadow:
    inset 0 1px 0 var(--vetro-luce-pub),
    0 8px 26px -12px rgb(0 0 0 / 45%);
  font-size: 0.9rem;
  transform: translateX(-50%);
}

.voce__apri {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 0.6rem;
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  text-align: left;
}

.voce__apri {
  cursor: pointer;
}

.voce__apri:hover .voce__nome {
  text-decoration: underline;
}

.voce__icona {
  flex: none;
  width: 1.15rem;
  height: 1.15rem;
  fill: none;
  stroke: var(--testo-tenue);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.6;
}

/* Una tinta per famiglia: il colore fa da indice visivo quando l'elenco è
   lungo, molto più del nome dell'estensione. */
.voce__icona--cartella {
  stroke: var(--tinta-file);
}

.voce__icona--immagine {
  stroke: var(--tinta-pubblicazioni);
}

.voce__icona--video {
  stroke: var(--tinta-link);
}

.voce__icona--audio {
  stroke: var(--tinta-utenti);
}

.voce__icona--archivio {
  stroke: var(--tinta-webserver);
}

.voce__icona--documento {
  stroke: var(--tinta-nfs);
}

.voce__icona--codice {
  stroke: var(--tinta-trasferimenti);
}

.voce__nome {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.voce__dimensione,
.voce__data {
  color: var(--testo-tenue);
  font-size: 0.85rem;
  /* Cifre a larghezza fissa: senza, le colonne di numeri ballano. */
  font-variant-numeric: tabular-nums;
}

.voce__dimensione {
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




.voce__azioni {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}


/* Percorso a pillole, con icona: una fila di testo sottile si perdeva
   nella pagina e non dava un punto di riferimento chiaro su dove ci si
   trova. La pillola piena segna la cartella attuale. */
.briciole {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.9rem;
}

.briciole__pillole {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: wrap;
}

.briciola {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--bordo);
  border-radius: 999px;
  background: var(--superficie);
  color: var(--testo-tenue);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
}

.briciola svg {
  flex: none;
  inline-size: 14px;
  block-size: 14px;
}

.briciola:hover {
  border-color: var(--accento);
  color: var(--accento);
}

.briciola--attuale {
  background: var(--accento);
  border-color: var(--accento);
  color: var(--accento-testo);
  font-weight: 600;
}

.briciole__freccia {
  flex: none;
  inline-size: 14px;
  block-size: 14px;
  color: var(--bordo);
}

.meta {
  font-size: 0.8rem;
  color: var(--testo-tenue);
  font-family: var(--font-mono);
  white-space: nowrap;
}

.descrizione {
  margin: 0 0 0.9rem;
  color: var(--testo-tenue);
}

/* Un solo riquadro per tutti i comandi della barra: niente vetro
   annidato dentro un altro riquadro, che in tema chiaro si vede a
   malapena (trovato provando la v0.28.15 su dati reali). */
.strumenti {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.7rem;
  border: 1px solid var(--bordo);
  border-radius: var(--raggio);
  background: var(--superficie);
  box-shadow: 0 1px 2px rgb(16 24 32 / 4%);
  margin-bottom: 0.9rem;
}

.cerca {
  display: flex;
  flex: 1 1 14rem;
  gap: 0.5rem;
}

.strumenti .divisore {
  inline-size: 1px;
  align-self: stretch;
  background: var(--bordo);
}

.viste {
  display: inline-flex;
  gap: 0.3rem;
}

.vista {
  border: 1px solid var(--bordo);
  border-radius: 6px;
  background: var(--superficie);
  color: var(--testo-tenue);
  padding: 0.4rem 0.75rem;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
}

.vista:hover {
  border-color: var(--accento);
  color: var(--accento);
}

.vista--scelta {
  color: var(--accento-testo);
  background: var(--accento);
  border-color: var(--accento);
}

.bottone--scelta {
  background: var(--superficie-alt);
  border-color: var(--accento);
  color: var(--accento);
}

.riga-form {
  display: flex;
  gap: 0.5rem;
  max-width: 26rem;
  margin-bottom: 0.9rem;
}

.velo {
  position: fixed;
  display: grid;
  padding: 1rem;
  background: rgb(0 0 0 / 45%);
  inset: 0;
  place-items: center;
}

.pannello {
  display: flex;
  flex-direction: column;
  width: min(26rem, 100%);
  gap: 0.7rem;
  padding: 1.25rem;
  border-radius: var(--raggio);
  border: 1px solid var(--vetro-bordo-pub);
  background: var(--superficie);
  box-shadow: inset 0 1px 0 var(--vetro-luce-pub), var(--vetro-ombra);
}

.pannello h2 {
  margin: 0;
  font-size: 1.05rem;
}

.pannello__testo,
.pannello__etichetta {
  margin: 0;
  color: var(--testo-tenue);
  font-size: 0.9rem;
}

.pannello__azioni {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
}




.avviso {
  margin: 0;
  color: var(--testo-tenue);
}

/* Prima era solo testo rosso sullo sfondo della pagina: un errore come
   "Pubblicazione non trovata" e' il primo messaggio che vede un visitatore
   che ha sbagliato indirizzo, e merita un riquadro vero, non una riga persa
   nel resto del testo. */
.avviso--errore {
  padding: 0.65rem 0.9rem;
  border: 1px solid color-mix(in srgb, var(--tinta-link) 40%, var(--vetro-bordo-pub));
  border-radius: var(--raggio);
  background: color-mix(in srgb, var(--tinta-link) 10%, var(--vetro-sfondo-pub));
  color: var(--tinta-link);
}

@media (width <= 40rem) {
  .voce {
    grid-template-columns: auto minmax(0, 1fr) auto;
  }

  /* Tre colonne definite sopra, ma la riga aveva ancora cinque figli visibili
     (casella, apri, dimensione, data, azioni): con "dimensione" nascosta solo
     qui sotto, "azioni" restava un quarto elemento fuori posto e la riga o
     scorreva di lato o diventava inutilmente alta. Nascosta anche
     "dimensione", che si vede comunque aprendo il file. */
  .voce__data,
  .voce__dimensione {
    display: none;
  }

  /* Su un telefono lo spazio orizzontale e' quello che manca: la galleria
     mette tre foto per riga invece di due grandi, e la griglia due schede. */
  .voci--galleria {
    grid-template-columns: repeat(3, 1fr);
    gap: 2px;
  }

  .voci--griglia {
    grid-template-columns: repeat(2, 1fr);
  }

  /* Il nome in sovrimpressione dipende dal passaggio del mouse, che su un
     telefono non esiste: per le foto sparisce, e resta solo per le cartelle
     che senza sarebbero indistinguibili. */
  .voci--galleria .voce__nome {
    display: none;
  }

  .voci--galleria .voce:has(.voce__icona--cartella) .voce__nome {
    display: block;
    opacity: 1;
  }

  /* La casella non compare al passaggio: o si vede sempre, o non si puo'
     selezionare niente col dito. */
  .voci--galleria .voce__scelta {
    opacity: 1;
  }

  /* Il selettore di vista a tutta larghezza, con bersagli piu' grandi. */
  .viste {
    display: flex;
    width: 100%;
  }

  .vista {
    flex: 1;
    padding-block: 0.5rem;
  }
}
</style>
