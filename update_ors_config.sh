#!/bin/bash
# Script to update ORS to use Kenya OSM data
cd /home/ors

# Stop container
docker-compose down

# Remove old graphs to force rebuild
rm -rf graphs/*

# Create proper ORS config file
cat > conf/ors-config.yml << 'EOF'
ors:
  engine:
    source_file: /home/ors/files/kenya-latest.osm.pbf
  profiles:
    driving-car:
      enabled: true
      profiles:
        driving-car:
          enabled: true
EOF

# Update docker-compose to mount Kenya file to expected location
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
      - ./kenya-latest.osm.pbf:/home/ors/files/kenya-latest.osm.pbf
    environment:
      - BUILD_GRAPHS=True
      - ORS_ENGINE_SOURCE_FILE=/home/ors/files/kenya-latest.osm.pbf
      - "JAVA_OPTS=-Djava.awt.headless=true -server -XX:TargetSurvivorRatio=75 -XX:SurvivorRatio=64 -XX:MaxTenuringThreshold=3 -XX:+UseG1GC -XX:+ScavengeBeforeFullGC -XX:ParallelGCThreads=4 -Xms2g -Xmx8g"
EOF

# Start container
docker-compose up -d

echo "Container restarted. ORS will now build graph from Kenya OSM data."
echo "This will take 15-20 minutes. Monitor with: docker logs -f ors-app"

