#!/bin/bash

# 1. Reading and exposing custom environment variables to Docker
# This option under explictely enables "auto export of variable"
#   from here on, ensuring custom variables will be "exposed" to docker
#   because running it will create a subprocess.
set -o allexport
# We read and autoexport all our custom variables
source .env
# We stop the autoexport mode.
set +o allexport

# 2. Checking if the chosen LLM model is a local one thus requiring ollama service.
if [[ "$LLM_MODEL_NAME" == *"ollama"* ]]; then
  echo "Local LLM model chosen ($LLM_MODEL_NAME): enabling docker profile to enable Ollama service."
  export COMPOSE_PROFILES=ollama
else
  echo "Non-local model chosen ($LLM_MODEL_NAME): Ollama ignored."
fi

# 3. Running all docker services, with potentially 'ollama' one if
#    COMPOSE_PROFILES was set to 'ollama'.
docker compose up -d 

# 4. Optional step specific to the use case where a local model was chosen.
if [[ "$LLM_MODEL_NAME" == *"ollama"* ]]; then
  
  # We must recreate the container name spawned from docker compose file.
  CONTAINER_NAME="${COMPOSE_PROJECT_NAME}-ollama"

  # Must wait for ollama service container to be up and ready.
  echo "Waiting for ollama handler to be ready to process requests..."
  until docker exec "$CONTAINER_NAME" ollama list > /dev/null 2>&1; do
    sleep 2
  done

  # Extract model name because we know its ollama/<name> (ex "ollama/llama3" -> "llama3")
  MODEL_TAG=$(echo "$LLM_MODEL_NAME" | cut -d'/' -f2)

  # Downloading if the model is not already present in related docker volume.
  if docker exec "$CONTAINER_NAME" ollama list | grep -q "$MODEL_TAG"; then
    echo "Model '$MODEL_TAG' already present, all is fine."
  else
    echo "Model '$MODEL_TAG' must be downloaded before requests can be made..."
    docker exec -t "$CONTAINER_NAME" ollama pull "$MODEL_TAG"
    echo "Download successfully finished, enjoy!"
  fi
fi
