# Introduction

This repo contains my Azure IoT Edge sandbox

## Deploy from local

### Prerequisites
- Have Contributor acces to an Azure subscription
- Install Azure CLI
- Have a raspberry PI with Raspberry Pi OS installed
- Being able to SSH into your Raspberry Pi
- Install VS Code with following extensions
  - Azure IoT Tools (vsciot-vscode.azure-iot-tools)

```bash
az login

stack_name='dev' && \
resource_group_name="rg-raspi-sandbox-$stack_name" && \
deployment_name="deploy-$stack_name" && \
pi_hostname='pi4b' && \ # replace with hostname/ip of raspberry pi
device_id='pi4b' # replace device id to be registered in IoT Hub

# create resource group
az group create --location 'westeurope' --name $resource_group_name

# deploy resources
az deployment group create \
    --name $deployment_name \
    --resource-group $resource_group_name \
    --template-file 'azuredeploy.json'

# extract deployment outputs
iot_hub_name=$(az deployment group show -g $resource_group_name -n $deployment_name --query properties.outputs.iotHubName.value -o tsv)
iot_hub_resource_id=$(az deployment group show -g $resource_group_name -n $deployment_name --query properties.outputs.iotHubResourceId.value -o tsv)
log_analytics_workspace_id=$(az deployment group show -g $resource_group_name -n $deployment_name --query properties.outputs.logAnalyticsWorkspaceId.value -o tsv)
log_analytics_workspace_key=$(az deployment group show -g $resource_group_name -n $deployment_name --query properties.outputs.logAnalyticsWorkspaceKey.value -o tsv)
acr_server=$(az deployment group show -g $resource_group_name -n $deployment_name --query properties.outputs.acrServer.value -o tsv)
acr_username=$(az deployment group show -g $resource_group_name -n $deployment_name --query properties.outputs.acrUsername.value -o tsv)
acr_password=$(az deployment group show -g $resource_group_name -n $deployment_name --query properties.outputs.acrPassword.value -o tsv)

# login acr
az acr login -n $acr_server

# register IoT Edge device
az iot hub device-identity create --hub-name $iot_hub_name --device-id $device_id --edge-enabled
connection_string=$(az iot hub device-identity connection-string show --hub-name $iot_hub_name --device-id $device_id -o tsv)

# generate iot edge config file
eval "cat <<EOF
$(<config.toml.template)
EOF
" 1>'config.toml'

# transfer config file to raspberry pi
scp 'config.toml' $pi_hostname:~/

# ssh into raspberry pi
ssh $pi_hostname 

# install microsoft repo 
curl https://packages.microsoft.com/config/debian/stretch/multiarch/prod.list > ./microsoft-prod.list
sudo mv ./microsoft-prod.list /etc/apt/sources.list.d/
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv ./microsoft.gpg /etc/apt/trusted.gpg.d/
sudo apt-get update

# install moby engine
sudo apt-get install moby-engine

# install iot edge
sudo apt-get install aziot-edge

# copy config file
sudo mv config.toml /etc/aziot/

# update iotedge config
sudo iotedge config apply

# check iot edge logs
sudo iotedge system logs -- -f # Ctrl+C to break out

# exit ssh session and go back to host
exit

# generate .env file
eval "cat <<EOF
$(<.env.template)
EOF
" 1>'.env'

# In VS code, right click on deployment.template.json and select "Generate IoT Edge Deployment Manifest" -->
# This should generate config/deployment.arm32v7.json

# deploy the modules to iot edge device
az iot edge set-modules --device-id $device_id --hub-name $iot_hub_name --content 'config/deployment.arm32v7.json'

```