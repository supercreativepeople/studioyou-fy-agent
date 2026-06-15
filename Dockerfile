# FutureYou LiveKit Agent — deploy with: lk agent deploy
#
# Standard LiveKit Agents Dockerfile pattern. The `download-files` step
# pre-fetches VAD/turn-detector model weights at build time so the worker
# doesn't pull them on every cold start.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download model files (Silero VAD, etc.) at build time.
RUN python agent.py download-files

CMD ["python", "agent.py", "start"]
