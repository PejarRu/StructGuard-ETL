#!/bin/bash
set -e

echo "🚀 Deploying StructGuard API to VPS..."

# Variables
VPS_HOST="root@91.99.142.12"
DEPLOY_DIR="/opt/structguard"
REPO_URL="https://github.com/PejarRu/StructGuard-ETL.git"

# SSH and deploy
ssh $VPS_HOST << 'ENDSSH'
set -e

# Create deploy directory
mkdir -p /opt/structguard
cd /opt/structguard

# Clone or pull latest
if [ -d ".git" ]; then
    echo "📦 Pulling latest changes..."
    git pull origin main
else
    echo "📦 Cloning repository..."
    git clone https://github.com/PejarRu/StructGuard-ETL.git .
fi

# Build and deploy with Docker Swarm Stack
cd structguard
echo "🐳 Building Docker image..."
docker build -t structguard-api:latest .

echo "🚢 Deploying to Docker Swarm..."
docker stack deploy -c docker-compose.yml structguard

echo "✅ Deployment complete!"
docker stack ps structguard
ENDSSH

echo "✅ Deployment script finished!"
