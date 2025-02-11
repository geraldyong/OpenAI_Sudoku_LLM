# OpenAI_Sudoku_LLM

This repository contains code to create a Sudoku Solver microservice and UI. It also features using an LLM
to propose the next move.
These code were generated using OpenAI o3-mini-high.

Note: This code uses ChatGPT APIs.

## Prerequisites

* You will need to have an OpenAI API account, with available usage tokens for ChatGPT4.
* You will also need an API Key, which you can create from https://platform.openai.com/account/api-keys
* Python 3.12 with libraries FastAPI, Pydantic (see requirements.txt)
* Docker on Linux (or Docker Desktop for MacOS)

## Steps to Run As Dockerised Web Service

1. Build and start up the services.
   ```
   ./rebuild.sh 
   ```
2. Check that the container is up.
   ```
   docker compose ps -a
   ```
