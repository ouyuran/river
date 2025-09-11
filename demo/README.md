# How to run demo
uv run river

# Clean sandboxs
docker rmi -f $(docker images --format '{{.Repository}}:{{.Tag}}' | grep -w '^river-sandbox')