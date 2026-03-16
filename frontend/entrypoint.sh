#!/bin/sh
# Substitute BACKEND_URL into the nginx config template at runtime,
# then start nginx. This lets the same image work in both docker-compose
# (BACKEND_URL=http://backend:8000) and Azure (BACKEND_URL=https://...).
set -e

: "${BACKEND_URL:=http://backend:8000}"
export BACKEND_URL

envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/default.conf.template \
    > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
