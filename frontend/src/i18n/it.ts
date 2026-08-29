/** Traduzioni italiane. Lingua di riferimento: qui si scrive per prime. */

export default {
  comune: {
    annulla: 'Annulla',
    salva: 'Salva',
    crea: 'Crea',
    elimina: 'Elimina',
    chiudi: 'Chiudi',
    esci: 'Esci',
    carico: 'Carico…',
    amministratore: 'amministratore',
    lingua: 'Lingua',
  },

  tema: {
    titolo: 'Tema',
    chiaro: 'Chiaro',
    auto: 'Automatico',
    scuro: 'Scuro',
  },

  menu: {
    archivio: 'Archivio',
    accessi: 'Accessi',
    sistema: 'Sistema',
    condivisioni: 'Condivisioni NFS',
    pubblicazioni: 'Pubblicazioni',
    file: 'File',
    utenti: 'Utenti',
    link: 'Link di condivisione',
    stato: 'Stato',
    webserver: 'Web server',
    trasferimenti: 'Trasferimenti',
    impostazioni: 'Impostazioni',
    apri: 'Apri il menu',
    inArrivo: 'Disponibile nella {fase}',
    fase: 'fase {n}',
  },

  accesso: {
    titolo: 'Accedi',
    utente: 'Nome utente',
    password: 'Password',
    inCorso: 'Accesso in corso…',
    credenzialiErrate: 'Nome utente o password non corretti.',
    erroreImprevisto: 'Errore imprevisto durante l’accesso.',
  },

  home: {
    sottotitolo:
      'Monta condivisioni NFS, pubblica cartelle con permessi per sottocartella, gestisci i file.',
    servizioAttivo: 'Servizio attivo',
    servizioNonRaggiungibile: 'Servizio non raggiungibile',
    passwordIniziale: 'Stai usando la password iniziale.',
    passwordInizialeDettaglio:
      'Cambiala prima di rendere il pannello raggiungibile da Internet.',
    vaiCondivisioni: 'Vai alle condivisioni',
    condivisioniDescrizione:
      'Monta le cartelle del NAS dal pannello, senza toccare file di configurazione: il sistema legge dal NAS l’elenco delle cartelle disponibili e le monta al posto tuo.',
    inArrivoTitolo: 'In arrivo',
    inArrivoDescrizione:
      'La pubblicazione delle cartelle con i permessi per sottocartella arriva nella fase 2, la gestione dei file nella fase 3.',
  },

  mount: {
    titolo: 'Condivisioni NFS',
    sottotitolo: 'Monta le cartelle del NAS senza toccare file di configurazione.',
    nuova: 'Nuova condivisione',
    vuoto:
      'Nessuna condivisione configurata. Comincia da «Nuova condivisione»: il pannello legge dal NAS l’elenco delle cartelle disponibili.',
    percorso: 'Percorso',
    versione: 'Versione',
    accessoRichiesto: 'Accesso richiesto',
    accessoEffettivo: 'Accesso effettivo',
    solaLettura: 'Sola lettura',
    letturaScrittura: 'Lettura e scrittura',
    nonRilevato: 'Non rilevato',
    monta: 'Monta',
    smonta: 'Smonta',
    rileggi: 'Rileggi stato',
    statoMontato: 'Montato',
    statoSmontato: 'Non montato',
    statoErrore: 'Errore',
    statoConfigurato: 'Configurato',
    scritturaNegata: 'Il NAS sta negando la scrittura.',
    scritturaNegataDettaglio:
      'Hai richiesto lettura e scrittura, ma la condivisione risulta in sola lettura. Va abilitata anche nei permessi NFS della cartella sul NAS.',
    confermaTitolo: 'Eliminare «{nome}»?',
    confermaTesto:
      'La condivisione viene smontata e la sua configurazione rimossa dal server. I file sul NAS non vengono toccati.',
  },

  nuovoMount: {
    titolo: 'Nuova condivisione',
    indirizzoNas: 'Indirizzo del NAS',
    cerca: 'Cerca condivisioni',
    cercando: 'Cerco…',
    consentitoA: 'consentito a {client}',
    nessunaEsportazione:
      'Il NAS risponde ma non esporta nulla verso questo server. Controlla i permessi NFS della cartella condivisa.',
    soloVersioni:
      'Il NAS espone solo NFS {versioni}: la versione 4 non è disponibile e chiederla farebbe fallire il montaggio.',
    nome: 'Nome',
    identificatore: 'Identificatore',
    versioneNfs: 'Versione NFS',
    montaARichiesta: 'Monta alla prima richiesta',
    consentiScrittura: 'Consenti la scrittura',
    consentiScritturaDettaglio:
      'Il pannello potrà modificare ed eliminare file sul NAS. Va abilitata anche nei permessi NFS della cartella condivisa, altrimenti resterà in sola lettura.',
    creando: 'Creo…',
  },

  share: {
    titolo: 'Pubblicazioni',
    sottotitolo: 'Decidi quali cartelle sono raggiungibili e da chi.',
    nuova: 'Nuova pubblicazione',
    vuoto:
      'Nessuna cartella pubblicata. Una pubblicazione parte da una condivisione NFS già montata.',
    servonoMount:
      'Prima serve almeno una condivisione NFS montata: una pubblicazione parte da lì.',
    condivisione: 'Condivisione',
    sottopercorso: 'Sottocartella',
    sottopercorsoAiuto: 'Vuoto per pubblicare la radice della condivisione',
    nome: 'Nome',
    identificatore: 'Identificatore',
    descrizione: 'Descrizione',
    visibilitaPredefinita: 'Chi può accedere',
    attiva: 'Pubblicazione attiva',
    disattivata: 'Disattivata',
    creando: 'Creo…',
    confermaTitolo: 'Eliminare «{nome}»?',
    confermaTesto:
      'La pubblicazione, le sue regole e i permessi vengono rimossi. I file sul NAS non vengono toccati.',
  },

  visibilita: {
    pubblica: 'Chiunque, anche senza accedere',
    password: 'Chi conosce la password',
    utenti: 'Tutti gli utenti autenticati',
    utenti_scelti: 'Solo gli utenti autorizzati',
    negata: 'Nessuno',
    breve_pubblica: 'Pubblica',
    breve_password: 'Password',
    breve_utenti: 'Utenti',
    breve_utenti_scelti: 'Autorizzati',
    breve_negata: 'Negata',
  },

  regole: {
    titolo: 'Regole per cartella',
    descrizione:
      'Ogni regola vale per una cartella e per tutto ciò che contiene. Vince sempre la regola più specifica, così una sottocartella può essere più chiusa di quella che la contiene.',
    percorso: 'Cartella',
    radice: 'tutta la pubblicazione',
    aggiungi: 'Aggiungi regola',
    password: 'Password',
    protetta: 'protetta da password',
    nessuna: 'Nessuna regola: vale la scelta predefinita della pubblicazione.',
  },

  permessi: {
    titolo: 'Permessi per utente',
    descrizione:
      'Stabilisci quale utente raggiunge quale cartella, o tutte. Un divieto esplicito vince sulla regola della cartella, così puoi togliere un ramo a una persona lasciandolo aperto agli altri.',
    utente: 'Utente',
    cartella: 'Cartella',
    livello: 'Permesso',
    negato: 'Negato',
    lettura: 'Lettura',
    scrittura: 'Lettura e scrittura',
    assegna: 'Assegna',
    nessuno: 'Nessun permesso assegnato.',
    tutte: 'tutte le cartelle',
  },

  prova: {
    titolo: 'Verifica un accesso',
    descrizione:
      'Controlla se una cartella è raggiungibile e quale regola lo decide, prima di scoprirlo dagli utenti.',
    percorso: 'Cartella da verificare',
    come: 'Come',
    anonimo: 'Visitatore anonimo',
    verifica: 'Verifica',
    consentito: 'Accesso consentito',
    negato: 'Accesso negato',
    conScrittura: 'con scrittura',
    decisoDaRegola: 'deciso dalla regola su «{percorso}»',
    decisoDaPermesso: 'deciso dal permesso su «{percorso}»',
    decisoDaPredefinita: 'deciso dalla scelta predefinita della pubblicazione',
  },

  pwa: {
    aggiornamento: 'È disponibile una versione aggiornata del pannello.',
    ricarica: 'Aggiorna',
    prontoOffline: 'Il pannello ora funziona anche senza rete.',
  },

  webserver: {
    titolo: 'Web server',
    descrizione:
      'Pubblica il pannello su Apache o Nginx. La configurazione viene provata prima di essere applicata, e se il test non passa quella precedente torna al suo posto.',
    nonGestiamo:
      'DNS, certificati e HTTPS restano dove sono: qui si scrive solo la configurazione locale del web server.',
    pubblica: 'Pubblica su un nome host',
    hostname: 'Nome host (es. archivio.esempio.it)',
    prefisso: 'Prefisso (/)',
    anteprima: 'Anteprima',
    applica: 'Applica',
    vediConfigurazione: 'Vedi configurazione',
    nessuno: 'Il pannello non è ancora pubblicato su nessun nome host.',
    agentAssente:
      'Non riesco a parlare con il servizio di sistema: l’elenco dei web server installati non è disponibile.',
    confermaTitolo: 'Togliere la pubblicazione?',
    confermaTesto:
      'La configurazione di {host} verrà rimossa dal web server. Le cartelle e i permessi non vengono toccati.',
  },

  link: {
    titolo: 'Link di condivisione',
    descrizione:
      'Un modo per far arrivare una cartella a chi non ha un account. Il collegamento vale solo per la cartella indicata, e si può limitare nel tempo e nel numero di scaricamenti.',
    cartella: 'Cartella (vuoto = tutta)',
    etichetta: 'Nome (facoltativo)',
    giorni: 'Giorni',
    maxDownload: 'Max download',
    password: 'Password (facoltativa)',
    crea: 'Crea link',
    copia: 'Copia',
    copiato: 'Copiato',
    copiaOra:
      'Copialo adesso: nel database resta solo la sua impronta, e non potrà essere mostrato di nuovo.',
    nessuno: 'Nessun link creato.',
    attivo: 'Attivo',
    chiuso: 'Non più valido',
    revoca: 'Revoca',
    usato: 'usato {n} volte',
    scaduto: 'Questo collegamento non è più valido.',
    passwordRichiesta: 'Questo collegamento è protetto da una password.',
  },

  caricamento: {
    trascina: 'Trascina qui i file da caricare',
    scegli: 'Scegli dal dispositivo',
    fatto: 'Caricato',
    annullato: 'Annullato',
    riprova: 'Riprova',
    pulisci: 'Pulisci elenco',
    esiste: 'Esiste già un file con questo nome in questa cartella.',
  },

  operazioni: {
    nuovaCartella: 'Nome della nuova cartella',
    crea: 'Crea cartella',
    rinomina: 'Rinomina',
    sposta: 'Sposta',
    copia: 'Copia',
    spostaTitolo: 'Sposta o copia «{nome}»',
    destinazione: 'Cartella di destinazione (vuoto = inizio)',
    eliminaTitolo: 'Eliminare «{nome}»?',
    eliminaFile: 'Il file viene eliminato dal NAS. L’operazione non si può annullare.',
    eliminaCartella:
      'La cartella viene eliminata con tutto il suo contenuto. L’operazione non si può annullare.',
  },

  archivio: {
    titolo: 'Archivio',
    apri: 'Sfoglia',
    percorso: 'Percorso',
    radice: 'Inizio',
    scarica: 'Scarica',
    vuota: 'Questa cartella è vuota.',
    passwordRichiesta: 'Questo percorso è protetto da una password.',
    sblocca: 'Apri',
  },

  errori: {
    serverNonRaggiungibile: 'Server non raggiungibile. Controlla la connessione.',
    sessioneScaduta: 'Sessione scaduta. Accedi di nuovo.',
    permessiMancanti: 'Non hai i permessi per questa operazione.',
    nonTrovato: 'Risorsa non trovata.',
    conflitto: 'Operazione in conflitto con lo stato attuale.',
    erroreServer: 'Errore del server.',
    richiestaNonValida: 'Richiesta non valida.',
    imprevisto: 'Errore imprevisto.',
  },

  nonTrovata: {
    titolo: 'Pagina non trovata',
    testo: 'L’indirizzo richiesto non esiste in questo pannello.',
    torna: 'Torna al pannello',
  },

  piede: {
    attribuzione: 'Ideato e sviluppato da {autore}',
  },
}
