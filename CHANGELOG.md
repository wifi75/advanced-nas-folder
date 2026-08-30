# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate qui.

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/)
e il versionamento segue [Semantic Versioning](https://semver.org/lang/it/).

## [Non rilasciato]

### Da fare
Vedere [TODO.md](TODO.md).

## [0.10.2] - 2026-08-30

### Corretto
- **Nel resoconto dell'aggiornamento risultava modificato ogni file.** rsync
  confronta data e dimensione, e il pacchetto viene ricompilato a ogni rilascio:
  le date sono sempre nuove, quindi tutto sembrava cambiato. Un resoconto che
  segnala tutto non segnala niente. Ora il confronto è sul contenuto.

## [0.17.0] - 2026-08-30

Impaginazione scelta fra cinque proposte: **un solo riquadro per pagina**.

### Modificato
- **La testata e' l'unico riquadro**, tinto del colore della cosa che descrive:
  azzurro per una condivisione, verde per una cartella pubblicata. Contiene
  identita', stato o visibilita', e — per una pubblicazione — l'indirizzo da
  condividere.

  Prima l'indirizzo aveva un riquadro suo, disegnato in un modo, e i gruppi di
  campi ne avevano un altro, disegnato diversamente: la stessa pagina sembrava
  fatta da due mani. Con un solo riquadro il difetto non puo' ripresentarsi,
  invece di doverne tenere allineati due a mano.
- **Un campo non e' piu' una scheda**: e' un'etichetta e un valore. Ogni campo
  aveva il proprio riquadro, dentro quello del gruppo, dentro quello della
  pagina — tre livelli.
- **Le sezioni si separano con una linea**, non con un riquadro ciascuna.

## [0.16.0] - 2026-08-30

### Corretto
- **L'elenco delle pubblicazioni non era piu' raggiungibile.** Con l'albero nel
  menu le cartelle pubblicate si aprono dalla loro condivisione, e nessuna voce
  portava piu' alla pagina che le raccoglie tutte. Ora c'e' «Tutte le cartelle
  pubblicate».
- **Quella pagina ripeteva le funzioni della pagina di dettaglio** — modifica,
  permessi, link, rimozione — con il risultato di doverle mantenere due volte e
  di nasconderle a chi arriva dall'albero. Ora l'elenco porta al dettaglio, e
  mostra da quale condivisione arriva ogni cartella: in un elenco che le mischia
  tutte e' l'informazione che manca per orientarsi.

### Modificato
- **I pulsanti hanno un fondo tinto della propria funzione**, con la stessa
  formula della scheda di stato: azzurro per le azioni, rosso per quelle
  distruttive, grigio per le secondarie. Bianchi su una pagina chiara non si
  distinguevano da un riquadro.
- Anche la linguetta attiva di un sottomenu e' tinta: bianca su bianco non
  diceva quale fosse.

## [0.15.3] - 2026-08-30

### Modificato
- **Lo stato del montaggio e' una scheda colorata fra i dati**, verde quando e'
  montato, gialla in attesa, rossa in errore. Era una pillola in alto a destra,
  lontana dai dati che descrive e facile da non guardare.

## [0.15.2] - 2026-08-30

### Corretto
- **La barra della selezione finiva sotto il pie' di pagina.** Su una cartella
  corta il piede arriva al fondo dello schermo, dove quella barra e' fissa: si
  sovrapponevano, e meta' dei comandi restava illeggibile. Lo stesso difetto
  gia' corretto per l'avviso di aggiornamento, nell'altro punto in cui
  capitava.

### Modificato
- **L'archivio usa il materiale del menu**: ogni voce e' una scheda di vetro
  invece di una riga incollata alla successiva, e il selettore fra elenco,
  griglia e galleria e' una barra segmentata come i sottomenu.

## [0.15.1] - 2026-08-30

### Corretto
- **Un gruppo con un solo campo lo allargava ancora per tutta la pagina.** La
  griglia usava `auto-fit`, che fa collassare le colonne vuote: l'unico campo
  presente le occupava tutte. Con `auto-fill` le colonne restano, e il campo
  tiene la propria larghezza.

## [0.15.0] - 2026-08-30

### Modificato
- **I campi stanno in griglia, non impilati.** Un campo per il nome era largo
  quanto la pagina: una fascia di 570 pixel per contenere una parola. Ora i
  campi corti stanno affiancati, e chiedono l'intera larghezza solo quelli che
  ne hanno bisogno — un interruttore con la sua spiegazione, un elenco su piu'
  righe.
- **Ogni gruppo di campi ha la sua pastiglia colorata**, come le voci del menu:
  la tinta delle condivisioni per l'origine, quella delle pubblicazioni per il
  nome, quella degli utenti per gli accessi, il rosso per la rimozione. Le
  pagine erano l'unica parte del pannello senza un'icona.

## [0.14.6] - 2026-08-30

### Modificato
- **I pulsanti secondari erano bianchi pieni con il testo grigio**: sparivano
  nella pagina e sembravano disattivati. Ora usano lo stesso vetro delle voci di
  menu, e il testo resta leggibile come quello del pulsante principale —
  «secondario» non deve voler dire «spento».

## [0.14.5] - 2026-08-30

### Corretto
- **«Nuova pubblicazione» dentro una condivisione lasciava la pagina bianca.**
  Il controllo che apre la finestra veniva eseguito subito, prima che la
  funzione che chiama fosse stata inizializzata: la pagina moriva con un errore
  e restava vuota. Introdotto nella 0.14.4, insieme alla correzione del
  collegamento.

### Modificato
- **Le pagine hanno un fondo proprio**, come la barra laterale. Prima poggiavano
  su un colore quasi identico a quello delle schede, e ogni cosa sembrava
  incollata alla successiva.
- **Ogni campo e' una scheda con il materiale delle voci di menu** — vetro,
  raggio di 11px, filo di luce — invece di un rettangolo grigio dentro un
  pannello piatto. I gruppi non sono piu' riquadri dentro riquadri: sono un
  titolo con sotto una pila di schede, come una categoria del menu.
- I pulsanti hanno spazio fra loro e da cio' che li precede.

## [0.14.4] - 2026-08-30

### Corretto
- **I campi delle pagine nuove erano senza stile.** L'etichetta risultava
  incollata al campo, i menu a tendina e le caselle erano quelli di sistema:
  gli stili esistevano, ma nel foglio *scoped* di una sola vista, e usare
  `class="campo"` altrove non li applicava. Ora sono globali, con lo stesso
  aspetto in ogni pagina.
- **«Nuova pubblicazione» dentro una condivisione portava all'elenco**, dove
  bisognava premere un secondo pulsante uguale e riscegliere l'origine da capo.
  Ora apre direttamente la creazione con quella condivisione gia' scelta.
- **«Permessi e link» portava all'elenco** invece che alla pubblicazione.

### Modificato
- **L'azione principale usa la sfumatura delle pastiglie del menu**, non un
  colore piatto: filo di luce in alto e alone della propria tinta sotto.
- Gli interruttori sono righe cliccabili con un riquadro proprio, e
  «Consenti la scrittura» ha la tinta dell'attenzione: espone il NAS a
  scritture, non e' una preferenza qualunque.

## [0.14.3] - 2026-08-30

### Corretto
- **Nessuna pagina puo' piu' scorrere in orizzontale.** Cio' che e' largo
  davvero — una tabella, un percorso — scorre dentro il proprio riquadro, non
  trascina la pagina intera. Un testo lungo nei passi della pagina iniziale
  poteva spingerla oltre il bordo.

### Interno
- **`controlla.ps1`**: un solo comando che esegue formattazione, analisi
  statica, tipi, test e compilazione, e si ferma davvero se qualcosa fallisce.
  Lanciandoli a mano finivo il comando con una pipe verso `tail` per leggere
  solo il riepilogo — e una pipe restituisce l'esito dell'ultimo comando, non
  di pytest. Due difetti sono arrivati su GitHub cosi'.

## [0.14.2] - 2026-08-30

### Corretto
- **Un mount in transizione mostrava `mount.statoInCorso`** al posto del testo:
  la chiave era usata ma non definita. Il test che controlla proprio questo era
  rosso, ma il rilascio e' partito lo stesso perche' nel comando la pipe verso
  `tail` nascondeva l'esito di pytest. Il difetto e' durato una versione.

## [0.14.1] - 2026-08-30

### Modificato
- **Le pagine usano lo stesso materiale della barra laterale**: vetro
  traslucido, raggio di 11px, filo di luce in alto. Erano riquadri piatti
  bianchi, e sembravano un'altra applicazione attaccata al menu.
- **Le linguette dei sottomenu sono una barra segmentata** invece di testo nudo
  su una linea: devono sembrare qualcosa su cui si clicca anche prima di
  provarci.
- **Ogni pagina di dettaglio ha la pastiglia colorata** della voce di menu
  corrispondente, così si riconosce dove si è senza leggere le briciole.

### Corretto
- **Il percorso di montaggio andava a capo a metà parola**
  (`/srv/nas/mnt-synology-f` poi `oto-cucina`): illeggibile, e impossibile da
  copiare a occhio. Ora scorre invece di spezzarsi.
- **Lo stato del montaggio non compariva** nella pagina della condivisione: era
  visibile solo nell'elenco, cioè nel posto da cui si era appena usciti.

## [0.14.0] - 2026-08-30

L'impianto scelto fra quattro proposte: **l'albero nel menu**.

### Aggiunto
- **Le condivisioni e le loro cartelle pubblicate stanno nel menu, annidate.**
  Il legame fra le due si vede senza aprire niente: era il punto in cui il
  pannello risultava incomprensibile, perche' quel legame andava ricostruito a
  mente saltando fra due elenchi separati.

  I figli compaiono solo per la condivisione aperta: mostrarli tutti sempre
  allungherebbe il menu oltre lo schermo appena le condivisioni diventano
  qualcuna in piu'.
- **«Pubblica una cartella» sotto ogni condivisione**: la nuova pubblicazione
  nasce gia' legata a quella, senza far riscegliere l'origine.
- **Pagina della singola pubblicazione**, con sottomenu: *Indirizzo e nome*
  (indirizzi, nome, origine), *Chi accede* (visibilita', regole per cartella,
  permessi, link, verifica), *Contenuto* (nomi da nascondere, rimozione).

### Modificato
- **Gli aggiornamenti si applicano da soli.** Il service worker chiedeva
  conferma con un avviso in fondo alla pagina, e chi non lo notava restava sulla
  versione precedente convinto che l'aggiornamento non avesse funzionato. La
  scelta iniziale — non cambiare il codice sotto le mani di chi sta lavorando —
  aveva un senso, ma il difetto che produceva era peggio del rischio che
  evitava: un pannello che non si aggiorna da solo sembra rotto.
- `shares.modifica` restituisce l'esito: prima chi la chiamava non poteva
  distinguere una modifica riuscita da una fallita.

## [0.13.1] - 2026-08-30

### Corretto
- **Le pubblicazioni gia' esistenti continuavano a mostrare il cestino del NAS.**
  La 0.13.0 proponeva i nomi da nascondere solo alle pubblicazioni nuove: chi
  aggiornava non vedeva alcun cambiamento, che e' esattamente il contrario di
  quello che serve. Ora una migrazione riempie l'elenco dove era rimasto vuoto.

## [0.13.0] - 2026-08-30

Di una pubblicazione si poteva cambiare quasi niente. Ora tutto quello che la
definisce e' modificabile.

### Aggiunto
- **Il nome nell'indirizzo si puo' cambiare.** Era fisso per scelta mia, per non
  rompere i collegamenti gia' condivisi: ma e' una conseguenza che va spiegata a
  chi decide, non un motivo per decidere al posto suo. Il pannello avvisa
  soltanto quando il nome e' stato davvero toccato, e rifiuta un nome gia' usato.
- **L'origine si puo' cambiare**: da quale condivisione NFS e da quale sua
  sottocartella. Correggere un percorso sbagliato non costringe piu' a rifare
  tutto: permessi, regole e link restano al loro posto.
- **Elenco dei nomi da non mostrare, per pubblicazione.** I NAS creano cartelle
  proprie — `#recycle` di Synology, `@eaDir`, le istantanee — che non sono
  contenuto da pubblicare e che chi riceve l'indirizzo non deve nemmeno vedere.
  Alla creazione l'elenco viene **proposto** con i nomi tipici, e si modifica:
  quali siano dipende dal NAS, quindi non e' una costante nel codice. Accetta i
  caratteri jolly (`@ea*`), e svuotarlo mostra di nuovo tutto.

  Vale anche per i **link di condivisione**: chi riceve un link non deve vedere
  il cestino del NAS piu' di chi entra dal pannello.

## [0.12.3] - 2026-08-30

### Modificato
- **Tema, lingua e utente stanno ora subito sotto l'ultima voce del menu**,
  invece di essere spinti in fondo alla barra. Il vuoto in mezzo li faceva
  sembrare scollegati dal resto.

## [0.12.2] - 2026-08-30

### Corretto
- **L'avviso in basso si sovrapponeva al piè di pagina.** Il piede sta nel
  flusso e su una pagina corta — l'accesso, per esempio — finisce proprio al
  fondo dello schermo, dove l'avviso e fisso: i due testi si leggevano uno
  attraverso l'altro. Ora l'avviso sta sopra.

## [0.12.1] - 2026-08-30

### Corretto
- **La pagina di accesso finiva in alto a sinistra invece che al centro.**
  Unificando l'impianto delle pagine nella 0.12.0 ho dato a tutte la stessa
  `.pagina`, che impagina un elenco in colonna: ma accesso e «pagina non
  trovata» hanno un solo riquadro, e vogliono essere centrate. Ora hanno un
  impianto proprio.
- **Trasferimenti e impostazioni avevano perso la loro larghezza.** I
  trasferimenti sono tabelle e stavano su 1100px, le impostazioni sono un
  modulo stretto e stavano su 760px: l'unificazione le aveva portate entrambe a
  880. Sono due eccezioni motivate, ora dichiarate come tali.

## [0.12.0] - 2026-08-30

Il pannello sapeva fare tutto ma era organizzato per **tipo di oggetto**, non
per cosa si sta facendo: quel che riguarda una condivisione stava sparso fra tre
pagine, e ogni pagina era un elenco piatto di campi. Chi non conosceva gia' il
pannello non aveva modo di capire che erano parti della stessa cosa.

### Aggiunto
- **Pagina della singola condivisione** (`/condivisioni/<id>`), con sottomenu:
  *Panoramica* (stato, percorso, accesso richiesto ed effettivo, monta/smonta),
  *Montaggio* (nome, versione NFS, montaggio su richiesta, scrittura —
  **modificabili**, prima si potevano solo decidere alla creazione),
  *Cartelle pubblicate* (solo quelle di questa condivisione, con i loro
  indirizzi), *Avanzate* (rimozione, che avvisa quante pubblicazioni si
  fermeranno).

  Sta su un indirizzo proprio e non in un pannello a comparsa: cosi' si puo'
  salvare fra i preferiti e il tasto «indietro» fa quello che ci si aspetta.
- **Sottomenu anche dentro una pubblicazione**: regole per cartella, permessi
  per utente, link di condivisione e verifica di un accesso erano quattro
  argomenti distinti impilati in un'unica colonna lunghissima.
- **Campi raggruppati** nei moduli di configurazione, ognuno con un titolo e una
  riga che dice a cosa serve quel gruppo: «Quale cartella», «Come si chiama»,
  «Chi puo' accedere» per una pubblicazione; «Come chiamarla», «Come montarla»
  per una condivisione. Erano elenchi piatti in cui non si capiva quante
  decisioni restassero.

### Corretto
- **Il pannello mostrava «share.modifica» al posto di «Modifica».** Le chiavi di
  quei testi erano finite nel blocco sbagliato del file delle traduzioni. Build,
  controllo dei tipi e lint passavano tutti: una chiave mancante si vede solo
  aprendo quella pagina.
- **Un test ora controlla che ogni testo usato esista in entrambe le lingue**, e
  ha subito trovato altri due casi: `errori.generico` non era definito affatto —
  quindi un errore imprevisto mostrava il nome della chiave — e
  l'identificatore del modulo dei mount era stato spostato via per sbaglio.
- La formattazione di `shares.py` faceva fallire i controlli automatici a ogni
  push. Il gate locale eseguiva `ruff check` ma non `ruff format --check`.

## [0.11.0] - 2026-08-30

Chiude la fase 4. La fase 3 era gia' completa.

### Aggiunto
- **Evidenziazione della sintassi anche mentre si scrive.** Uno strato colorato
  sotto, l'area di testo sopra col testo trasparente e il solo cursore visibile.
  Non serve una libreria per editor: le due copie del testo devono solo avere le
  stesse identiche metriche del carattere, o si sfalsano riga dopo riga.

### Corretto
- **Nel resoconto dell'aggiornamento risultava modificato ogni file.** rsync
  confronta data e dimensione, e il pacchetto viene ricompilato a ogni rilascio:
  le date sono sempre nuove, quindi tutto sembrava cambiato. Un resoconto che
  segnala tutto non segnala niente. Ora il confronto e' sul contenuto. *(La
  v0.10.2 dichiarava questa correzione senza contenerla: la modifica non era
  stata applicata al file. Le sue note sono state corrette.)*

### Non fatto, e perche'
- **L'avanzamento del download lato pannello resta fuori.** Le due voci ancora
  aperte della fase 2 e della fase 4 sono la stessa cosa, ed e' un limite
  dichiarato: la consegna e' delegata al web server, e da quel momento
  l'applicazione e' uscita di scena. Mostrare una percentuale richiede di far
  passare i byte da Python, cioe' rinunciare alla ripresa nativa dei download e
  saturare i worker. Non e' lavoro rimasto: e' una decisione gia' presa, che
  andrebbe ribaltata di proposito.

## [0.10.1] - 2026-08-30

### Corretto
- **Il resoconto dell'aggiornamento annegava nel rumore.** `__pycache__` e
  `.egg-info` venivano cancellati e ricreati a ogni aggiornamento, e l'elenco
  dei file cambiati si apriva con decine di righe che non dicevano niente. Ora
  restano fuori: Python li rigenera da solo.

## [0.10.0] - 2026-08-30

Pagine più coerenti, e le cose che mancavano per governare una pubblicazione.

### Aggiunto
- **Tasto Modifica su una pubblicazione.** Si potevano cambiare solo lo stato
  acceso/spento e nient'altro: nome, descrizione e visibilità erano decisi alla
  creazione e poi immutabili dal pannello, pur essendo tutte cose che l'API
  accetta. Il nome nell'indirizzo resta invece fisso di proposito, e la finestra
  lo spiega: cambiarlo romperebbe i collegamenti già condivisi, che sono
  esattamente ciò che una pubblicazione serve a produrre.

### Modificato
- **Un solo sistema di pulsanti per tutto il pannello.** Ne convivevano due —
  `.bottone` con le sue varianti in certe pagine, `.secondario`/`.pericolo` in
  altre, più i `button` nudi stilizzati dal foglio di ogni vista — e lo stesso
  pulsante cambiava aspetto a seconda della pagina. La forma segue ora quella
  delle voci del menu: stesso raggio, stesso peso, stessa distanza dal bordo.
- **Impianto delle pagine unificato**: `.pagina`, `.testata`, `.scheda` e
  `.vuoto` erano definiti in ogni vista, nove volte, e avevano già cominciato a
  divergere — larghezze uguali ma spaziature diverse, così passando da una
  pagina all'altra il contenuto si spostava senza motivo.
- **Il menu non ha più voci disattivate.** «File» e «Link di condivisione»
  erano segnate come in arrivo «nella fase 3 e 4», ma quelle funzioni ci sono da
  parecchie versioni: annunciarle come future era la prima cosa che si leggeva
  aprendo il menu. «File» porta ora davvero all'archivio; i link si creano
  dentro la pubblicazione a cui appartengono, quindi la voce a sé è sparita.
- **Le etichette dell'interruttore erano stati, non azioni**: il pulsante per
  spegnere una pubblicazione diceva «Disattivata». Ora dice «Disattiva».

## [0.9.1] - 2026-08-30

### Modificato
- **`update.sh` mostra i file cambiati**, in verde quelli aggiunti, in rosso i
  rimossi, in giallo i modificati, con il totale in fondo. Senza, un
  aggiornamento riuscito e uno che non ha toccato niente erano indistinguibili
  — ed è esattamente la domanda che ci si fa dopo averlo lanciato. Quando non
  cambia nulla lo dice: «eri già aggiornato».

  I colori escono solo su un terminale vero: rediretto in un file, le sequenze
  di escape sporcherebbero l'output senza colorare niente.
- **Il campo che decide l'indirizzo si chiama ora «Nome nell'indirizzo»**, non
  più «Identificatore», e sotto compare **l'indirizzo che ne uscirà, mentre lo
  si scrive**. Il collegamento fra quel campo e l'indirizzo pubblico si scopriva
  solo dopo aver salvato. Il nome resta proposto a partire dall'etichetta, ma è
  chiaro che si può riscrivere.

## [0.9.0] - 2026-08-30

Chiude le tre voci rimaste della gestione file.

### Aggiunto
- **Viste a griglia e galleria** nell'archivio, oltre all'elenco. La scelta
  resta nel browser di chi guarda: è una preferenza di lettura, non una
  proprietà della cartella. In galleria le miniature vengono chieste **solo
  quando entrano nello schermo** — ogni miniatura richiede un gettone all'API, e
  una cartella con qualche centinaio di foto ne genererebbe altrettante
  richieste all'apertura, per immagini che nessuno ha ancora guardato.
- **Menu contestuale** col tasto destro, con le stesse azioni della riga. Serve
  soprattutto alle viste a griglia e galleria, dove i pulsanti per esteso non
  ci stanno: senza, quelle viste sarebbero di sola lettura.
- **Evidenziazione della sintassi in lettura**, con `highlight.js` 11.12.0.
  L'anteprima ora **apre anche i file di codice**, che prima finivano fra i «non
  mostrabili» e non si potevano vedere affatto. I linguaggi si dichiarano uno
  per uno invece di caricare la libreria intera: quella completa supera il
  megabyte e finirebbe tutta nella precache della PWA. Il costo effettivo è di
  circa 75 KB.

  I colori dell'evidenziazione sono **variabili del tema**, non un foglio di
  stile esterno: seguono chiaro e scuro come tutto il resto, invece di restare
  fissi su una delle due varianti.

### Limite dichiarato
- L'evidenziazione vale **in lettura, non mentre si scrive**: modificando si
  torna al testo semplice. Evidenziare dentro un campo modificabile richiede un
  editor vero, che è lavoro di un altro ordine di grandezza.

## [0.8.0] - 2026-08-30

Il pannello faceva tutto, ma non spiegava **in che ordine**. Chi montava una
cartella del NAS non trovava niente da nessuna parte, perché montata non vuol
dire pubblicata — e questo non era scritto da nessuna parte.

### Modificato
- **La pagina iniziale mostra i tre passi reali**, con lo stato di ciascuno:
  quante cartelle sono montate, quante pubblicate, e da dove si arriva
  all'archivio. La numerazione non è decorativa: senza il primo passo il secondo
  non è possibile, e la pagina lo dice.
- **Toglie l'avviso «in arrivo nella fase 2 e nella fase 3»**, che descriveva
  come future funzioni presenti da parecchie versioni. Era il primo motivo di
  confusione: chi lo leggeva concludeva che pubblicare non si potesse ancora
  fare.
- **L'indirizzo da condividere ha ora un posto suo**, in un riquadro dedicato
  accanto a ogni pubblicazione: indirizzo corto e completo, ciascuno con il suo
  pulsante per copiare e una riga che spiega quando usare l'uno o l'altro. Prima
  gli indirizzi comparivano come testo in mezzo al resto.
- **Le condivisioni NFS dicono quante pubblicazioni le usano**, con il
  collegamento per crearne una. Una cartella montata e mai pubblicata non è
  raggiungibile da nessuno, nemmeno da un amministratore: adesso si vede.
- **I sottotitoli delle due pagine dicono anche cosa NON fanno**: montare non
  rende raggiungibile, pubblicare non copia né sposta niente.
- **Guida utente riscritta** nella parte iniziale, in italiano e inglese: una
  tabella dei tre passi con cosa fa e cosa non fa ciascuno, e una sezione
  dedicata all'indirizzo da condividere — compresa la differenza fra condividere
  l'indirizzo e creare un link a scadenza per una singola persona.

### Interno
- Gli indirizzi di una pubblicazione stanno ora in un componente unico
  (`IndirizziPubblicazione.vue`) invece che duplicati nelle pagine: due copie
  erano già divergite una volta.

## [0.7.3] - 2026-08-30

### Corretto
- **`update.sh` si fermava con «curl: (23) Failure writing output».** Il comando
  che risolve il tag dell'ultima versione era `curl … | grep -m1 …`: `grep -m1`
  chiude la pipe appena trova la riga, curl non riesce più a scrivere ed esce con
  23, e `pipefail` fa fallire l'aggiornamento. Il messaggio fa pensare a un disco
  pieno, che non c'entrava nulla. Introdotto nella 0.7.2, insieme alla
  risoluzione del tag.

### Modificato
- **`update.sh` e `uninstall.sh` vivono ora nella cartella dell'applicazione.**
  Sono strumenti dell'applicazione, e il posto dove cercarli è la sua cartella,
  non `/root`. Per aggiornare basta quindi:

  ```bash
  cd /var/www/advanced-nas-folder && sudo bash update.sh
  ```

  Perché sia possibile, `update.sh` **si ricopia da solo in una cartella
  temporanea e riparte da lì** quando viene lanciato da dentro l'installazione:
  è proprio quella la cartella che riscrive, e bash legge lo script mentre lo
  esegue — sostituirlo a metà corsa interromperebbe l'aggiornamento in un punto
  qualunque.

## [0.7.2] - 2026-08-30

### Corretto
- **Le scorciatoie rispondevano 404.** Erano generate come regole di
  `mod_rewrite`, che i VirtualHost **non** ereditano dalla configurazione di
  server — quindi non si applicavano a nessun sito servito da un vhost, cioè a
  tutti. Ora sono `RedirectMatch`, di `mod_alias`, che invece viene ereditato.
  L'`Alias` del pannello funzionava proprio per questo, e la differenza non era
  visibile dal test di sintassi: la configurazione era valida, semplicemente non
  si applicava.
- **`update.sh` poteva installare in silenzio la versione precedente.** Usava
  `/releases/latest/download/`, che GitHub serve da una cache: subito dopo una
  pubblicazione quell'indirizzo restituisce ancora il pacchetto di prima, e
  l'aggiornamento riusciva senza aggiornare nulla. Ora risolve il tag vero
  dall'API prima di scaricare.

## [0.7.1] - 2026-08-30

### Corretto
- **`update.sh` non ricaricava le unit systemd.** I servizi ripartivano con la
  definizione caricata all'avvio, quindi una correzione a un file `.service`
  installata dall'aggiornamento non aveva effetto — e systemd si limitava a un
  avviso in coda all'output, facile da non vedere.

## [0.7.0] - 2026-08-30

### Aggiunto
- **Indirizzi corti per le cartelle pubblicate.** `https://sito/documenti` porta
  alla stessa cartella di `https://sito/pannello/archivio/documenti`. Il file di
  configurazione viene riscritto per intero a ogni modifica di una pubblicazione,
  a partire dall'elenco di quelle attive: una scorciatoia non può sopravvivere
  alla pubblicazione che l'aveva creata.

  Tre scelte, non tre limiti: viene generata **una regola per ogni
  pubblicazione** e mai una che cattura tutto, perché il sito ospita quasi sempre
  anche altro e una regola generica ne oscurerebbe i contenuti in silenzio; sono
  **redirezioni** e non riscritture interne, perché il router del pannello non
  riconoscerebbe un indirizzo che parte dalla radice; funzionano **solo su
  Apache**, perché su Nginx le `location` devono stare dentro il blocco `server`
  e un file a sé non sarebbe valido — il pannello lo dice invece di scrivere
  configurazione che non funziona.

  I nomi `pannello`, `api`, `server-status` e `server-info` sono rifiutati: una
  scorciatoia `/pannello` renderebbe il pannello irraggiungibile, e a quel punto
  non ci sarebbe più modo di toglierla dal pannello stesso.
- Nuovo endpoint `POST /api/v1/shares/scorciatoie` per riapplicarle a mano,
  quando il web server era irraggiungibile al momento della modifica.

### Modificato
- Ogni pubblicazione mostra ora **entrambi** gli indirizzi: quello completo e
  quello corto.
- Badge dei test aggiornato: 388.
- Lo stato dichiarato nel README non dice più che il progetto non è mai stato
  installato in produzione, perché non è più vero.

## [0.6.9] - 2026-08-30

### Corretto
- **`update.sh` non aggiornava nulla**: cercava l'ambiente Python in
  `backend/.venv`, che è il percorso di sviluppo. In produzione l'installer lo
  crea nella radice, e l'aggiornamento si fermava con «No such file or
  directory». Il ripristino automatico funzionava — la versione precedente
  tornava al suo posto e i servizi ripartivano — ma l'aggiornamento non era mai
  possibile.

## [0.6.8] - 2026-08-30

### Aggiunto
- **Ogni pubblicazione mostra l'indirizzo completo su cui si raggiunge**, con un
  pulsante per copiarlo. Prima compariva solo l'identificatore (`/documenti`), e
  il resto andava indovinato: il pannello vive sotto `/pannello/` e non sulla
  radice del sito, quindi chi scriveva l'indirizzo a mano finiva su una pagina
  inesistente.

## [0.6.7] - 2026-08-30

Prima installazione su un server reale. Tutto quello che segue è emerso lì: sono
errori che nessun test poteva cogliere, perché riguardano il modo in cui systemd
crea le cartelle e il punto da cui viene letta la configurazione.

### Corretto
- **L'agent risultava irraggiungibile pur essendo in esecuzione.** Il socket aveva
  i permessi giusti (`root:anf`, `0660`), ma la cartella che lo contiene veniva
  creata da systemd come `root:root 0750`: l'utente `anf` non poteva nemmeno
  attraversarla. Il pannello rispondeva «Agent non raggiungibile su
  /run/anf/agent.sock» mentre il file era lì, visibile e apparentemente corretto.
  L'unit dell'agent dichiara ora il gruppo, che serve alla cartella e non ai
  privilegi: l'agent resta root.
- **L'agent non partiva**: `No module named anf_agent`. Mancavano il percorso del
  modulo e il tipo di servizio, e `PrivateNetwork` gli impediva di montare — i
  mount NFS avvengono nello spazio di rete di chi li chiede.
- **Le migrazioni fallivano con «secret_key: Field required».** Il file `.env`
  veniva cercato con un percorso relativo, risolto quindi dalla cartella corrente:
  applicazione, alembic e installer partono da cartelle diverse, e lo trovavano
  solo per caso. Ora si cerca in percorsi assoluti, sia nella radice
  dell'installazione sia in `backend/`.
- La cartella dei dati restava di root dopo le migrazioni, e il servizio non
  riusciva a scrivere il database.

### Modificato
- **Il riepilogo finale dice dove andare davvero.** Prima indicava
  `http://localhost:PORTA`, che è l'unico indirizzo su cui il pannello *non*
  risponde da un'altra macchina: quella porta ascolta solo in locale, dietro il web
  server. Ora mostra l'indirizzo di rete della macchina, la porta interna
  dichiarata come tale, utente e password. E se i servizi non hanno risposto non
  dichiara più «installazione completata», ma dice che è incompleta e con quali
  comandi guardare.
- **Password iniziale `Admin1234` invece di `admin`.** È scritta in chiaro anche
  nella documentazione, di proposito: essendo pubblica non protegge nulla, e
  serve solo a far entrare la prima volta. Il pannello continua a segnalarla
  finché non viene cambiata.
- Documentato in `INSTALL.md` che la porta chiesta dall'installer non è
  l'indirizzo del pannello, e che dietro un firewall va inoltrata la 80/443.

## [0.6.4] - 2026-08-30

### Corretto
- **La prova a vuoto non chiedeva la porta.** Le domande erano disattivate con
  `--dry-run`, e la prova mostrava quindi un'esperienza diversa da quella vera — che è
  esattamente ciò che doveva evitare. Ora chiede anche lì: il caso automatico è già
  coperto dal controllo sulla presenza di un terminale. La conferma finale resta
  esclusa, perché in una prova a vuoto non c'è nulla da confermare.
- L'elenco delle porte libere usciva senza spazi («8101,8102»): `tr` sostituisce un
  carattere con un altro, non con due.
- Il percorso dell'access log veniva calcolato **prima** delle domande, quindi restava
  quello del web server rilevato anche se poi ne veniva scelto un altro.

### Modificato
- **Guida all'installazione riscritta** sui due punti che mancavano: scaricare
  l'installer da una cartella propria e non da `/var/www`, dove si installa da solo, e
  la prova a vuoto come primo passo e non come opzione. Documentate le due domande che
  ora pone, e il fatto che con `curl | bash` non ne pone nessuna perché non ha un
  terminale da cui leggere.

## [0.6.3] - 2026-08-30

L'installer diventa una cosa che si guarda mentre lavora, e chiede invece di
decidere da solo quando c'è qualcuno davanti.

### Aggiunto
- **Intestazione, icone e colori.** Ogni passo è marcato, gli esiti hanno un simbolo,
  e i simboli Unicode si usano solo se il terminale dichiara UTF-8: altrove
  comparirebbero come caratteri illeggibili, che è peggio di un trattino.
- **Riepilogo del sistema prima di toccarlo**: distribuzione, versione di Python, web
  server, memoria e spazio liberi, e **le porte già in ascolto fra la 8000 e la 9000**.
  È l'informazione che evita il conflitto più comune, e non si trova altrove se non
  guardandola.
- **Quando una porta è occupata viene detto da chi**, con il nome del servizio systemd
  e non del programma: «ilmioricettario.service» dice cosa fermare, «python» no.
- **Scelta interattiva della porta**: vengono proposte le prime cinque libere, con la
  prima come valore predefinito. E un **riepilogo delle scelte con conferma** prima che
  qualcosa venga scritto sul sistema.
- Con `curl | bash` non viene chiesto nulla e l'installer decide da solo: lì non c'è
  nessuno a rispondere, e restare fermi ad aspettare un tasto sarebbe peggio.

### Corretto
- **Il percorso dell'access log era sbagliato.** Veniva ricavato dal nome del web server
  (`/var/log/apache`), ma Apache su Ubuntu scrive in `/var/log/apache2`. Il monitoraggio
  dei trasferimenti non avrebbe mai letto un byte, e nessuno avrebbe capito perché.

## [0.6.2] - 2026-08-30

Rilasciata perché l'installer della 0.6.1 non parte su una macchina dove la porta 8100
è già occupata — cioè su qualunque server che ospiti già altre applicazioni.

### Aggiunto
- **L'installer sceglie la porta da solo.** Parte dalla 8100 e sale finché non ne trova
  una libera, dicendo quale ha scelto. Verificato su un server reale dove la 8100 era
  occupata: è passato alla 8101.
- Con `--porta` si indica una porta precisa, e se è occupata l'installer **si ferma**
  invece di spostarsi da solo: chi l'ha scritta aveva un motivo, e ritrovarsi il
  pannello altrove sarebbe peggio di un errore. Le porte fuori intervallo o non
  numeriche vengono rifiutate dicendo cosa serve.

### Corretto
- **L'installer poteva lasciare `mod_xsendfile` spento.** Il controllo era sul
  *pacchetto*, non sul modulo: su una macchina dove il pacchetto era già installato ma
  il modulo non attivo, l'intero blocco veniva saltato — compresi `mod_remoteip` e i
  moduli proxy — e i download rispondevano vuoti senza dire perché. Ora pacchetto e
  moduli si verificano separatamente, e vengono abilitati solo quelli che mancano.
- Il pacchetto della release non conteneva `README.en.md`: chi scaricava il progetto
  senza passare da GitHub aveva solo la versione italiana.
- Il banner di stato del README riportava un numero di versione fisso, che sarebbe
  invecchiato a ogni rilascio. Ora dice «dalla v0.6.0», che è un fatto storico e resta
  vero: il numero corrente lo mostra già il badge dinamico.

## [0.6.1] - 2026-08-30

Nessun cambiamento di comportamento: solo documentazione. Rilasciata perché il
pacchetto della 0.6.0 contiene i README con le affermazioni sbagliate, e chi lo
scarica leggerebbe che manca la consegna dei file.

### Corretto
- **Il README dichiarava cose non vere.** Il banner di stato diceva che mancava la
  consegna dei file, fatta dalla v0.6.0; le funzionalità elencavano viste a griglia e
  galleria, che non esistono; il cruscotto prometteva «percentuale e velocità», che con
  la consegna delegata al web server non sono ottenibili. Corretto in entrambe le
  lingue, e aggiunta la nota che spiega perché quella percentuale non c'è.
- I collegamenti ai documenti interni nel README inglese puntavano alle versioni
  italiane, tradotte nel frattempo.

### Aggiunto
- Badge di **release**, **stato dei controlli** e **numero di test** nei due README:
  i primi due sono dinamici e dicono la verità da soli.
- README: sezione su `update.sh` e `uninstall.sh`, che esistevano senza essere
  documentati, e i comandi dei test e della formattazione fra quelli utili.
- `update.sh` e `uninstall.sh` fra gli allegati della release: il primo si documenta
  come scaricabile con `curl`, e senza allegato quel comando non funzionava.

## [0.6.0] - 2026-08-30

Il pannello fa tutto quello per cui era stato pensato: i file si scaricano, si
caricano, si cercano e si modificano; gli utenti si creano; i trasferimenti si
vedono mentre succedono.

### Aggiunto
- **Consegna dei file**: le cartelle pubblicate si sfogliano e i file si scaricano.
  Il download lo esegue il web server, non l'applicazione: Python autorizza e passa
  il file con `X-Sendfile` (Apache) o `X-Accel-Redirect` (Nginx). Così la ripresa di
  un trasferimento interrotto funziona da sola — `Range`, `If-Range` ed `ETag` sono
  già implementati là — e un file grande non tiene occupato un worker.
- L'elenco di una cartella **filtra ogni voce con il controllo degli accessi**: una
  sottocartella vietata sparisce dall'elenco anche quando quella che la contiene è
  aperta a tutti. Nasconderla solo nell'interfaccia non servirebbe, visto che
  l'elenco resta leggibile via API.
- I collegamenti di download portano un **gettone valido pochi minuti e solo per quel
  percorso**, invece della password: una navigazione del browser non può portare
  intestazioni, e la query string finisce nei log del web server.
- I file che il browser eseguirebbe (HTML, SVG, XML) vengono serviti come
  `application/octet-stream`: con il loro tipo reale girerebbero nel contesto del
  pannello.
- Vista di navigazione dell'archivio, raggiungibile **anche senza accedere** quando la
  cartella è pubblica, con percorso navigabile, dimensioni, date e richiesta della
  password dove serve. Dall'elenco delle pubblicazioni un pulsante «Sfoglia» apre la
  cartella corrispondente.
- **Link di condivisione**: un modo per far arrivare una cartella a chi non ha un
  account e non lo avrà. Il token stesso è l'autorizzazione, limitata a un ramo, a una
  scadenza e a un numero di scaricamenti, e revocabile in qualunque momento.
  Facoltativamente protetto da una password.
- Due limiti il token non li supera, perché non sarebbero eccezioni ma buchi: non
  porta mai fuori dal ramo per cui è stato creato, e non apre un percorso marcato
  *negato*. Se un link superasse un divieto esplicito, crearne uno sarebbe il modo per
  aggirarlo.
- Nel database resta solo l'impronta SHA-256 del token, che perciò viene mostrato una
  volta sola, subito dopo la creazione.
- La revoca non cancella la riga: quante volte è stato usato un collegamento poi
  revocato è esattamente ciò che si vuole sapere dopo averlo revocato.
- Pagina dedicata a chi riceve un link — spoglia di proposito, senza menu né accesso al
  pannello, perché mostra soltanto il ramo che il collegamento concede.
- **Pubblicazione sul web server dal pannello**: si indica un nome host, si guarda
  l'anteprima della configurazione e la si applica. Il file generato non tocca quello
  scritto dall'installer.
- La configurazione viene **provata prima di essere applicata** con `apache2ctl
  configtest` o `nginx -t`, e **se il test non passa quella precedente torna al suo
  posto**. Un pannello che può lasciare il web server incapace di ripartire prima o poi
  lo mette fuori uso. L'esito del test compare nel messaggio d'errore: è l'unica cosa
  che spiega cosa correggere.
- La configurazione generata contiene le direttive delicate che finora andavano
  ricordate a mano — `XSendFilePath` su Apache, una `location` marcata `internal` su
  Nginx. Se mancano, i download rispondono vuoti; se sono scritte male, i file del NAS
  diventano raggiungibili saltando i permessi.
- **Operazioni sui file**: nuova cartella, rinomina, sposta, copia ed elimina, dal
  pannello. I pulsanti compaiono solo dove si ha il permesso di scrittura, e il
  controllo vero lo rifà comunque il server a ogni chiamata.
- Non si sovrascrive mai per sbaglio: se la destinazione esiste l'operazione fallisce e
  lo dice. Una cartella con dentro qualcosa si elimina solo con una conferma esplicita:
  chi crede di cancellarne una vuota non deve perderne il contenuto.
- Spostare richiede la scrittura su origine **e** destinazione — chiederla solo sulla
  destinazione permetterebbe di svuotare una cartella su cui non si ha alcun diritto.
  Copiare richiede solo di poter leggere l'origine, perché non la cambia.
- I nomi vengono controllati contro quelli che il NAS accetterebbe ma che poi risultano
  inapribili da SMB o da Windows: barre, due punti, nomi di dispositivo, nomi che
  finiscono con uno spazio.
- La scrittura viene verificata provandoci, non fidandosi di ciò che il pannello ha
  chiesto: se la regola NFS sul NAS è in sola lettura, il mount lo è.
- **Caricamento dei file**, con trascinamento, avanzamento e ripresa. Il file viene
  inviato a blocchi: su una rete domestica un file da qualche gigabyte non arriva al
  primo tentativo, e ricominciare da capo a ogni interruzione renderebbe la funzione
  inutile.
- **Lo stato della ripresa è il file parziale stesso**, non una riga in un database:
  quanti byte sono arrivati lo dice la sua dimensione. Non c'è nulla da tenere
  allineato, e un caricamento interrotto ieri riprende oggi senza che nessuno se ne sia
  dovuto ricordare.
- Il file parziale è nascosto e non compare fra i file: un caricamento a metà non deve
  sembrare un file scaricabile. Il completamento è una rinomina atomica, quindi non
  esiste un istante in cui il file esiste ma è incompleto.
- Un blocco inviato alla posizione sbagliata viene rifiutato invece che scritto:
  scriverlo comunque produrrebbe un file corrotto che nessuno nota fino all'apertura.
- ESLint conosce ora i nomi globali del browser. Prima non li dichiarava, e per farlo
  tacere si scriveva `globalThis.document` al posto di `document`: quei giri sono stati
  tolti.
- **Gestione degli utenti**: creazione, permessi generali, ambito, attivazione ed
  eliminazione. Finora i permessi per utente erano una funzione teorica, perché l'unico
  account esistente era l'amministratore creato dall'installazione.
- Due protezioni impediscono di rendere il pannello ingestibile: **non ci si può
  chiudere fuori da soli** (togliersi i privilegi, disattivarsi o cancellarsi) e
  **l'ultimo amministratore non si tocca**, nemmeno da parte di un altro amministratore.
- Il cambio della propria password richiede quella attuale anche a chi ha già effettuato
  l'accesso: un token rubato non deve bastare a chiudere fuori il proprietario.
- I permessi generali (cosa può fare una persona) restano separati dai permessi per
  cartella (dove può farlo): rispondono a domande diverse, e mescolarli renderebbe
  illeggibili entrambi.
- **Ricerca** nei nomi dei file, ricorsiva a partire dalla cartella in cui ci si trova.
  I risultati mostrano il percorso completo, così non si perde il contesto, e passano dal
  controllo degli accessi voce per voce: una ricerca che mostrasse i nomi dentro una
  cartella vietata sarebbe un modo di leggerne il contenuto.
- Due tetti — ai risultati e alle cartelle visitate — non sono opzioni ma parte del
  progetto: su NFS ogni cartella è un giro di rete, e senza limiti una ricerca su
  centomila file terrebbe occupato un thread per minuti.
- **Scaricare una cartella intera come archivio ZIP**. L'archivio viene prodotto mentre
  lo si invia, non costruito prima su disco: una cartella del NAS può pesare più dello
  spazio libero della macchina. Il prezzo è che il browser non mostra la percentuale,
  perché la dimensione totale non è nota in anticipo.
- I file entrano nell'archivio **senza compressione**: su un NAS domestico il contenuto è
  quasi sempre già compresso, e comprimerlo di nuovo consuma processore per guadagnare
  qualche per mille.
- **Selezione multipla**: si scelgono più file e cartelle e si scaricano in un unico
  archivio. La barra della selezione è fissa in basso invece che nel flusso, perché
  comparendo fra le voci sposterebbe l'elenco alla prima scelta e la casella successiva
  finirebbe sotto il dito di chi sta selezionando.
- Ogni elemento della selezione viene **risolto contro la radice e ricontrollato**: la
  selezione arriva dal client, e fidarsi di ciò che dichiara significherebbe lasciargli
  decidere cosa scaricare.
- **Icone per tipo di file**, con una tinta per famiglia — immagini, video, audio,
  archivi, documenti, codice. Il colore fa da indice visivo quando l'elenco è lungo,
  molto più del nome dell'estensione.
- **La CI esegue i controlli a ogni push**: `ruff`, `mypy`, `pytest`, ESLint, `vue-tsc` e
  build. Prima girava solo la build della release, e un errore di tipo o un test rotto si
  scopriva al momento di rilasciare, cioè nel momento peggiore.
- **Anteprime**: immagini, video, audio, PDF e testo semplice si aprono nel pannello
  invece di essere scaricati. Il server concede l'apertura in linea **solo a questi
  tipi**: farlo per un tipo qualunque significherebbe farlo interpretare dal browser, e
  un file caricato da altri diventerebbe codice eseguito nel contesto del pannello.
  HTML e SVG restano allegati anche se l'anteprima li chiede.
- **Checksum SHA-256** calcolato su richiesta. Risponde a una domanda precisa: il file
  arrivato è identico a quello che c'era? Confrontare le dimensioni non basta — due file
  diversi possono pesare uguale. Viene letto a blocchi, perché caricarlo in memoria lo
  renderebbe impossibile proprio sui file per cui serve di più.
- **Import dei montaggi già presenti in `/etc/fstab`**: il pannello li legge, propone un
  identificatore e li prende in gestione. Ricopiarli a mano significa riscrivere server,
  percorsi e opzioni senza sbagliare, e poi accorgersi di aver dimenticato una riga.
- Commentare la riga di fstab è **un'azione separata e successiva**: finché entrambi sono
  attivi il sistema prova a montare due volte lo stesso percorso, ma disattivare prima di
  aver verificato il mount del pannello lascerebbe la cartella irraggiungibile.
- La riga non viene mai cancellata: viene commentata con un marcatore che dice chi l'ha
  spenta e quando, dopo una copia di sicurezza del file. Una riga sbagliata in `/etc/fstab`
  può impedire l'avvio della macchina.
- L'import parte sempre in **sola lettura**, anche quando la riga di fstab concedeva la
  scrittura: la scrittura si concede di proposito, non per eredità.
- **Registro dei trasferimenti e cruscotto dal vivo**: cosa è stato scaricato e caricato,
  da chi e da quale indirizzo, con aggiornamento in tempo reale.
- Il flusso dal vivo usa **SSE e non WebSocket**: qui i dati vanno in una sola direzione,
  e un WebSocket dietro Apache richiede `mod_proxy_wstunnel` e una configurazione in più
  che qualcuno dimenticherà. Una risposta che non finisce mai passa da qualunque proxy.
- **`X-Forwarded-For` viene letto solo dai proxy dichiarati fidati**: quell'intestazione la
  può scrivere chiunque, e fidarsene sempre permetterebbe a ogni visitatore di dichiarare
  l'indirizzo che preferisce.
- **Lettura dell'access log del web server** per i byte davvero trasferiti, con gestione
  della rotazione: senza, dopo la prima rotazione notturna il monitoraggio smetterebbe di
  aggiornarsi in silenzio. Finché quei byte non arrivano restano vuoti — un numero
  inventato sarebbe peggio di uno assente.
- **Impostazioni del pannello**: nome, sottotitolo e logo personalizzabili, e la scelta
  se elencare anche i file nascosti. Titolo e logo si leggono anche senza accedere,
  perché disegnano la pagina di accesso.
- **Spazio sui dischi**, comprese le condivisioni montate. Quello del disco del pannello
  sta accanto agli altri di proposito: è quello che ci si dimentica, e se si riempie il
  pannello smette di funzionare anche con il NAS mezzo vuoto.
- **Editor di testo** nell'anteprima, dove si ha il permesso di scrivere. Il salvataggio
  scrive un file accanto e poi lo rinomina al posto dell'originale: se la scrittura si
  interrompe a metà, il file di partenza è ancora quello di prima.
- **Caricamento di cartelle intere**, ricostruendo l'albero dall'altra parte.
- 196 test nuovi. Suite complessiva a **375 test**.

### Modificato
- In sviluppo la consegna passa da sola a `stream`: senza un web server davanti,
  `X-Sendfile` produce risposte vuote che sembrano un difetto del codice.
- `ruff` non analizza più le migrazioni di alembic: sono generate, e riformattarle le
  farebbe divergere da ciò che il comando rigenera.

## [0.5.0] - 2026-08-29

Le cartelle si pubblicano e si proteggono dall'interfaccia, e il pannello si
installa sul telefono.

### Aggiunto
- **Endpoint delle pubblicazioni**: elenco, creazione, modifica ed eliminazione delle
  cartelle pubblicate, con regole di visibilità per prefisso di percorso e permessi
  assegnati ai singoli utenti.
- **`prova-accesso`**: dice se un percorso è raggiungibile e **quale regola l'ha
  deciso**, con o senza utente. Configurare permessi a prefissi senza poterli
  verificare significa scoprire gli errori quando è troppo tardi.
- I prefissi vengono normalizzati prima di essere salvati: `foto`, `/foto` e `/foto/`
  sono la stessa regola, e una sola regola per percorso è ammessa — due
  renderebbero la decisione dipendente dall'ordine di lettura.
- L'assegnazione di un permesso è idempotente (`PUT`): riassegnare lo stesso percorso
  allo stesso utente ne cambia il livello invece di creare un secondo permesso che
  contraddirebbe il primo.
- 20 test sugli endpoint. Suite complessiva a **179 test**.
- **Interfaccia delle pubblicazioni**: elenco, creazione con identificatore proposto
  dal nome, regole per cartella, permessi per utente e **verifica dell'accesso nella
  stessa pagina**, che dice se una cartella è raggiungibile e quale regola lo decide.
  La voce «Pubblicazioni» del menu non è più in attesa.

- **Applicazione installabile (PWA)**: manifest, icone generate a partire dalla
  pastiglia delle condivisioni NFS — compresa la variante ritagliabile che i sistemi
  richiedono per l'icona in schermata home — e service worker con precache dei file
  del pannello.
  - Le chiamate all'API sono **sempre escluse dalla cache**: mostrare uno stato del
    sistema non più reale, su un pannello che monta filesystem, è peggio di un errore
    di rete.
  - L'aggiornamento **non si applica da solo**: compare un avviso e decide chi sta
    lavorando. Ricaricare il codice mentre qualcuno configura un mount è peggio che
    restare una versione indietro per qualche minuto.
  - Colore della barra del browser diverso per tema chiaro e scuro.

### Corretto
- **Il pannello è servito sotto `/pannello/`, ma il frontend era compilato come se
  stesse alla radice del sito**: in produzione i file non sarebbero stati trovati.
  Impostata la base e allineato il router.
- Un percorso con risalita passato alla verifica dell'accesso produceva un errore
  interno invece di una risposta comprensibile.
- Nella verifica, lasciare vuoto il campo utente per provare l'accesso **anonimo**
  inviava una stringa vuota anziché «nessun utente»: la verifica falliva, e l'errore
  veniva pure inghiottito lasciando la pagina muta. Ora l'anonimo funziona e gli
  errori si vedono.

### Da fare
Vedere [TODO.md](TODO.md).

## [0.4.0] - 2026-08-29

Il progetto diventa installabile su un server, e i permessi arrivano al singolo
utente.

### Aggiunto
- **`deploy/install.sh`**: installazione su server Linux, con messaggi in italiano e
  in inglese. Idempotente, con `--dry-run` per vedere cosa farebbe e `--uninstall`
  che lascia intatti dati e mount. Installa Python 3.14 *accanto* all'interprete di
  sistema, rileva Apache o Nginx, e prima di ricaricare il web server ne verifica la
  configurazione: se non è valida ripristina la precedente, così un errore qui non
  ferma gli altri siti ospitati sulla macchina.
- Modelli di configurazione per Apache e Nginx, da includere in un vhost esistente
  invece di sostituirlo.
- **Permessi per singolo utente** (`PermessoUtente`): stabilire quale utente accede a
  quale cartella, o a tutte. Un divieto esplicito batte la regola del percorso, così
  si può togliere a una persona un ramo che per gli altri resta aperto.
- Nuova visibilità `utenti_scelti`: il percorso è riservato a chi ha un permesso
  esplicito. Restano disponibili l'accesso anonimo (`pubblica`), la password e
  l'accesso a tutti gli utenti autenticati.
- Livelli di permesso: negato, lettura, scrittura.
- **Documentazione bilingue** per chi usa e installa il progetto: `README.en.md`,
  `docs/INSTALL.md` e la sua versione inglese, guida alla scrittura NFS su Synology
  nelle due lingue, con i collegamenti reciproci in cima a ogni documento.
- `docs/INSTALL.md`: prerequisiti, verifica del NAS prima di installare, cosa fa
  l'installer passo per passo, aggiornamento, disinstallazione e risoluzione dei
  problemi più frequenti.
- **`avvia-dev.ps1`**: avvia backend e frontend in sviluppo come schede della stessa
  finestra di Windows Terminal, con ripiego a finestre separate, e stampa gli
  indirizzi. Controlla prima che ambiente Python, dipendenze e `.env` esistano.

### Cambiato
- In sviluppo i servizi ascoltano su **tutte le interfacce**, così il pannello si può
  provare da telefono o tablet. Aggiunto `allowedHosts` perché Vite rifiuta gli Host
  che non conosce, come difesa dal rebinding DNS. Opzione `-SoloLocale` per tornare
  ad ascoltare solo su `127.0.0.1`.
- Il README non dichiara più che l'installer manca: ora esiste.

## [0.3.0] - 2026-08-29

I mount NFS si gestiscono dall'interfaccia, in due lingue.

### Aggiunto
- **Interfaccia bilingue, italiano e inglese**: menu, testi, messaggi d'errore e
  titolo della scheda. L'italiano è la lingua di riferimento e il tipo delle chiavi
  fa fallire la compilazione se l'inglese ne dimentica una.
- **Tema chiaro, scuro o automatico.** L'automatico non è un terzo colore ma
  l'assenza di scelta: non marca nulla sulla radice e segue il sistema operativo.
- **Barra laterale per categorie** — Archivio, Accessi, Sistema — con pulsanti in
  vetro traslucido e una pastiglia colorata per voce. Le voci non ancora realizzate
  restano visibili ma disattivate, con la fase indicata.
- Lingua e tema si scelgono anche dalla pagina di accesso.
- **Risoluzione sicura dei percorsi** (`services/percorsi.py`): il percorso finale si
  costruisce dalla radice e si verifica che non ne sia uscito. Il controllo è fatto
  sul percorso *risolto*, così un collegamento simbolico che punta fuori viene
  bloccato.
- **Permessi per sottocartella** (`services/acl.py`): vince la regola con il prefisso
  più lungo, quindi una sottocartella può essere più restrittiva di quella che la
  contiene. Il confronto è per componenti, non per stringhe.
- **Endpoint dei mount**: elenco, scoperta delle condivisioni di un NAS, creazione,
  modifica, avvio, arresto ed eliminazione. Tutti riservati agli amministratori.
- Client verso l'agent (`services/agent_client.py`), unico punto di contatto fra
  l'API e il processo privilegiato.
- **Interfaccia dei mount**: elenco con stato richiesto *e* effettivo affiancati,
  creazione con scoperta delle condivisioni dal NAS invece che percorso digitato a
  mano, montaggio, smontaggio, rilettura dello stato ed eliminazione con conferma.
- 41 test su percorsi e permessi, 25 sugli endpoint. Suite complessiva a **150 test**.

### Corretto
- Cambiando lingua il titolo della scheda restava nella precedente: veniva impostato
  solo alla navigazione, e cambiare lingua non cambia rotta.
- Il comando `typecheck` non intercettava errori che il `build` trovava, dando falsa
  sicurezza. Ora usa lo stesso controllo.
- La cartella di configurazione locale dell'editor era finita nel repository: rimossa,
  con la regola di ignore in `.git/info/exclude` e non in `.gitignore`, che viene
  pubblicato e conterrebbe a sua volta il nome della cartella.

## [0.2.0] - 2026-08-29

Fase 1 — autenticazione e agent privilegiato, entrambi verificati eseguendoli:
l'agent contro un NAS Synology reale, l'accesso dall'API e dal browser.

### Aggiunto
- **Agent privilegiato `anf-agent`**: socket Unix `0660`, protocollo JSON con
  insieme chiuso di verbi, validatori con whitelist, generazione di unit systemd,
  scoperta delle condivisioni NFS e lettura dello stato reale dei montaggi.
  Nessuna dipendenza esterna: usa solo la libreria standard.
- Autenticazione: Argon2id, token JWT, guardia sulle rotte, utente `admin` creato
  al primo avvio con avviso sulla password iniziale.
- Configurazione applicativa (`app/core/config.py`) letta da ambiente e `.env`,
  con validazione dei percorsi assoluti.
- Motore e sessioni SQLite (`app/core/database.py`) con i PRAGMA riapplicati a ogni
  connessione: `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout`.
- Modelli del database: `User`, `Mount`, `Share`, `AccessRule`, `ShareLink`,
  `Transfer`, `VHost`, `Setting`.
- Endpoint `/api/v1/health` e `/api/v1/health/ready`, quest'ultimo verifica davvero
  la raggiungibilità del database.
- **Suite di test: 84 test.** La parte più consistente copre i validatori
  dell'agent, cioè la barriera su cui poggia la sicurezza dell'intero progetto:
  slug con `..`, comandi iniettati nell'indirizzo del server, opzioni fuori
  whitelist, percorsi con risalita, verbi inventati. Più hash delle password,
  token manomessi, scaduti o firmati con un'altra chiave, e il flusso di accesso.
- Configurazione ruff unica in `ruff.toml` nella radice, così anche `agent/` e
  `tests/` rientrano negli stessi controlli del backend.
- Prima migrazione Alembic con supporto asincrono e `render_as_batch`, necessario
  perché SQLite non sa modificare una colonna con `ALTER`.
- Scheletro frontend: Vue 3, TypeScript, Vite, Pinia, Vue Router. Client HTTP con
  messaggi d'errore comprensibili, tema chiaro/scuro a tre stati, piede di pagina
  con versione e attribuzione letti dall'API.

### Cambiato
- Python 3.14 richiesto, installato dal PPA `deadsnakes` accanto all'interprete di
  sistema e non al suo posto.
- Versioni delle dipendenze fissate interrogando PyPI e npm anziché a memoria:
  correzioni fino a versioni maggiori intere (TypeScript 5→7, Vue Router 4→5,
  Pinia 3→4, mypy 1→2, pytest 8→9).
- **Database: SQLite in modalità WAL al posto di PostgreSQL.** Il profilo d'uso del
  pannello (pochi utenti, scritture rare, letture frequenti) è esattamente quello per
  cui SQLite è progettato. Elimina un servizio da installare, configurare e mantenere,
  e rende l'installazione molto più leggera.

### Corretto
- `pyproject.toml` indicava `readme = "../README.md"`: setuptools rifiuta i percorsi
  fuori dalla cartella del pacchetto e l'installazione falliva. Campo rimosso.
- TypeScript riportato alla 6.0.3: `typescript-eslint` stabile non supporta la 7, che
  ha solo build alpha. Rimosso `baseUrl`, deprecato nella 6 e rimosso nella 7.
- Client HTTP: con `exactOptionalPropertyTypes` attivo, `body: undefined` non equivale
  a omettere la proprietà. La richiesta viene ora costruita in modo condizionale.
- `setuptools` non riusciva a determinare i pacchetti da installare con `alembic/` e
  `.venv/` accanto ad `app/`: ora sono dichiarati esplicitamente.
- Lo stato di un mount non innescava l'automount e riportava sempre "non montato";
  e `findmnt` filtrato sul tipo `nfs` nascondeva i percorsi sotto automount, che
  compaiono prima come `autofs`. Entrambi trovati eseguendo, non leggendo.

### Nota
Il codice usa la sintassi PEP 758 (`except A, B:` senza parentesi), valida solo da
**Python 3.14**, coerentemente con `requires-python`.

## [0.1.0] - 2026-08-29

Fase 0 — fondamenta del progetto.

### Aggiunto
- Struttura del repository: `backend/`, `agent/`, `frontend/`, `deploy/`, `docs/`.
- Licenza MIT.
- Documentazione di progetto: [README.md](README.md), [docs/PIANO.md](docs/PIANO.md),
  [TODO.md](TODO.md), `memory.md`.
- Wiki operativa: [abilitare la scrittura NFS su Synology](docs/synology-nfs-scrittura.md).
- `.env.example` con tutte le voci di configurazione previste.
- `.gitignore` che esclude segreti, `.env`, dipendenze e dati locali.

### Deciso
- Separazione dei privilegi fra `anf-api` (non privilegiato) e `anf-agent` (root),
  con comandi tipizzati su socket Unix — mai stringhe di shell.
- Generazione di unit systemd `.mount`/`.automount` invece di righe in `/etc/fstab`.
- Consegna dei download delegata al web server (`X-Sendfile` su Apache,
  `X-Accel-Redirect` su Nginx) per ottenere il resume in modo nativo.
- Scrittura sui mount disattivata di default, con avviso di rischio.
- La shell integrata di FileBrowser **non** viene replicata, per sicurezza.
