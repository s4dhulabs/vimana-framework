FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WEB2PY_PASSWORD=admin123
ENV WEB2PY_ADMIN_EMAIL=admin@example.com

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install psutil

# Create app directory
WORKDIR /app

# Create uploads directory
RUN mkdir -p uploads

# Copy vulnerable Web2py application
COPY web2py_app.py /app/web2py_app.py

# Set permissions
RUN chmod +x /app/web2py_app.py

# Expose port
EXPOSE 8080

# Start the vulnerable Web2py application
CMD ["python", "web2py_app.py"] 