# Dependency versions

Project rule: **always use the latest stable versions.** Nothing old, no
unverified `latest`, no numbers written from memory.

*[Versione italiana](VERSIONI.md)*

---

## How to check them (the only valid way)

**Query the official registries.** Neither memory nor web searches are reliable
sources: both were contradicted by the registries on 2026-08-29, and not by a
little — TypeScript was reported at version 5 when it was already at 7, Pinia
at 2 when it was at 4.

### PyPI

```bash
curl -s https://pypi.org/pypi/NAME/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
```

### npm

```bash
curl -s https://registry.npmjs.org/NAME/latest | python3 -c "import sys,json;print(json.load(sys.stdin)['version'])"
```

For scoped packages, encode the special characters: `@vitejs/plugin-vue`
becomes `%40vitejs%2Fplugin-vue`.

---

## State as of 2026-08-29

### Backend (PyPI)

| Package | Version |
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
| zipstream-ng | 1.9.3 |
| pytest | 9.1.1 |
| pytest-asyncio | 1.4.0 |
| httpx | 0.28.1 |
| ruff | 0.16.5 |
| mypy | 2.3.1 |

### Frontend (npm)

| Package | Version |
|---|---|
| vue | 3.5.42 |
| vue-router | 5.3.0 |
| pinia | 4.0.3 |
| vite | 8.2.2 |
| **typescript** | **6.0.3** — see below |
| vue-tsc | 3.3.11 |
| @vitejs/plugin-vue | 6.0.8 |
| @types/node | 26.4.0 |
| eslint | 10.9.1 |
| @eslint/js | 10.0.1 |
| eslint-plugin-vue | 10.10.0 |
| typescript-eslint | 8.68.0 |
| globals | 17.11.0 |
| jiti | 2.7.0 |

### The one exception: TypeScript stays at 6.0.3

TypeScript 7.0.2 exists and is stable, but **the ecosystem has not caught up**:
stable `typescript-eslint` declares `typescript >=4.8.4 <6.1.0`, and only
*alpha* builds exist for 7. Verified with a real installation, which indeed
fails.

The alternatives were giving up the typed linter or installing alpha packages:
both worse than staying one major version behind on a compiler.

The configuration is nonetheless ready for 7: `baseUrl` was removed from
`tsconfig.app.json` because it is deprecated in 6 and gone in 7.

**To be reconsidered** when `typescript-eslint` ships a compatible stable
release.

### Platform

| | Version | Note |
|---|---|---|
| Python | **3.14** required | upstream is at 3.14.7; the `deadsnakes` PPA for Ubuntu 24.04 provides 3.14.6 |
| Node.js | 24.18.1 LTS | needed by CI only, never on the server |
| SQLite | Python standard library | WAL mode |

---

## Points to validate on the first build

Some of these versions are very recent major bumps. They are to be used, but
the first build deserves a look:

- ~~**TypeScript 7**~~ — checked: the ecosystem is not ready, we stay at 6.0.3.
- ~~**mypy 2.x**~~ — checked on 2026-08-29: `mypy --strict` passes cleanly on
  the whole backend.
- ~~**Vite 8 + vue-tsc 3.3.11**~~ — checked: full build in 184 ms.
- **Vue Router 5** and **Pinia 4** have breaking changes compared with the
  previous versions: follow the official migration guides, not the examples
  found online, most of which are still on versions 4 and 2.
- **pytest 9** removed features deprecated in the 8 series.

---

## Python: installed alongside, never in place of

Ubuntu 24.04 ships Python 3.12, and the system itself depends on it. The
project uses 3.14 from the `deadsnakes` PPA, which installs it **next to** the
system interpreter:

```bash
add-apt-repository -y ppa:deadsnakes/ppa
apt-get install -y python3.14 python3.14-venv python3.14-dev
python3.14 -m venv /var/www/advanced-nas-folder/venv
```

`python3` keeps pointing at 3.12. **Never move that link** with
`update-alternatives`: the operating system and the other applications on the
machine run on top of it. The project's venv must be created explicitly with
`python3.14`.

## When to update

At every work cycle, before a release. Re-run the registry queries, update
`pyproject.toml`, `package.json` and this table in the same commit, and note
major version changes in `CHANGELOG.md`.
