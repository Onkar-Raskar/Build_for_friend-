FROM ollama/ollama:latest
ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_KEEP_ALIVE=30m
RUN ollama serve & sleep 6 && ollama pull qwen2.5:3b && pkill ollama || true
EXPOSE 11434