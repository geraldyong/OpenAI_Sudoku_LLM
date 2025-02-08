# Use an official lightweight Python image.
FROM python:3.12-slim

# Create app user.
# Use this for non-alpine.
#RUN useradd --user-group --system --no-log-init --create-home appusr
# Use this for alpine.
RUN addgroup --system apps --gid 1000 && adduser --system appuser --uid 1000 --gid 1000

# Set the working directory in the container.
WORKDIR /app

# Copy requirements.txt and install dependencies.
COPY --chown=appuser:apps *.py  /app
COPY --chown=appuser:apps requirements.txt /app
COPY --chown=appuser:apps certs /app/certs

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "uvicorn[standard]" && \
    rm -f /app/requirements.txt

USER appuser

# Expose the port the app runs on.
EXPOSE 8000

# Run the FastAPI app with Uvicorn.
CMD ["uvicorn", "sudoku_ms:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["uvicorn", "sudoku_ms:app", "--host", "0.0.0.0", "--reload", "--ssl-keyfile", "certs/geraldyong-priv.pem", "--ssl-certfile", "certs/geraldyong-cert.pem"]
