#!/usr/bin/bash
uvicorn front:app --port 8003
sleep 3
curl -X GET http://127.0.0.1:8003/health
