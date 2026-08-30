# Guida all'uso

Come si usa Advanced NAS Folder, dal punto di vista di chi ci lavora dentro.
Per installarlo vedere [INSTALL.md](INSTALL.md).

*[English version](GUIDA.en.md)*

---

## In due parole

Il pannello fa tre cose, in quest'ordine:

1. **monta** le cartelle del NAS sul server, senza toccare file di configurazione;
2. **pubblica** quelle cartelle decidendo chi può vederle;
3. **serve** i file a chi ha il diritto di scaricarli.

Le tre cose sono separate di proposito: una condivisione montata non è
raggiungibile da nessuno finché non la si pubblica, e una pubblicazione non
dice nulla su *come* il NAS è collegato.

---

## Primo accesso

L'installazione crea un solo utente, `admin`, con password `Admin1234`. Il pannello
lo dice a ogni accesso finché non la si cambia: **Utenti → il proprio nome →
cambia password**, oppure dalla pagina di accesso.

Finché quella password è quella iniziale, il pannello non va reso raggiungibile
da Internet.

---

## I tre passi, in quest'ordine

È la cosa che più spesso non è chiara, quindi vale la pena dirla prima di tutto
il resto:

| | Cosa fa | Cosa **non** fa |
|---|---|---|
| **1. Condivisioni NFS** | monta una cartella del NAS **sul server** | non la rende raggiungibile da nessuno |
| **2. Pubblicazioni** | decide quale cartella è raggiungibile dal web, con che nome e da chi | non copia né sposta niente |
| **3. Archivio** | è dove si sfoglia e si scarica quello che è stato pubblicato | |

Senza il passo 1 il passo 2 non è possibile: una pubblicazione parte sempre da
una cartella già montata. E **una cartella montata ma non pubblicata non è
raggiungibile da nessuno**, nemmeno da un amministratore: sta solo sul server.

L'indirizzo da condividere nasce al passo 2, e il pannello lo mostra per esteso
accanto a ogni pubblicazione, pronto da copiare.

---

## Montare una cartella del NAS

**Condivisioni NFS → Nuova condivisione.**

Si indica l'indirizzo del NAS e il pannello chiede al NAS stesso quali cartelle
esporta: si sceglie da un elenco invece di digitare un percorso a memoria.

Tre cose da sapere:

- **La sola lettura è il valore predefinito.** Concedere la scrittura è una
  scelta separata, e va fatta anche sul NAS: il pannello può chiederla, ma se
  la regola NFS del NAS non la concede il mount resta in sola lettura. Quando
  succede, il pannello lo dice invece di far scoprire il problema al primo
  caricamento. Come configurarla sul Synology: [synology-nfs-scrittura.md](synology-nfs-scrittura.md).
- **Il montaggio su richiesta è acceso.** La cartella viene montata quando
  qualcuno la usa e smontata dopo un po' che nessuno la tocca. Un NAS spento
  di notte non fa quindi bloccare il server.
- **Se hai già dei mount in `/etc/fstab`**, il pannello li trova da solo e
  propone di importarli. Dopo averli importati *e verificati*, si può
  commentare la vecchia riga dalla stessa schermata: prima no, perché finché
  entrambi sono attivi il sistema prova a montare due volte lo stesso percorso.

---

## Pubblicare una cartella

**Pubblicazioni → Nuova pubblicazione.**

Una pubblicazione è una cartella del NAS resa raggiungibile a un indirizzo, con
un nome breve che scegli tu.

### L'indirizzo da condividere

Ogni pubblicazione mostra **due indirizzi**, entrambi con un pulsante per
copiarli. Portano allo stesso posto:

| | Esempio | Quando usarlo |
|---|---|---|
| **Corto** | `https://tuo-dominio/documenti` | da dettare o scrivere a mano. Solo con Apache |
| **Completo** | `https://tuo-dominio/pannello/archivio/documenti` | sempre valido, anche con Nginx |

Il corto è una redirezione verso il completo: funziona ovunque tu lo scriva, ma
il browser mostra poi quello lungo nella barra.

Se la visibilità è *Chiunque, anche senza accedere*, l'indirizzo funziona per
chi lo riceve senza che debba avere un account. Se invece vuoi dare accesso a
**una persona sola**, senza aprire la cartella a tutti, non condividere questo
indirizzo: usa un **link di condivisione**, che scade e si può revocare.

### Chi può vederla

La **visibilità** si sceglie a parole, non con termini tecnici:

| Scelta | Chi entra |
|---|---|
| Chiunque, anche senza accedere | tutti, compreso chi non ha un account |
| Chi conosce la password | chi ha la password di quella cartella |
| Tutti gli utenti autenticati | chiunque abbia un account sul pannello |
| Solo gli utenti autorizzati | solo chi ha un permesso esplicito su quel percorso |
| Nessuno | nessuno, **nemmeno gli amministratori** |

La visibilità si può cambiare **per singola sottocartella**: vince sempre la
regola più specifica. Una cartella pubblica può contenerne una riservata, e
viceversa.

### Chi può fare cosa

Accanto alle regole ci sono i **permessi per utente**: «questa cartella la vede
solo Mario». Anche qui vince il prefisso più lungo, e un permesso *Negato*
batte la regola della cartella — è il modo di togliere a una persona un ramo
che per tutti gli altri resta aperto.

### Verificare prima che lo scoprano gli utenti

Nella stessa pagina c'è **Verifica un accesso**: si scrive un percorso, si
sceglie un utente (o si lascia vuoto per provare un visitatore anonimo), e il
pannello risponde dicendo **quale regola ha deciso**. È il modo di accorgersi
di un permesso sbagliato prima che se ne accorga qualcun altro.

---

## Sfogliare, scaricare, caricare

Da **Pubblicazioni → Sfoglia**, oppure direttamente all'indirizzo della
pubblicazione.

- **Scaricare** un file: il pulsante *Scarica*. Se il download si interrompe,
  il browser lo riprende da dove era arrivato — non riparte da capo.
- **Scaricare una cartella intera**: *Scarica cartella*, che produce uno ZIP
  mentre lo invia. Il browser non mostra la percentuale, perché la dimensione
  totale non è nota in anticipo.
- **Scaricare più cose insieme**: si spuntano le caselle e si usa *Scarica
  insieme*.
- **Caricare**: si trascinano i file nella zona tratteggiata, o si sceglie una
  cartella intera. Il caricamento avviene a blocchi: se si interrompe, riprende
  da dove era arrivato anche il giorno dopo.
- **Cercare**: la casella in alto cerca nei nomi, anche nelle sottocartelle. I
  risultati mostrano il percorso completo.
- **Anteprima**: si fa clic sul nome di un file. Immagini, video, audio, PDF e
  testo si aprono nel pannello; il testo si può anche modificare, dove si ha il
  permesso di scrivere. Da lì si calcola anche l'**impronta SHA-256**, per
  verificare che un file sia arrivato identico.

I pulsanti di modifica compaiono solo dove si può scrivere davvero.

---

### Guardare le foto

Tre modi di vedere la stessa cartella, dal selettore in alto:

| | Quando serve |
|---|---|
| **Elenco** | file di ogni tipo: nome, dimensione e data incolonnati |
| **Griglia** | schede con miniatura, nome e comandi |
| **Galleria** | miniature grandi, per riconoscere le foto a colpo d'occhio |

La scelta resta nel tuo browser: è una preferenza di lettura, non una proprietà
della cartella, e non cambia quello che vedono gli altri.

**Le miniature le prepara il server**, una volta sola per foto, e le tiene in
`/var/lib/anf/miniature` — non sul NAS. Vengono chieste solo quando entrano
nello schermo: in una cartella con centinaia di scatti, generarle tutte
all'apertura significherebbe attendere per immagini che non guarderai.

Se una foto viene sostituita con un'altra dello stesso nome, la miniatura si
rifà da sola: dipende anche da data e dimensione del file.

Aprendo una foto si scorre alle altre della cartella con le **frecce ai lati**,
con i **tasti freccia** della tastiera, o **trascinando col dito** su un
telefono. In alto è scritto a che punto sei: «3 di 12».

Sul telefono la galleria mette tre foto per riga e l'anteprima occupa tutto lo
schermo: i margini di una finestra sprecherebbero proprio lo spazio che serve a
guardare l'immagine.

## Condividere con chi non ha un account

**Pubblicazioni → Regole per cartella → Link di condivisione.**

Si sceglie la cartella, facoltativamente una scadenza, un numero massimo di
scaricamenti e una password. Il collegamento che esce si manda a chi deve
ricevere i file: chi lo apre vede solo quella cartella, senza menu e senza
possibilità di risalire.

Due cose importanti:

- **il token si vede una volta sola.** Nel database resta solo la sua impronta,
  quindi non è più recuperabile: va copiato subito;
- **revocare non cancella.** Il collegamento smette di funzionare ma resta
  nell'elenco con il numero di volte in cui è stato usato, che è esattamente
  ciò che si vuole sapere dopo averlo revocato.

Un link non supera mai due limiti: non porta fuori dalla cartella per cui è
stato creato, e non apre un percorso marcato *Nessuno*.

---

## Utenti

**Utenti → Nuovo utente.**

I permessi qui sono **generali** — cosa una persona può fare ovunque:
scaricare, caricare, creare cartelle, rinominare, modificare, eliminare, creare
link. *Dove* può farlo si decide nella pubblicazione. Le due cose sono separate
perché rispondono a domande diverse.

L'**ambito** è un confine: un utente con ambito `foto` non esce da quella
cartella, qualunque permesso gli si dia.

Il pannello impedisce di rendersi ingestibile: non ci si può togliere i
privilegi da soli, e l'ultimo amministratore non si può degradare né eliminare.

---

## Vedere cosa succede

**Trasferimenti** mostra cosa è stato scaricato e caricato, da chi e da quale
indirizzo, aggiornandosi dal vivo.

Una precisazione onesta sui numeri: i **byte davvero trasferiti** li conosce
solo il web server, perché è lui a inviare i file. Compaiono qui solo se nel
file `.env` è indicato il suo access log (`ANF_ACCESS_LOG`). Finché non ci
sono, restano vuoti — un numero inventato sarebbe peggio di uno assente.

Se il pannello è dietro un reverse proxy, gli indirizzi reali arrivano solo se
il proxy è elencato in `ANF_TRUSTED_PROXIES`: `X-Forwarded-For` la può scrivere
chiunque, e fidarsene sempre permetterebbe a ogni visitatore di dichiarare
l'indirizzo che preferisce.

---

## Impostazioni

**Impostazioni** permette di cambiare nome, sottotitolo e logo del pannello, e
di decidere se elencare anche i file che iniziano con un punto.

Nella stessa pagina c'è lo **spazio sui dischi**, compreso quello del disco su
cui vive il pannello: è quello che ci si dimentica, e se si riempie il pannello
smette di funzionare anche con il NAS mezzo vuoto.

---

## Installare il pannello sul telefono

Il pannello è un'applicazione installabile: aprendolo dal browser del telefono,
il menu offre *Aggiungi a schermata Home*. Da lì si apre come un'applicazione,
a schermo intero.

Gli aggiornamenti non si applicano da soli: compare un avviso e si decide.
Ricaricare il codice mentre qualcuno sta configurando un mount è peggio che
restare una versione indietro per qualche minuto.

---

## Se qualcosa non va

| Sintomo | Dove guardare |
|---|---|
| Una cartella non si apre | Pubblicazioni → *Verifica un accesso*: dice quale regola ha deciso |
| I download rispondono vuoti | manca `XSendFilePath` (Apache) o la `location internal` (Nginx): rigenerare il vhost da **Web server** |
| Il mount non parte | Condivisioni NFS: lo stato reale e l'errore del sistema sono lì |
| Il NAS rifiuta la scrittura | è una regola del NAS, non del pannello: [synology-nfs-scrittura.md](synology-nfs-scrittura.md) |
| I trasferimenti non mostrano i byte | manca `ANF_ACCESS_LOG` nel file `.env` |

I registri dei servizi:

```bash
journalctl -u anf-api -f
journalctl -u anf-agent -f
```
