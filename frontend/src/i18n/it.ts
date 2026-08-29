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
