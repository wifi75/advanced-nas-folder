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
