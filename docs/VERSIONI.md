# Versioni delle dipendenze

Regola del progetto: **si usano sempre le ultime versioni stabili.** Niente di vecchio,
niente `latest` non verificato, niente numeri scritti a memoria.

---

## Come si verificano (l'unico modo valido)

**Interrogare i registri ufficiali.** Né la memoria né le ricerche web sono fonti
attendibili: sono state entrambe smentite dai registri il 2026-08-29, e non di poco —
TypeScript risultava alla versione 5 quando era già alla 7, Pinia alla 2 quando era
alla 4.

### PyPI

```bash
curl -s https://pypi.org/pypi/NOME/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
```

### npm

```bash
curl -s https://registry.npmjs.org/NOME/latest | python3 -c "import sys,json;print(json.load(sys.stdin)['version'])"
```

Per i pacchetti con scope, codificare i caratteri speciali:
`@vitejs/plugin-vue` diventa `%40vitejs%2Fplugin-vue`.

---

## Stato al 2026-08-29

### Backend (PyPI)

| Pacchetto | Versione |
|---|---|
| fastapi | 0.141.1 |
| uvicorn[standard] | 0.52.4 |
| pydantic | 2.13.5 |
| pydantic-settings | 2.15.0 |
| sqlalchemy | 2.0.52 |
| alembic | 1.19.1 |
| aiosqlite | 0.22.1 |
| argon2-cffi | 25.1.0 |
| pyjwt | 2.13.0 |
| python-multipart | 0.0.32 |
| pytest | 9.1.1 |
| pytest-asyncio | 1.4.0 |
| httpx | 0.28.1 |
| ruff | 0.16.5 |
| mypy | 2.3.1 |

### Frontend (npm)

| Pacchetto | Versione |
|---|---|
| vue | 3.5.42 |
| vue-router | 5.3.0 |
| pinia | 4.0.3 |
| vite | 8.2.2 |
| **typescript** | **6.0.3** — vedere sotto |
| vue-tsc | 3.3.11 |
| @vitejs/plugin-vue | 6.0.8 |
| @types/node | 26.4.0 |
| eslint | 10.9.1 |
| @eslint/js | 10.0.1 |
| eslint-plugin-vue | 10.10.0 |
| typescript-eslint | 8.68.0 |
| jiti | 2.7.0 |

### L'unica eccezione: TypeScript resta alla 6.0.3

TypeScript 7.0.2 esiste ed è stabile, ma **l'ecosistema non l'ha ancora raggiunta**:
`typescript-eslint` stabile dichiara `typescript >=4.8.4 <6.1.0`, e per la 7 esistono
solo build *alpha*. Verificato con un'installazione reale, che infatti fallisce.

Le alternative erano rinunciare al linter tipizzato o installare pacchetti alpha:
entrambe peggiori del restare una versione maggiore indietro su un compilatore.

La configurazione è comunque già pronta per la 7: `baseUrl` è stato rimosso da
`tsconfig.app.json` perché deprecato nella 6 ed eliminato nella 7.

**Da rivalutare** quando `typescript-eslint` pubblica una versione stabile compatibile.

### Piattaforma

| | Versione | Nota |
|---|---|---|
| Python | **3.14** richiesta | upstream è alla 3.14.7; il PPA `deadsnakes` per Ubuntu 24.04 fornisce la 3.14.6 |
| Node.js | 24.18.1 LTS | serve solo alla CI, mai sul server |
| SQLite | libreria standard di Python | modalità WAL |

---

## Punti da validare al primo build

Alcune di queste versioni sono cambi di versione maggiore molto recenti. Sono da usare,
ma il primo build va guardato:

- ~~**TypeScript 7**~~ — verificato: l'ecosistema non è pronto, si resta alla 6.0.3.
- ~~**mypy 2.x**~~ — verificato il 2026-08-29: `mypy --strict` passa pulito su tutto
  il backend.
- ~~**Vite 8 + vue-tsc 3.3.11**~~ — verificato: build completo in 184 ms.
- **Vue Router 5** e **Pinia 4** hanno modifiche non retrocompatibili rispetto alle
  versioni precedenti: seguire le guide di migrazione ufficiali, non gli esempi
  trovati online, che in larga maggioranza sono ancora fermi alle versioni 4 e 2.
- **pytest 9** ha rimosso funzionalità deprecate nella serie 8.

---

## Python: si installa affiancato, mai al posto

Ubuntu 24.04 distribuisce Python 3.12, e il sistema stesso ne dipende. Il progetto usa
la 3.14 dal PPA `deadsnakes`, che la installa **accanto** all'interprete di sistema:

```bash
add-apt-repository -y ppa:deadsnakes/ppa
apt-get install -y python3.14 python3.14-venv python3.14-dev
python3.14 -m venv /var/www/advanced-nas-folder/venv
```

`python3` continua a puntare alla 3.12. **Non spostare mai quel collegamento** con
`update-alternatives`: ci girano sopra il sistema operativo e le altre applicazioni
presenti sulla macchina. Il venv del progetto va creato esplicitamente con
`python3.14`.

## Quando aggiornare

A ogni ciclo di lavoro, prima di un rilascio. Rilanciare le interrogazioni ai registri,
aggiornare `pyproject.toml`, `package.json` e questa tabella nello stesso commit, e
annotare in `CHANGELOG.md` i cambi di versione maggiore.
