#!/bin/sh
# Substitute only our custom env vars in nginx.conf, leaving nginx's own
# $variables (like $host, $scheme, $request_uri) untouched.
set -e

# Defaults for local development
: "${NGINX_SERVER_NAME:=localhost}"
: "${NGINX_SSL_CERT:=/etc/nginx/ssl/varuna.crt}"
: "${NGINX_SSL_KEY:=/etc/nginx/ssl/varuna.key}"

export NGINX_SERVER_NAME NGINX_SSL_CERT NGINX_SSL_KEY

envsubst '${NGINX_SERVER_NAME} ${NGINX_SSL_CERT} ${NGINX_SSL_KEY}' \
    < /etc/nginx/nginx.conf.template \
    > /etc/nginx/nginx.conf

exec nginx -g 'daemon off;'
