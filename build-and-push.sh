#!/bin/bash
set -e

REGISTRY="ghcr.io/hacker-home-chile"
IMAGE_NAME="ledfx"
TAG="${1:-latest}"

echo "Building and pushing ${REGISTRY}/${IMAGE_NAME}:${TAG} for linux/amd64..."

docker buildx build \
    --platform linux/amd64 \
    -f ledfx_docker/Dockerfile \
    -t "${REGISTRY}/${IMAGE_NAME}:${TAG}" \
    --push \
    .

echo "Done! Image pushed to ${REGISTRY}/${IMAGE_NAME}:${TAG}"
