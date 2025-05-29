#!/bin/bash
set -e

# Check if model exists - default to /tmp for writable filesystem
MODEL_PATH=${MODEL_PATH:-"/tmp/models/llama-2-7b-chat.gguf"}
MODEL_DIR=$(dirname "$MODEL_PATH")

if [ ! -f "$MODEL_PATH" ]; then
  echo "Model not found. Downloading model..."
  
  # Create model directory if it doesn't exist
  mkdir -p "$MODEL_DIR"
  
  # Download the model using huggingface-cli
  # Replace HF_TOKEN with your actual Huggingcat Face token
  if [ -z "$HF_TOKEN" ]; then
    echo "Error: HF_TOKEN environment variable not set. Cannot download model."
    exit 1
  fi
  
  # Use huggingface-cli to download the model
  huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF llama-2-7b-chat.Q4_K_M.gguf \
    --local-dir "$MODEL_DIR" \
    --local-dir-use-symlinks False \
    --token "$HF_TOKEN"
  
  # Rename the downloaded file to match expected path if needed
  if [ -f "$MODEL_DIR/llama-2-7b-chat.Q4_K_M.gguf" ] && [ "$MODEL_DIR/llama-2-7b-chat.Q4_K_M.gguf" != "$MODEL_PATH" ]; then
    mv "$MODEL_DIR/llama-2-7b-chat.Q4_K_M.gguf" "$MODEL_PATH"
  fi
  
  echo "Model downloaded to $MODEL_PATH"
else
  echo "Model already exists at $MODEL_PATH"
fi

# Execute the main command
exec "$@"
