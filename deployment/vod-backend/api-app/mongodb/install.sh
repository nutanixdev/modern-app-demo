#!/bin/bash

# Add the Bitnami repository to Helm 
helm repo add bitnami https://charts.bitnami.com/bitnami

# Deploy the chart
helm install \
mongodb bitnami/mongodb \
--version 13.6.2 \
--namespace vod-backend \
-f values.yaml
 