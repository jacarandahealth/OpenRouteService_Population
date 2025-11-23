# Deploy ORS on GCP

$INSTANCE_NAME = "ors-kenya-server"
$ZONE = "us-central1-a"
$MACHINE_TYPE = "e2-standard-4" # 4 vCPUs, 16 GB memory
$IMAGE_PROJECT = "debian-cloud"
$IMAGE_FAMILY = "debian-11"

Write-Host "Creating Compute Engine instance..."
gcloud compute instances create $INSTANCE_NAME `
    --zone=$ZONE `
    --machine-type=$MACHINE_TYPE `
    --image-project=$IMAGE_PROJECT `
    --image-family=$IMAGE_FAMILY `
    --tags=ors-server `
    --metadata-from-file=startup-script=startup-script.sh

Write-Host "Creating firewall rule to allow port 8080..."
gcloud compute firewall-rules create allow-ors-8080 `
    --direction=INGRESS `
    --priority=1000 `
    --network=default `
    --action=ALLOW `
    --rules=tcp:8080 `
    --source-ranges=0.0.0.0/0 `
    --target-tags=ors-server

Write-Host ""
Write-Host "Deployment initiated. It may take 10-15 minutes for the instance to start and build the graphs."
Write-Host ""
Write-Host "Getting instance external IP address..."
Start-Sleep -Seconds 5  # Wait a moment for instance to be created

try {
    $IP_OUTPUT = gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="get(networkInterfaces[0].accessConfigs[0].natIP)" 2>&1
    if ($LASTEXITCODE -eq 0 -and $IP_OUTPUT) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Instance External IP: $IP_OUTPUT" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Update your config.yaml with:" -ForegroundColor Yellow
        Write-Host "  ors:" -ForegroundColor Yellow
        Write-Host "    base_url: `"http://$IP_OUTPUT:8080/ors`"" -ForegroundColor Yellow
        Write-Host "    health_url: `"http://$IP_OUTPUT:8080/ors/v2/health`"" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Or run: python get_gcp_ors_ip.py --update-config" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host "Could not retrieve IP address yet. Instance may still be starting." -ForegroundColor Yellow
        Write-Host "Run this command later to get the IP:" -ForegroundColor Yellow
        Write-Host "  python get_gcp_ors_ip.py" -ForegroundColor Cyan
    }
} catch {
    Write-Host "Could not retrieve IP address. Instance may still be starting." -ForegroundColor Yellow
    Write-Host "Run this command later to get the IP:" -ForegroundColor Yellow
    Write-Host "  python get_gcp_ors_ip.py" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Monitoring commands:"
Write-Host "  - Check status: gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE"
Write-Host "  - SSH into instance: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
Write-Host "  - Check logs: gcloud compute instances get-serial-port-output $INSTANCE_NAME --zone=$ZONE"
Write-Host "  - Get IP address: python get_gcp_ors_ip.py"
Write-Host ""
