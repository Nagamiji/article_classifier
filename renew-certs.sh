#!/bin/bash
# renew-certs.sh - SSL certificate renewal

echo "🔄 Renewing SSL certificates..."

docker run --rm \
  -v ./certbot-etc:/etc/letsencrypt \
  -v ./certbot-var:/var/www/certbot \
  certbot/certbot renew \
  --quiet

# Reload nginx to use new certificates
docker-compose exec nginx nginx -s reload

echo "✅ Certificates renewed!"