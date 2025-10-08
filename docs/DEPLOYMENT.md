# Deployment Guide

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.12+
- 2GB RAM minimum
- 10GB disk space
- Domain name (optional but recommended)

## Deployment Options

### Option 1: Manual Deployment

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-venv python3.12-dev -y

# Install system dependencies
sudo apt install git nginx certbot python3-certbot-nginx -y
```

#### 2. Clone and Configure

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/youtube-summarizer-agent.git
cd youtube-summarizer-agent

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your API keys
```

#### 3. Create Systemd Service

Create `/etc/systemd/system/youtube-summarizer.service`:

```ini
[Unit]
Description=YouTube Summarizer Agent
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/youtube-summarizer-agent
Environment="PATH=/opt/youtube-summarizer-agent/.venv/bin"
ExecStart=/opt/youtube-summarizer-agent/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable youtube-summarizer
sudo systemctl start youtube-summarizer
sudo systemctl status youtube-summarizer
```

#### 4. Configure Nginx

Create `/etc/nginx/sites-available/youtube-summarizer`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # SSE support
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/youtube-summarizer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. SSL Certificate (Optional but Recommended)

```bash
sudo certbot --nginx -d yourdomain.com
```

---

### Option 2: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create cache directory
RUN mkdir -p .cache

EXPOSE 8000

CMD ["python", "main.py"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  youtube-summarizer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FIREWORKS_API_KEY=${FIREWORKS_API_KEY}
      - YOUTUBE_PROXY_USERNAME=${YOUTUBE_PROXY_USERNAME}
      - YOUTUBE_PROXY_PASSWORD=${YOUTUBE_PROXY_PASSWORD}
    volumes:
      - ./cache:/app/.cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### 3. Deploy

```bash
# Create .env file with your keys
cp .env.example .env

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

### Option 3: Cloud Platforms

#### Railway

1. Connect GitHub repository
2. Add environment variables in dashboard
3. Deploy automatically on push

#### Heroku

```bash
# Create Procfile
echo "web: python main.py" > Procfile

# Deploy
heroku create youtube-summarizer
heroku config:set FIREWORKS_API_KEY=your_key
git push heroku main
```

#### Render

1. Connect GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python main.py`
4. Add environment variables
5. Deploy

---

## Monitoring

### Logs

```bash
# Systemd service logs
sudo journalctl -u youtube-summarizer -f

# Docker logs
docker-compose logs -f
```

### Health Check Endpoint

Add to `main.py`:

```python
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
```

### Monitoring Tools

- **Uptime monitoring**: UptimeRobot, Pingdom
- **Error tracking**: Sentry
- **Performance**: New Relic, DataDog

---

## Backup

```bash
# Backup cache
tar -czf cache-backup-$(date +%Y%m%d).tar.gz .cache/

# Backup configuration
cp .env .env.backup
```

---

## Scaling

### Vertical Scaling
- Increase server RAM/CPU
- Adjust `max_concurrent_platform` in rate limiter

### Horizontal Scaling
- Deploy multiple instances
- Use load balancer (Nginx, HAProxy)
- Implement Redis for shared cache
- Use database for session management

---
