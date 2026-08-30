# anf-agent — agent privilegiato

*[English version](README.en.md)*

Questo è l'unico componente che gira da **root**. Per questo motivo è tenuto
deliberatamente minimale: nessuna dipendenza esterna, solo la libreria standard di
Python.

## Regole non negoziabili

1. **Nessuna dipendenza esterna.** Ogni pacchetto in più è superficie di attacco in
   più su un processo root.
2. **Mai una stringa di shell.** Si passano sempre liste di argomenti, mai
   `shell=True`. Ogni comando ha un timeout e un ambiente ridotto al minimo
   (`comandi.py` è l'unico punto del progetto che lancia processi esterni).
3. **Insieme chiuso di verbi.** Nessun verbo generico, nessun "esegui questo".
4. **Confinamento dei percorsi.** Il punto di montaggio non arriva mai dall'API: si
   ricava dallo slug validato e resta sotto `ANF_MOUNT_ROOT`.
5. **Whitelist delle opzioni di mount.** Un'opzione non prevista è un errore, non un
   valore da inoltrare al kernel.
6. **Solo le proprie unit.** L'agent non tocca file che non riportino il proprio
   marcatore, quindi non può danneggiare configurazioni di terzi.
7. **Si rifiuta di partire senza root**, invece di degradare in silenzio.

## Comunicazione

Socket Unix, permessi `0660`, proprietario `root`, gruppo dell'applicazione. Un
messaggio JSON per riga, una risposta per riga. L'agent **non apre porte di rete**:
l'unit systemd lo esegue con `PrivateNetwork=yes`.

```json
→ {"verbo": "nfs.discover", "dati": {"server": "192.168.1.10"}}
← {"ok": true, "risultato": {"esportazioni": [...], "versioni": ["2", "3"]}}
← {"ok": false, "codice": "validazione", "errore": "Opzione non consentita: 'exec'"}
```

## Verbi

| Verbo | Dati | Restituisce |
|---|---|---|
| `ping` | — | conferma che l'agent risponde |
| `nfs.discover` | `server` | condivisioni esportate e versioni NFS disponibili |
| `mount.create` | `slug`, `server`, `export_path`, `nfs_version`, `automount`, `idle_timeout`, `opzioni` | mountpoint e unit generate |
| `mount.start` | `slug`, `automount` | stato dopo l'avvio |
| `mount.stop` | `slug` | stato dopo l'arresto |
| `mount.remove` | `slug` | unit rimosse |
| `mount.status` | `slug` | stato reale del montaggio |
| `mount.list` | — | tutti i mount gestiti, con il loro stato |

## Stato richiesto e stato effettivo

`mount.status` non deduce nulla dalla configurazione: legge il sistema con `findmnt`
e, se il mount è attivo, **prova a scrivere** un file temporaneo. È l'unico modo per
sapere davvero se la scrittura è possibile: le opzioni dicono cosa ha chiesto il
client, ma il NAS può negarla per conto suo.

Due dettagli che sembrano cavilli e non lo sono:

- con `x-systemd.automount` il filesystem viene montato **al primo accesso**, quindi
  lo stato tocca il percorso prima di leggerlo — altrimenti riporterebbe sempre
  "non montato";
- un percorso sotto automount compare in `findmnt` prima come `autofs` e solo dopo
  come `nfs`: si leggono entrambe le voci e vale la seconda.

## Codici di errore

`verbo_sconosciuto`, `richiesta_malformata`, `validazione`, `non_trovato`,
`comando_fallito`, `timeout`, `interno`. Servono all'API per reagire in modo diverso:
un errore di validazione è un difetto del pannello, un `comando_fallito` è un problema
del sistema o del NAS.

## Struttura

```
anf_agent/
├── __main__.py      avvio, lettura dell'ambiente, controllo dei privilegi
├── server.py        socket Unix, smistamento dei verbi
├── protocol.py      messaggi tipizzati, verbi ammessi, codici di errore
├── validators.py    barriera di sicurezza: slug, percorsi, opzioni
├── comandi.py       unico punto che lancia processi esterni
├── systemd_units.py generazione e rimozione delle unit .mount / .automount
└── nfs.py           scoperta delle esportazioni, stato reale, prova di scrittura
```

## Configurazione

| Variabile | Predefinito | Cosa fa |
|---|---|---|
| `ANF_AGENT_SOCKET` | `/run/anf/agent.sock` | socket di ascolto |
| `ANF_MOUNT_ROOT` | `/srv/nas` | radice oltre la quale non si monta nulla |
| `ANF_AGENT_GROUP` | `anf` | gruppo che può parlare con l'agent |
| `ANF_LOG_LEVEL` | `INFO` | livello di registrazione |
