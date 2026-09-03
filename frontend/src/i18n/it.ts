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
    tuttePubblicazioni: 'Tutte le cartelle pubblicate',
    pubblica: 'Pubblica una cartella',
    tutteCondivisioni: 'Nuova condivisione',
    archivio: 'Archivio',
    sistema: 'Sistema',
    condivisioni: 'Condivisioni NFS',
    pubblicazioni: 'Pubblicazioni',
    file: 'File',
    utenti: 'Utenti',
    leMieCartelle: 'Le mie cartelle',
    nessunaMiaCartella: 'Nessuna cartella assegnata. Chiedi a chi amministra il pannello.',
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
    sottotitolo: 'Le cartelle del NAS, raggiungibili dal web con i permessi che decidi tu.',
    servizioAttivo: 'Servizio attivo',
    servizioNonRaggiungibile: 'Servizio non raggiungibile',
    passwordIniziale: 'Stai usando la password iniziale.',
    passwordInizialeDettaglio:
      'Cambiala prima di rendere il pannello raggiungibile da Internet.',
    comeFunziona: 'Come si arriva a una cartella condivisa',
    comeFunzionaIntro:
      'Tre passi, in quest’ordine: senza il primo il secondo non è possibile.',
    passo1: 'Monta la cartella del NAS',
    passo1Testo:
      'Il pannello chiede al NAS quali cartelle espone e la monta sul server. Da sola non è ancora raggiungibile da nessuno: sta solo sul server.',
    passo1Vai: 'Condivisioni NFS',
    passo2: 'Pubblicala',
    passo2Testo:
      'Scegli quale cartella — o quale sottocartella — rendere raggiungibile, con che nome e chi può entrarci. È questo passo a creare l’indirizzo.',
    passo2Vai: 'Pubblicazioni',
    passo3: 'Condividi l’indirizzo',
    passo3Testo:
      'Ogni pubblicazione mostra il proprio indirizzo, pronto da copiare. Per dare accesso a una singola persona senza aprire la cartella a tutti, usa invece un link di condivisione, che scade.',
    passo3Vai: 'Archivio',
    statoMount: 'nessuna cartella montata | 1 cartella montata | {count} cartelle montate',
    statoShare: 'nessuna pubblicazione | 1 pubblicazione | {count} pubblicazioni',
  },

  mount: {
    stato: 'Stato',
    gestisci: 'Apri e configura',
    titolo: 'Condivisioni NFS',
    sottotitolo:
      'Passo 1. Monta le cartelle del NAS sul server. Montata non vuol dire raggiungibile: per quello serve una pubblicazione.',
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
    pubblicaQuesta: 'Pubblica questa cartella',
    giaPubblicata: 'nessuna pubblicazione | 1 pubblicazione | {count} pubblicazioni',
    monta: 'Monta',
    smonta: 'Smonta',
    rileggi: 'Rileggi stato',
    statoMontato: 'Montato',
    statoSmontato: 'Non montato',
    statoErrore: 'Errore',
    statoInCorso: 'Operazione in corso…',
    statoConfigurato: 'Configurato',
    scritturaNegata: 'Il NAS sta negando la scrittura.',
    scritturaNegataDettaglio:
      'Hai richiesto lettura e scrittura, ma la condivisione risulta in sola lettura. Va abilitata anche nei permessi NFS della cartella sul NAS.',
    confermaTitolo: 'Eliminare «{nome}»?',
    confermaTesto:
      'La condivisione viene smontata e la sua configurazione rimossa dal server. I file sul NAS non vengono toccati.',
  },

  nuovoMount: {
    gruppoNome: 'Come chiamarla',
    gruppoNomeAiuto: 'Serve a riconoscerla nel pannello. Non è ancora un indirizzo pubblico: quello nasce dalla pubblicazione.',
    gruppoMontaggio: 'Come montarla',
    gruppoMontaggioAiuto: 'Versione del protocollo e comportamento del montaggio. In caso di dubbio lascia i valori proposti.',
    identificatore: 'Identificatore',
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
    versioneNfs: 'Versione NFS',
    montaARichiesta: 'Monta alla prima richiesta',
    consentiScrittura: 'Consenti la scrittura',
    consentiScritturaDettaglio:
      'Il pannello potrà modificare ed eliminare file sul NAS. Va abilitata anche nei permessi NFS della cartella condivisa, altrimenti resterà in sola lettura.',
    creando: 'Creo…',
  },

  condivisione: {
    panoramica: 'Panoramica',
    montaggio: 'Montaggio',
    pubblicazioni: 'Cartelle pubblicate',
    avanzate: 'Avanzate',
    salvato: 'Modifiche salvate',
    apri: 'Apri',
    gestisci: 'Permessi e link',
    nessunaPubblicazione:
      'Questa condivisione non pubblica ancora nessuna cartella, quindi non è raggiungibile da nessuno.',
    zonaPericolosa: 'Rimozione',
    zonaPericolosaAiuto:
      'Toglie la condivisione dal pannello e smonta la cartella. I file sul NAS non vengono toccati.',
    haPubblicazioni:
      'Attenzione: {n} cartella pubblicata smetterà di funzionare. | Attenzione: {n} cartelle pubblicate smetteranno di funzionare.',
    confermaEliminazione:
      'La cartella viene smontata e la condivisione tolta dal pannello. Sul NAS non viene eliminato niente.',
  },

  share: {
    gestisci: 'Apri e configura',
    gruppoNascosti: 'Cosa non mostrare',
    gruppoNascostiAiuto:
      'I NAS creano cartelle proprie — il cestino, le miniature — che non sono contenuto da pubblicare. Un nome per riga; si possono usare * e ?. Svuota per mostrare tutto.',
    nascosti: 'Nomi da nascondere',
    origineAvviso:
      'Cambiando l’origine, allo stesso indirizzo si troverà un altro contenuto. Permessi, regole e link restano al loro posto.',
    gruppoCosa: 'Quale cartella',
    gruppoCosaAiuto: 'Da quale condivisione NFS, e quale parte di essa.',
    gruppoNome: 'Come si chiama',
    gruppoNomeAiuto: 'Il nome che leggi nel pannello, e quello che finisce nell’indirizzo pubblico.',
    gruppoAccesso: 'Chi può accedere',
    gruppoAccessoAiuto: 'Vale per l’intera pubblicazione. Dopo potrai fare eccezioni per singola sottocartella.',
    modifica: 'Modifica',
    modificaTitolo: 'Modifica «{nome}»',
    identificatoreAvviso:
      'Cambiandolo, l’indirizzo pubblico cambia: i collegamenti già condivisi smetteranno di funzionare.',
    attivaAzione: 'Attiva',
    disattivaAzione: 'Disattiva',
    identificatore: 'Nome nell’indirizzo',
    identificatoreAiuto:
      'Lo scegli tu. Viene proposto dal nome, ma puoi riscriverlo: lettere, numeri, - e _.',
    anteprimaIndirizzo: 'Sarà raggiungibile qui:',
    titolo: 'Pubblicazioni',
    sottotitolo:
      'Passo 2. Decidi quali cartelle montate sono raggiungibili dal web, con che nome e da chi. È qui che nasce l’indirizzo da condividere.',
    nuova: 'Nuova pubblicazione',
    vuoto:
      'Nessuna cartella pubblicata. Una pubblicazione parte da una condivisione NFS già montata.',
    servonoMount:
      'Prima serve almeno una condivisione NFS montata: una pubblicazione parte da lì.',
    daCondividere: 'Indirizzo da condividere',
    cortoNota: 'Indirizzo breve, da dettare o scrivere a mano. Funziona solo con Apache.',
    completoNota: 'Indirizzo completo: è qui che quello breve fa arrivare.',
    copia: 'Copia',
    copiato: 'Copiato',
    condivisione: 'Condivisione',
    sottopercorso: 'Sottocartella',
    sottopercorsoAiuto: 'Vuoto per pubblicare la radice della condivisione',
    nome: 'Nome',
    descrizione: 'Descrizione',
    visibilitaPredefinita: 'Chi può accedere',
    attiva: 'Pubblicazione attiva',
    disattivata: 'Disattivata',
    creando: 'Creo…',
    confermaTitolo: 'Eliminare «{nome}»?',
    confermaTesto:
      'La pubblicazione, le sue regole e i permessi vengono rimossi. I file sul NAS non vengono toccati.',
  },

  pubblicazione: {
    indirizzo: 'Indirizzo e nome',
    accesso: 'Chi accede',
    contenuto: 'Contenuto',
    rimozioneAiuto:
      'Toglie la pubblicazione: l’indirizzo smette di rispondere e i link creati non funzionano più. La cartella sul NAS non viene toccata.',
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

  scegliCartella: {
    risali: 'Sali di un livello',
    scendi: 'Entra in una sottocartella…',
    nessuna: 'Nessuna sottocartella qui',
    nonLeggibile: 'Cartella non leggibile',
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
    notaMultipla: 'Tieni premuto Ctrl (o Cmd) per selezionarne più di uno.',
    nessunUtente: 'Nessun utente da scegliere: creane uno dalla voce Utenti.',
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
    barraDelBrowser:
      'Per togliere anche la barra del browser: condividi ▸ «Aggiungi a Home». Da lì il pannello si apre come un’applicazione, senza barre. Da una scheda del browser nessuna pagina può nasconderla.',
    aggiornamento: 'È disponibile una versione aggiornata del pannello.',
    ricarica: 'Aggiorna',
    prontoOffline: 'Il pannello ora funziona anche senza rete.',
  },

  impostazioni: {
    titolo: 'Impostazioni',
    descrizione: 'Aspetto del pannello e spazio sui dischi.',
    marchio: 'Marchio',
    nome: 'Nome del pannello',
    sottotitolo: 'Sottotitolo (facoltativo)',
    logo: 'Logo (indirizzo di un’immagine)',
    logoNota: 'Se indicato sostituisce il nome nella barra laterale.',
    nascosti: 'Mostra anche i file che iniziano con un punto',
    nascostiNota:
      'I caricamenti a metà restano comunque invisibili: non sono file, e mostrarli li farebbe sembrare scaricabili.',
    salvato: 'Salvato',
    spazio: 'Spazio sui dischi',
    discoPannello: 'Disco del pannello',
    liberi: '{libero} liberi',
    nonRaggiungibile: 'non raggiungibile',
  },

  trasferimenti: {
    titolo: 'Trasferimenti',
    descrizione: 'Cosa è stato scaricato e caricato, da chi e da dove.',
    dalVivo: 'Aggiornamento dal vivo',
    fermo: 'Aggiornamento fermo',
    nessuno: 'Nessun trasferimento registrato.',
    riepilogo: '{n} trasferimenti, {corso} in corso',
    quando: 'Quando',
    cosa: 'Cosa',
    file: 'File',
    dimensione: 'Dimensione',
    trasferiti: 'Trasferiti',
    da: 'Indirizzo',
    stato: 'Stato',
    download: 'Scaricamento',
    upload: 'Caricamento',
    ripresa: 'ripresa',
    stato_in_corso: 'in corso',
    stato_completato: 'completato',
    stato_interrotto: 'interrotto',
    stato_fallito: 'fallito',
    notaByte:
      'I byte trasferiti li scrive il web server nel suo log: compaiono solo se quel log è indicato nella configurazione (ANF_ACCESS_LOG). Finché non ci sono restano vuoti, perché un numero inventato sarebbe peggio di uno assente.',
  },

  utenti: {
    titolo: 'Utenti',
    descrizione:
      'Chi può accedere al pannello e cosa può fare in generale. In quali cartelle lo può fare si decide nella pubblicazione.',
    nuovo: 'Nuovo utente',
    amministratore: 'Amministratore',
    rendiAdmin: 'Rendi amministratore',
    togliAdmin: 'Togli amministratore',
    attiva: 'Attiva',
    disattiva: 'Disattiva',
    disattivato: 'Disattivato',
    sonoIo: 'sei tu',
    permessi: 'Permessi generali',
    passwordMinima: 'Almeno 10 caratteri.',
    ambito: 'Ambito',
    ambitoVuoto: 'nessun limite',
    ambitoNota: 'Cartella oltre la quale questo utente non può uscire. Vuoto = nessun limite.',
    can_download: 'Scaricare',
    can_upload: 'Caricare',
    can_create: 'Creare cartelle',
    can_rename: 'Rinominare',
    can_modify: 'Modificare',
    can_delete: 'Eliminare',
    can_share: 'Creare link',
    confermaTitolo: 'Eliminare «{nome}»?',
    confermaTesto:
      'L’utente e i permessi che gli sono stati assegnati vengono eliminati. I file non vengono toccati.',
  },

  webserver: {
    titolo: 'Web server',
    descrizione:
      'Serve a rendere il pannello raggiungibile su un altro nome host — per esempio archivio.tuodominio.it — oltre a quello configurato durante l’installazione. Non serve a niente altro: se ti basta l’indirizzo che usi adesso, questa pagina puoi ignorarla.',
    comeFunziona:
      'Il pannello scrive un file di configurazione per il web server, lo prova con il suo stesso comando di verifica, e solo se il test passa lo applica. Se non passa, la configurazione precedente torna al suo posto: un errore qui fermerebbe tutti i siti ospitati sulla macchina, non solo questo.',
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
    titolo: 'Link temporanei',
    descrizione:
      'Diverso dall’indirizzo della pubblicazione qui sopra, che è fisso e vale per tutti: questo è un collegamento usa-e-getta per chi non ha un account. Vale solo per la cartella indicata, e può scadere dopo un certo numero di giorni o di scaricamenti.',
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

  anteprima: {
    presentazione: 'Presentazione',
    datiScatto: 'Dati dello scatto',
    quando: 'Scattata il',
    fotocamera: 'Fotocamera',
    obiettivo: 'Obiettivo',
    esposizione: 'Esposizione',
    dimensioni: 'Dimensioni',
    luogo: 'Luogo',
    vediSullaMappa: 'Vedi sulla mappa',
    schermoIntero: 'Schermo intero',
    posizione: '{n} di {tot}',
    precedente: 'Immagine precedente',
    successiva: 'Immagine successiva',
    nonMostrabile: 'Questo tipo di file non si può mostrare qui: scaricalo per aprirlo.',
    modifica: 'Modifica il testo',
    salvato: 'Salvato',
    troncato: 'Il file è troppo grande: ne vedi solo l’inizio, e salvare perderebbe il resto.',
    impronta: 'Calcola impronta SHA-256',
    improntaNota:
      'Confrontala con quella del file di partenza per essere certo che sia arrivato identico.',
  },

  selezione: {
    scegli: 'Seleziona {nome}',
    scelti: 'nessun elemento | 1 elemento scelto | {n} elementi scelti',
    scarica: 'Scarica insieme',
    azzera: 'Deseleziona',
  },

  ricerca: {
    campo: 'Cerca in questa cartella…',
    cerca: 'Cerca',
    azzera: 'Azzera',
    esito: 'nessun risultato | 1 risultato | {n} risultati',
    troncata: 'ci sono altri risultati: restringi la ricerca',
  },

  caricamento: {
    trascina: 'Trascina qui i file da caricare',
    scegli: 'Scegli dal dispositivo',
    scegliCartella: 'Scegli una cartella',
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

  fstab: {
    titolo: 'Montaggi già presenti sul sistema',
    descrizione:
      'Righe NFS trovate in /etc/fstab. Importandole le gestisce il pannello, senza doverle riscrivere a mano.',
    importa: 'Importa',
    giaGestito: 'Gestito dal pannello',
    disattiva: 'Commenta la riga in fstab',
    solaLettura: 'sola lettura',
    notaDisattiva:
      'Fallo solo dopo aver verificato che il mount del pannello funzioni: finché entrambi sono attivi il sistema prova a montare due volte lo stesso percorso.',
    disattivata: 'Riga commentata. Copia di sicurezza del file: {copia}',
    nonDisponibile:
      'Non riesco a leggere /etc/fstab: il servizio di sistema non risponde.',
  },

  accessoCartella: {
    utenteFacoltativo: 'Nome utente (solo se ne hai uno)',
    serveNomeUtente: 'Per questa cartella serve un account: indica il nome utente.',
    titolo: 'Cartella protetta',
    servePassword: 'Per aprirla serve la parola d’ordine che ti è stata data.',
    serveAccount: 'Per aprirla serve un account su questo pannello.',
    entra: 'Entra',
    credenzialiErrate: 'Nome utente o password non corretti.',
  },

  archivio: {
    comandiNelMenu: 'Tocca a lungo, o tasto destro, per rinominare, spostare ed eliminare.',
    senzaData: 'Senza data',
    apriCartella: 'Apri',
    vediAnteprima: 'Anteprima',
    vista: 'Vista',
    vistaElenco: 'Elenco',
    vistaGriglia: 'Griglia',
    vistaGalleria: 'Miniature',
    azioniSu: 'Azioni su {nome}',
    titolo: 'Archivio',
    apri: 'Sfoglia',
    percorso: 'Percorso',
    radice: 'Inizio',
    scarica: 'Scarica',
    scaricaCartella: 'Scarica cartella',
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
    generico: 'Errore imprevisto.',
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
