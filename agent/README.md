# anf-agent — agent privilegiato

Questo è l'unico componente che gira da **root**. Per questo motivo è tenuto
deliberatamente minimale.

## Regole non negoziabili

1. **Nessuna dipendenza esterna.** Solo libreria standard di Python. Ogni pacchetto in
   più è superficie di attacco in più su un processo root.
2. **Mai una stringa di shell.** L'agent riceve campi tipizzati e li sostituisce in
   template. Non esiste un punto in cui input dell'utente venga concatenato in un
   comando.
3. **Insieme chiuso di verbi.** `mount.create`, `mount.start`, `mount.stop`,
   `mount.remove`, `mount.status`, `nfs.discover`, `vhost.apply`, `vhost.remove`.
   Nessun verbo generico, nessun "esegui questo".
4. **Confinamento dei percorsi.** Ogni mountpoint è forzato sotto `ANF_MOUNT_ROOT`.
   Percorsi normalizzati, `..` rifiutati.
5. **Whitelist delle opzioni di mount.** Un'opzione non prevista è un errore, non un
   valore da passare al kernel.
6. **Verifica prima di applicare.** Ogni modifica alla configurazione del web server
   passa da `apache2ctl configtest` / `nginx -t` prima del reload, con ripristino
   automatico della versione precedente se il test fallisce.

## Comunicazione

Socket Unix, permessi `0660`, proprietario `root`, gruppo dell'applicazione. L'agent
non apre porte di rete: l'unit systemd lo esegue con `PrivateNetwork=yes`.

## Struttura prevista

```
anf_agent/
├── __main__.py      avvio, gestione del socket
├── protocol.py      definizione dei messaggi tipizzati
├── validators.py    confinamento percorsi, whitelist opzioni
├── nfs.py           scoperta degli export, montaggio
├── systemd_units.py generazione delle unit .mount / .automount
└── webserver.py     vhost, configtest, ripristino
```

Implementazione prevista in **fase 1**. Vedere [../TODO.md](../TODO.md).
