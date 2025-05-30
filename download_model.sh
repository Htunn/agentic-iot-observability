#!/bin/bash

# Define model path and URL
MODEL_PATH="./llm_service/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/microsoft/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_DIR="$(dirname "$MODEL_PATH")"

# Print status message
echo "Checking for TinyLlama model at $MODEL_PATH"

# Create directory if it doesn't exist
if [ ! -d "$MODEL_DIR" ]; then
  echo "Creating directory: $MODEL_DIR"
  mkdir -p "$MODEL_DIR"
fi

# Download the model if it doesn't exist
if [ -f "$MODEL_PATH" ]; then
  echo "Model already exists. Skipping download."
else
  echo "Model not found. Downloading from $MODEL_URL"
  echo "This may take a while depending on your internet connection..."
  
  # Check if curl or wget is available
  if command -v curl &>/dev/null; then
    curl -L "$MODEL_URL" -o "$MODEL_PATH"
  elif command -v wget &>/dev/null; then
    wget -O "$MODEL_PATH" "$MODEL_URL"
  else
    echo "Error: Neither curl nor wget is installed. Please install one of them to download the model."
    exit 1
  fi
  
  # Verify the download
  if [ -f "$MODEL_PATH" ]; then
    echo "Model downloaded successfully to $MODEL_PATH"
  else
    echo "Error: Failed to download model"
    exit 1
  fi
fi

echo "Model is ready at $MODEL_PATH"