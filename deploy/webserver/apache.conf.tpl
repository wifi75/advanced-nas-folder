# Advanced NAS Folder — Apache
#
# Modello. install.sh sostituisce @@RADICE@@, @@PORTA@@ e @@MOUNT_ROOT@@.
# Template. install.sh replaces @@RADICE@@, @@PORTA@@ and @@MOUNT_ROOT@@.
#
# Questo file non definisce un VirtualHost: si include in quello esistente,
# così il pannello convive con gli altri siti della macchina invece di
# sostituirli.

# --- indirizzo reale del client -------------------------------------------
# Dietro un reverse proxy che termina il TLS, senza questo ogni visitatore
# risulterebbe avere l'indirizzo del proxy e il monitoraggio dei download non
# distinguerebbe nessuno. Aggiungere qui gli indirizzi dei propri proxy.
RemoteIPHeader X-Forwarded-For
RemoteIPTrustedProxy 127.0.0.1

# Formato di log con l'indirizzo reale e i byte effettivamente inviati: è da
# qui che il pannello ricava lo stato dei download.
LogFormat "%a %t \"%r\" %>s %O %D \"%{User-Agent}i\"" anf
CustomLog /var/log/apache2/anf_access.log anf

# --- consegna dei file -----------------------------------------------------
# L'applicazione autorizza e risponde vuota indicando il file; è Apache a
# inviarlo. Così il resume delle richieste interrotte funziona in modo nativo
# e Python non resta occupato per la durata del trasferimento.
XSendFile On
XSendFilePath @@MOUNT_ROOT@@

# --- interfaccia -----------------------------------------------------------
Alias /pannello @@RADICE@@/frontend/dist

<Directory @@RADICE@@/frontend/dist>
    Options -Indexes +FollowSymLinks
    AllowOverride None
    Require all granted

    # L'interfaccia è un'applicazione a pagina singola: gli indirizzi interni
    # non corrispondono a file su disco e vanno tutti serviti dall'index.
    RewriteEngine On
    RewriteBase /pannello/
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule . /pannello/index.html [L]

    # I file compilati hanno il contenuto nel nome: si possono tenere a lungo.
    <FilesMatch "\.[0-9a-zA-Z]{8,}\.(js|css|woff2?)$">
        Header set Cache-Control "public, max-age=31536000, immutable"
    </FilesMatch>
    <FilesMatch "\.(html|webmanifest)$">
        Header set Cache-Control "no-cache"
    </FilesMatch>
</Directory>

# --- API -------------------------------------------------------------------
ProxyPreserveHost On
ProxyPass        /api/  http://127.0.0.1:@@PORTA@@/api/
ProxyPassReverse /api/  http://127.0.0.1:@@PORTA@@/api/
RequestHeader set X-Forwarded-Proto expr=%{REQUEST_SCHEME}
