#!/bin/bash
# Script to fix ORS container on GCP instance
# Run this via: gcloud compute ssh ors-kenya-server --zone=us-central1-a --command="bash -s" < fix_ors_container.sh

set -e

cd /home/ors

echo "Stopping current ORS container..."
docker-compose down || docker stop ors-app || true

echo "Checking if Kenya OSM file exists..."
if [ ! -f "kenya-latest.osm.pbf" ]; then
    echo "Downloading Kenya OSM file..."
    wget https://download.geofabrik.de/africa/kenya-latest.osm.pbf -O kenya-latest.osm.pbf
fi

echo "Verifying docker-compose.yml exists..."
if [ ! -f "docker-compose.yml" ]; then
    echo "Creating docker-compose.yml..."
    cat > docker-compose.yml << 'EOF'
version: '2.4'
services:
  ors-app:
    container_name: ors-app
    ports:
      - "8080:8080"
      - "9001:9001"
    image: openrouteservice/openrouteservice:latest
    restart: always
    volumes:
      - ./graphs:/home/ors/ors-core/data/graphs
      - ./elevation_cache:/home/ors/ors-core/data/elevation_cache
      - ./logs/ors:/home/ors/ors-core/logs/ors
      - ./logs/tomcat:/home/ors/ors-core/logs/tomcat
      - ./conf:/home/ors/ors-conf
      - ./kenya-latest.osm.pbf:/home/ors/ors-core/data/osm_file.pbf
    environment:
      - BUILD_GRAPHS=True
      - "JAVA_OPTS=-Djava.awt.headless=true -server -XX:TargetSurvivorRatio=75 -XX:SurvivorRatio=64 -XX:MaxTenuringThreshold=3 -XX:+UseG1GC -XX:+ScavengeBeforeFullGC -XX:ParallelGCThreads=4 -Xms2g -Xmx8g"
EOF
fi

echo "Starting ORS container with correct configuration..."
docker-compose up -d

echo "Waiting for container to start..."
sleep 10

echo "Checking container status..."
docker ps | grep ors-app

echo "Container logs (last 20 lines):"
docker logs ors-app --tail 20

echo ""
echo "Testing health endpoint in 30 seconds (ORS needs time to initialize)..."
sleep 30
curl -s http://localhost:8080/ors/v2/health || echo "Health check failed - ORS may still be initializing"

echo ""
echo "Done! Check logs with: docker logs -f ors-app"

