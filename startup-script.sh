#!/bin/bash

# Update and install dependencies
apt-get update
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Install Docker
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create working directory
mkdir -p /home/ors
cd /home/ors

# Download Kenya OSM PBF
wget https://download.geofabrik.de/africa/kenya-latest.osm.pbf -O kenya-latest.osm.pbf

# Create config directory
mkdir -p conf

# Download default ORS config (we can customize if needed, but default usually works for basic car profile)
# Using a known compatible config or the default from the repo
wget https://raw.githubusercontent.com/GIScience/openrouteservice/master/openrouteservice/src/main/resources/ors-config-sample.json -O conf/ors-config.json

# Write docker-compose.yml (embedding it here to ensure it exists on the VM)
cat <<EOF > docker-compose.yml
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

# Start ORS
docker-compose up -d
