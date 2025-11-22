#!/bin/sh
set -e

echo "[INFO] Starting Synapse container..."

# Validate configuration (non-fatal, as in startup scripts)
echo "[INFO] Validating configuration..."
python config.py || echo "[WARN] Configuration validation failed, but continuing..."

# Ensure data files exist with correct permissions so they can be written to by the 'synapse' user
# This is important when mounting volumes from the host.
touch /app/memory.json /app/synapse_errors.log
chown synapse:synapse /app/memory.json /app/synapse_errors.log

echo "[INFO] Handing over to CMD..."
# Execute the command passed to the script (the Dockerfile's CMD)
exec "$@"
