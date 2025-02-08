# OpenAI_Sudoku_Agentic

This repository contains code to create a Sudoku Solver microservice and UI.
These code were generated using OpenAI o3-mini-high.

Note: This code uses ChatGPT APIs.

## Prerequisites

* You will need to have an OpenAI API account, with available usage tokens for ChatGPT4.
* You will also need an API Key, which you can create from https://platform.openai.com/account/api-keys
* Python 3.12 with libraries FastAPI, Pydantic (see requirements.txt)

## Steps to Run Microservice Locally

1. Install the required libraries.
   ```
   pip install -r requirements.txt
   ```
2. Export your OpenAI keys as environment variables.
   ```
   export OPENAI_API_KEY=xxxx
   export OPENAI_API_KEY=yyyy
   ``` 
3. Generate your self-signed certificates.
   ```
   openssl req -x509 -newkey rsa:4096 -nodes \
     -out mydomain-cert.pem \
     -keyout mydomain-priv.pem -days 365
   ```
   For example, I'm using `mydomain.com` as my `CN`.
   If you change the file names, you will have to change the filenames in `Dockerfile` and in the `privacy_ms.py` file.
4. Edit `/etc/hosts`:
   ```
   vim /etc/hosts
   ```
   Add an entry for your domain.
   ```
   127.0.0.1   localhost mydomain.com
   ```
5. Start up the microservice.
   ```
   uvicorn sudoku_ms:app --reload \
     --ssl-certfile certs/mydomain-cert.pem \
     --ssl-keyfile certs/mydomain-priv.pem 
   ```
6. Load up the browser to point to your domain, e.g. `https://mydomain.com:8000`
7. Access the `/docs` endpoint.


## Steps to Run As Dockerised Web Service

1. Build and start up the services.
   ```
   ./rebuild.sh 
   ```
2. Check that the container is up.
   ```
   docker compose ps -a
   ```
