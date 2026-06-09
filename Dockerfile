FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (excluding those in .gitignore)
COPY . .

# Expose port 7860 (Hugging Face Spaces standard port)
EXPOSE 7860

# Command to run FastAPI server
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "7860"]
