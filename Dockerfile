FROM python:3.11-slim

WORKDIR /app

# Install basic network tools and docker client for plugins
RUN apt-get update && \
    apt-get install -y nmap curl docker.io && \
    rm -rf /var/lib/apt/lists/*

COPY . /app/

# Install python dependencies
# RUN pip install -r requirements.txt (if we had external deps)

ENTRYPOINT ["python", "hexagent.py"]
CMD ["--engagement", "default"]
