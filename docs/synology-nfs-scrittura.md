# Abilitare la scrittura NFS su Synology

🇬🇧 [English version](synology-nfs-scrittura.en.md)

Advanced NAS Folder crea ogni mount **in sola lettura**. È una scelta deliberata: un
pannello raggiungibile da Internet che può scrivere sul NAS è un rischio molto diverso
da uno che può solo leggere.

Se ti serve caricare file dal pannello, la scrittura va abilitata **su due lati**.
Abilitarla solo nel pannello non basta: il NAS continuerà a rifiutare le scritture, e
il pannello te lo segnalerà mostrando *stato richiesto: lettura-scrittura — stato
effettivo: sola lettura*.

---

## 1. Lato NAS (DSM)

1. **Pannello di controllo → Cartella condivisa**
2. Seleziona la cartella e premi **Modifica**
3. Scheda **Permessi NFS**
4. Seleziona la regola del server e premi **Modifica** (o **Crea** se non esiste)

Imposta:

| Campo | Valore | Nota |
|---|---|---|
| **Nomehost o IP** | l'indirizzo del server | mai `*`: limita sempre a un host singolo |
| **Privilegi** | `Lettura/Scrittura` | è la voce che sblocca la scrittura |
| **Squash** | vedi sotto | **la scelta più importante** |
| **Sicurezza** | `sys` | |
| Consenti connessioni da porte senza privilegi | ✅ | necessario per i mount non-root |
| Consenti agli utenti di accedere alle sottocartelle montate | ✅ | serve se monti una sottocartella |

Premi **Salva** su entrambe le finestre.

### Lo squash: il campo che si sbaglia più spesso

Lo *squash* decide **di chi sono i file** che il server scrive sul NAS. Sbagliarlo non
dà errori: i file vengono creati, ma con un proprietario tale che poi non riesci più a
gestirli da File Station o via SMB.

| Impostazione | Effetto |
|---|---|
| `Nessuna mappatura` | i file mantengono l'UID del server. È l'opzione corretta **se** gli UID coincidono fra server e NAS — quasi mai. |
| `Mappa tutti gli utenti su admin` | tutti i file risultano di `admin`. Comodo, gestibile da DSM, ma il server ottiene di fatto i privilegi di admin sulla condivisione. |
| `Mappa tutti gli utenti su guest` | i file risultano di `guest`. Più sicuro, ma su alcune configurazioni `guest` non ha permesso di scrittura nella cartella e le scritture falliscono. |

**Consiglio:** parti da `Mappa tutti gli utenti su admin`, verifica che l'upload
funzioni e che i file si vedano correttamente in File Station. Se ti serve un
isolamento maggiore, passa a `guest` e verifica di nuovo — controllando prima che
`guest` abbia i permessi di scrittura nella scheda **Autorizzazioni** della cartella.

---

## 2. Lato pannello

1. Apri il mount in **Mount → Modifica**
2. Attiva **Consenti scrittura**
3. Conferma l'avviso di rischio
4. Il pannello rimonta la condivisione e rilegge lo stato effettivo

Se dopo il rimontaggio lo stato effettivo resta `sola lettura`, la regola sul NAS non è
stata applicata: ricontrolla che l'indirizzo nella regola NFS corrisponda esattamente
a quello del server.

---

## Verifica dalla riga di comando

Sul server, per vedere come è montata davvero la condivisione:

```bash
findmnt -t nfs -o TARGET,SOURCE,OPTIONS
```

Cerca `ro` o `rw` all'inizio delle opzioni. Per una prova concreta di scrittura:

```bash
touch /srv/nas/<nome-mount>/.prova-scrittura && rm /srv/nas/<nome-mount>/.prova-scrittura && echo "scrittura OK"
```

Per vedere quali condivisioni il NAS esporta e verso quali host:

```bash
showmount -e <indirizzo-del-nas>
```

---

## Se il mount fallisce con `Protocol not supported`

Non è un problema di permessi ma di versione del protocollo: la configurazione sta
chiedendo NFSv4 mentre il NAS espone solo la v3. Verifica quali versioni sono
disponibili:

```bash
rpcinfo -p <indirizzo-del-nas> | grep nfs
```

Se compaiono solo le versioni `2` e `3`, imposta `vers=3` nelle opzioni del mount —
oppure abilita NFSv4.1 in **Pannello di controllo → Servizi file → NFS** su DSM.

Per un mount in sola lettura in LAN la v3 va benissimo: l'unico vantaggio pratico
della v4.1 in questo scenario è non dipendere da `rpcbind`/`rpc-statd`, e lo si ottiene
già con l'opzione `nolock`.
