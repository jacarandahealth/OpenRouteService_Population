# PowerShell script to fix ORS container on GCP instance
$INSTANCE_NAME = "ors-kenya-server"
$ZONE = "us-central1-a"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ORS Container Fix Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Connecting to GCP instance and running fix script..." -ForegroundColor Yellow
Write-Host ""

# Execute commands directly via SSH
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="cd /home/ors && docker-compose down 2>/dev/null || docker stop ors-app 2>/dev/null || true && docker rm ors-app 2>/dev/null || true"

Write-Host "[1/6] Container stopped" -ForegroundColor Green

gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="cd /home/ors && if [ ! -f 'kenya-latest.osm.pbf' ]; then echo 'Downloading Kenya OSM data...' && wget -q --show-progress https://download.geofabrik.de/africa/kenya-latest.osm.pbf -O kenya-latest.osm.pbf && echo 'Download complete'; else echo 'Kenya OSM data already exists'; ls -lh kenya-latest.osm.pbf; fi"

Write-Host "[2/6] Kenya OSM data checked" -ForegroundColor Green

gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="cd /home/ors && mkdir -p graphs elevation_cache logs/ors logs/tomcat conf"

Write-Host "[3/6] Directories created" -ForegroundColor Green

# Create docker-compose.yml
$dockerCompose = @"
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
"@

# Write docker-compose.yml to remote instance
$dockerCompose | gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="cd /home/ors && cat > docker-compose.yml"

Write-Host "[4/6] docker-compose.yml created" -ForegroundColor Green

gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="cd /home/ors && docker-compose up -d"

Write-Host "[5/6] Container started" -ForegroundColor Green

Start-Sleep -Seconds 5

Write-Host "[6/6] Checking container status..." -ForegroundColor Green
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="docker ps | grep ors-app"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Fix script completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Recent container logs:" -ForegroundColor Cyan
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="docker logs ors-app --tail 30"

Write-Host ""
Write-Host "IMPORTANT: Wait 15-20 minutes for ORS to build the routing graph." -ForegroundColor Yellow
Write-Host ""
Write-Host "Monitor progress:" -ForegroundColor Cyan
Write-Host "  gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='docker logs -f ors-app'" -ForegroundColor White
Write-Host ""
Write-Host "Test connection (after graph building completes):" -ForegroundColor Cyan
Write-Host "  python check_ors.py" -ForegroundColor White
Write-Host ""
