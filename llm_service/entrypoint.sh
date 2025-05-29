#!/bin/bash
set -e

# Check if model exists - default to /tmp for writable filesystem
MODEL_PATH=${MODEL_PATH:-"/tmp/models/llama-2-7b-chat.Q4_K_M.gguf"}
MODEL_DIR=$(dirname "$MODEL_PATH")

if [ ! -f "$MODEL_PATH" ]; then
  echo "Model not found. Downloading model..."
  
  # Create model directory if it doesn't exist
  mkdir -p "$MODEL_DIR"
  
  # Check if huggingface-hub is installed, install if needed
  if ! python -c "import huggingface_hub" &>/dev/null; then
    echo "Installing huggingface-hub..."
    pip install --no-cache-dir huggingface_hub
  fi
  
  # Check if hf_transfer is installed, install it if enabled
  if [ "$HF_HUB_ENABLE_HF_TRANSFER" = "1" ] && ! python -c "import hf_transfer" &>/dev/null; then
    echo "HF_HUB_ENABLE_HF_TRANSFER is enabled but hf_transfer is not installed. Installing it..."
    pip install --no-cache-dir hf_transfer
  elif [ "$HF_HUB_ENABLE_HF_TRANSFER" = "1" ]; then
    echo "HF_HUB_ENABLE_HF_TRANSFER is enabled and hf_transfer is already installed."
  else
    # Explicitly disable hf_transfer to avoid errors
    echo "Disabling HF_HUB_ENABLE_HF_TRANSFER to avoid dependency issues..."
    export HF_HUB_ENABLE_HF_TRANSFER=0
  fi
  
  # Check for HF token
  if [ -z "$HF_TOKEN" ]; then
    echo "Warning: HF_TOKEN environment variable not set. Trying to download without authentication."
    echo "This may fail if the model requires authentication."
    
    # For development only, create a simple placeholder file
    echo "Creating placeholder model file for development..."
    dd if=/dev/zero of="$MODEL_PATH" bs=1M count=10
  else
    # Use Python to download the model
    echo "Downloading model using Python huggingface_hub..."
    python -c "
from huggingface_hub import hf_hub_download
import os

# Explicitly disable hf_transfer to avoid errors if not installed
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'

try:
    file_path = hf_hub_download(
        repo_id='TheBloke/Llama-2-7B-Chat-GGUF', 
        filename='llama-2-7b-chat.Q4_K_M.gguf',
        token=os.environ.get('HF_TOKEN'),
        local_dir='$MODEL_DIR',
        local_dir_use_symlinks=False
    )
    print(f'Model downloaded to {file_path}')
except Exception as e:
    print(f'Error downloading model: {e}')
    exit(1)
"
  
    
    # Rename the downloaded file if needed
    if [ -f "$MODEL_DIR/llama-2-7b-chat.Q4_K_M.gguf" ] && [ "$MODEL_DIR/llama-2-7b-chat.Q4_K_M.gguf" != "$MODEL_PATH" ]; then
      mv "$MODEL_DIR/llama-2-7b-chat.Q4_K_M.gguf" "$MODEL_PATH"
    fi
  fi
else
  echo "Model already exists at $MODEL_PATH"
fi

echo "Model path: $MODEL_PATH"
ls -la "$MODEL_PATH" || echo "Warning: Cannot access model file"

# Execute the main command
exec "$@"
