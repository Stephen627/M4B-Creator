FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the script
COPY convert_to_m4b.py .

# Define the entrypoint
ENTRYPOINT ["python", "convert_to_m4b.py"]
