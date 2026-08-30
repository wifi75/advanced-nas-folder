"""Unica sorgente di verita per versione e attribuzione.

Ogni altro punto del progetto (FastAPI, endpoint di health, frontend) legge da qui.
Non duplicare questi valori altrove.
"""

APP_NAME = "Advanced NAS Folder"
APP_VERSION = "0.6.7"
APP_AUTHOR = "Tiziano Cassone"
APP_DESCRIPTION = (
    "Pannello self-hosted per montare condivisioni NFS, pubblicare cartelle "
    "con permessi per sottocartella e gestire file."
)

#: Riga di attribuzione mostrata a pie di pagina, backend e frontend.
APP_FOOTER = f"v{APP_VERSION} — Ideato e sviluppato da {APP_AUTHOR}"
