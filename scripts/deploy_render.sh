#!/bin/bash
# Deploy to Render
# Usage: ./scripts/deploy_render.sh

set -e

# Checks
if ! command -v render &> /dev/null; then
    echo "Error: 'render' CLI not found."
    echo "Please install it: https://render.com/docs/cli"
    echo "Or deploy via Dashboard by pushing to main."
    exit 1
fi

echo "Validating Render configuration..."
# Basic check for render.yaml
if [ ! -f "render.yaml" ]; then
    echo "Error: render.yaml not found in root."
    exit 1
fi

echo "Deploying to Render..."
# This command automatically finds render.yaml and applies it
render deploy render.yaml

echo "Deployment triggered. Monitor status via Dashboard or 'render logs'."
