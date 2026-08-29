/** English translations. Mirrors the Italian file key by key. */

export default {
  comune: {
    annulla: 'Cancel',
    salva: 'Save',
    crea: 'Create',
    elimina: 'Delete',
    chiudi: 'Close',
    esci: 'Sign out',
    carico: 'Loading…',
    amministratore: 'administrator',
    lingua: 'Language',
  },

  tema: {
    titolo: 'Theme',
    chiaro: 'Light',
    auto: 'Automatic',
    scuro: 'Dark',
  },

  menu: {
    archivio: 'Storage',
    accessi: 'Access',
    sistema: 'System',
    condivisioni: 'NFS shares',
    pubblicazioni: 'Published folders',
    file: 'Files',
    utenti: 'Users',
    link: 'Share links',
    stato: 'Status',
    trasferimenti: 'Transfers',
    impostazioni: 'Settings',
    apri: 'Open the menu',
    inArrivo: 'Available in {fase}',
    fase: 'phase {n}',
  },

  accesso: {
    titolo: 'Sign in',
    utente: 'Username',
    password: 'Password',
    inCorso: 'Signing in…',
    credenzialiErrate: 'Wrong username or password.',
    erroreImprevisto: 'Unexpected error while signing in.',
  },

  home: {
    sottotitolo:
      'Mount NFS shares, publish folders with per-subfolder permissions, manage your files.',
    servizioAttivo: 'Service running',
    servizioNonRaggiungibile: 'Service unreachable',
    passwordIniziale: 'You are still using the initial password.',
    passwordInizialeDettaglio: 'Change it before exposing the panel to the internet.',
    vaiCondivisioni: 'Go to shares',
    condivisioniDescrizione:
      'Mount your NAS folders from the panel, without touching configuration files: the system reads the list of available folders from the NAS and mounts them for you.',
    inArrivoTitolo: 'Coming next',
    inArrivoDescrizione:
      'Publishing folders with per-subfolder permissions arrives in phase 2, file management in phase 3.',
  },

  mount: {
    titolo: 'NFS shares',
    sottotitolo: 'Mount your NAS folders without touching configuration files.',
    nuova: 'New share',
    vuoto:
      'No share configured yet. Start with “New share”: the panel reads the list of available folders straight from the NAS.',
    percorso: 'Mount point',
    versione: 'Version',
    accessoRichiesto: 'Requested access',
    accessoEffettivo: 'Actual access',
    solaLettura: 'Read only',
    letturaScrittura: 'Read and write',
    nonRilevato: 'Not detected',
    monta: 'Mount',
    smonta: 'Unmount',
    rileggi: 'Refresh status',
    statoMontato: 'Mounted',
    statoSmontato: 'Not mounted',
    statoErrore: 'Error',
    statoConfigurato: 'Configured',
    scritturaNegata: 'The NAS is denying write access.',
    scritturaNegataDettaglio:
      'You requested read and write, but the share is mounted read only. It must be allowed on the NAS too, in the NFS permissions of the shared folder.',
    confermaTitolo: 'Delete “{nome}”?',
    confermaTesto:
      'The share is unmounted and its configuration removed from the server. Files on the NAS are left untouched.',
  },

  nuovoMount: {
    titolo: 'New share',
    indirizzoNas: 'NAS address',
    cerca: 'Find shares',
    cercando: 'Searching…',
    consentitoA: 'allowed to {client}',
    nessunaEsportazione:
      'The NAS answers but exports nothing to this server. Check the NFS permissions of the shared folder.',
    soloVersioni:
      'This NAS only offers NFS {versioni}: version 4 is unavailable, and asking for it would make the mount fail.',
    nome: 'Name',
    identificatore: 'Identifier',
    versioneNfs: 'NFS version',
    montaARichiesta: 'Mount on first access',
    consentiScrittura: 'Allow writing',
    consentiScritturaDettaglio:
      'The panel will be able to modify and delete files on the NAS. It must also be allowed in the NFS permissions of the shared folder, otherwise the share stays read only.',
    creando: 'Creating…',
  },

  share: {
    titolo: 'Published folders',
    sottotitolo: 'Decide which folders are reachable, and by whom.',
    nuova: 'New publication',
    vuoto: 'No folder published yet. A publication starts from an NFS share already mounted.',
    servonoMount: 'You need at least one mounted NFS share first: a publication starts from there.',
    condivisione: 'NFS share',
    sottopercorso: 'Subfolder',
    sottopercorsoAiuto: 'Leave empty to publish the root of the share',
    nome: 'Name',
    identificatore: 'Identifier',
    descrizione: 'Description',
    visibilitaPredefinita: 'Who can access',
    attiva: 'Publication enabled',
    disattivata: 'Disabled',
    creando: 'Creating…',
    confermaTitolo: 'Delete “{nome}”?',
    confermaTesto:
      'The publication, its rules and its permissions are removed. Files on the NAS are left untouched.',
  },

  visibilita: {
    pubblica: 'Anyone, without signing in',
    password: 'Anyone with the password',
    utenti: 'Every signed-in user',
    utenti_scelti: 'Only authorised users',
    negata: 'Nobody',
    breve_pubblica: 'Public',
    breve_password: 'Password',
    breve_utenti: 'Users',
    breve_utenti_scelti: 'Authorised',
    breve_negata: 'Denied',
  },

  regole: {
    titolo: 'Rules per folder',
    descrizione:
      'Each rule covers one folder and everything inside it. The most specific rule always wins, so a subfolder can be stricter than the folder containing it.',
    percorso: 'Folder',
    radice: 'the whole publication',
    aggiungi: 'Add rule',
    password: 'Password',
    protetta: 'password protected',
    nessuna: 'No rule: the publication default applies.',
  },

  permessi: {
    titolo: 'Per-user permissions',
    descrizione:
      'Decide which user reaches which folder, or all of them. An explicit denial beats the folder rule, so you can take a branch away from one person while leaving it open to everyone else.',
    utente: 'User',
    cartella: 'Folder',
    livello: 'Permission',
    negato: 'Denied',
    lettura: 'Read',
    scrittura: 'Read and write',
    assegna: 'Assign',
    nessuno: 'No permission assigned.',
    tutte: 'all folders',
  },

  prova: {
    titolo: 'Check an access',
    descrizione:
      'See whether a folder is reachable and which rule decides it, before your users find out for you.',
    percorso: 'Folder to check',
    come: 'As',
    anonimo: 'Anonymous visitor',
    verifica: 'Check',
    consentito: 'Access allowed',
    negato: 'Access denied',
    conScrittura: 'with write access',
    decisoDaRegola: 'decided by the rule on “{percorso}”',
    decisoDaPermesso: 'decided by the permission on “{percorso}”',
    decisoDaPredefinita: 'decided by the publication default',
  },

  pwa: {
    aggiornamento: 'A new version of the panel is available.',
    ricarica: 'Update',
    prontoOffline: 'The panel now works offline too.',
  },

  archivio: {
    titolo: 'Files',
    apri: 'Browse',
    percorso: 'Path',
    radice: 'Top',
    scarica: 'Download',
    vuota: 'This folder is empty.',
    passwordRichiesta: 'This path is protected by a password.',
    sblocca: 'Open',
  },

  errori: {
    serverNonRaggiungibile: 'Server unreachable. Check your connection.',
    sessioneScaduta: 'Session expired. Please sign in again.',
    permessiMancanti: 'You do not have permission for this operation.',
    nonTrovato: 'Resource not found.',
    conflitto: 'The operation conflicts with the current state.',
    erroreServer: 'Server error.',
    richiestaNonValida: 'Invalid request.',
    imprevisto: 'Unexpected error.',
  },

  nonTrovata: {
    titolo: 'Page not found',
    testo: 'The requested address does not exist in this panel.',
    torna: 'Back to the panel',
  },

  piede: {
    attribuzione: 'Designed and developed by {autore}',
  },
}
