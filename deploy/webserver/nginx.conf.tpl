# Advanced NAS Folder — Nginx
#
# Modello. install.sh sostituisce @@RADICE@@, @@PORTA@@ e @@MOUNT_ROOT@@.
# Template. install.sh replaces @@RADICE@@, @@PORTA@@ and @@MOUNT_ROOT@@.

# "log_format" e' valido solo nel contesto "http": qui fuori dal blocco
# "server" funziona comunque, perche' Debian include questo file dentro il
# proprio blocco "http" (vedi /etc/nginx/nginx.conf). Dentro "server" invece
# nginx -t fallisce con «"log_format" directive is not allowed here» — bug
# trovato installando su un server pulito, corretto spostandolo qui.
log_format anf '$remote_addr $time_local "$request" $status '
               '$body_bytes_sent $request_time "$http_user_agent"';

server {
    listen 80;
    server_name _;

    # Nessun limite sul corpo delle richieste: si caricano file, non moduli.
    client_max_body_size 0;

    # Indirizzo reale del client dietro un reverse proxy che termina il TLS.
    # Senza, ogni visitatore risulterebbe avere l'indirizzo del proxy e il
    # monitoraggio dei download non distinguerebbe nessuno.
    set_real_ip_from 127.0.0.1;
    real_ip_header X-Forwarded-For;

    access_log /var/log/nginx/anf_access.log anf;

    # --- interfaccia -------------------------------------------------------
    location /pannello/ {
        alias @@RADICE@@/frontend/dist/;
        # Applicazione a pagina singola: gli indirizzi interni non
        # corrispondono a file su disco.
        try_files $uri $uri/ /pannello/index.html;
    }

    # I file compilati hanno il contenuto nel nome: si possono tenere a lungo.
    location ~* ^/pannello/.*\.[0-9a-zA-Z]{8,}\.(js|css|woff2?)$ {
        alias @@RADICE@@/frontend/dist/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # --- API ---------------------------------------------------------------
    location /api/ {
        proxy_pass http://127.0.0.1:@@PORTA@@;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }

    # --- consegna dei file -------------------------------------------------
    # Raggiungibile solo tramite X-Accel-Redirect dall'applicazione, mai
    # direttamente dall'esterno: è "internal" a garantirlo. L'applicazione
    # autorizza e indica il file, Nginx lo invia, e il resume delle richieste
    # interrotte funziona in modo nativo.
    location /__anf_internal/ {
        internal;
        alias @@MOUNT_ROOT@@/;
    }
}
