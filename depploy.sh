#!/bin/bash
# deploy.sh - Production deployment script

echo "🚀 Starting deployment..."

# 1. Stop any running containers
docker-compose down

# 2. Pull latest changes (if using git)
# git pull origin main

# 3. Build and start services without nginx
docker-compose up -d postgres backend

# 4. Wait for services to be ready
sleep 10

# 5. Get SSL certificates (first time only)
echo "📝 Obtaining SSL certificates..."
docker run --rm \
  -v ./certbot-etc:/etc/letsencrypt \
  -v ./certbot-var:/var/www/certbot \
  certbot/certbot certonly \
  --webroot -w /var/www/certbot \
  --email admin@seyha.online \
  -d classified-artical.seyha.online \
  -d www.classified-artical.seyha.online \
  --agree-tos \
  --non-interactive \
  --dry-run  # Remove --dry-run for real certificates

# 6. Start nginx with HTTPS
docker-compose up -d nginx

echo "✅ Deployment complete!"
echo "🌐 Access your application at: https://classified-artical.seyha.online"