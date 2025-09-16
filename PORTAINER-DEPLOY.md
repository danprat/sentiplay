# 🐳 SentiPlay - Docker Portainer Stack

Panduan lengkap untuk deploy SentiPlay menggunakan Docker Portainer Stack.

## 📋 Prerequisites

- ✅ Docker Engine terinstall
- ✅ Portainer terinstall dan running
- ✅ Akses ke Portainer Web UI
- ✅ Port 5000 tersedia

## 🚀 Quick Deploy

### Method 1: Simple Stack (Recommended)

1. **Login ke Portainer**
   - Buka Portainer Web UI (biasanya `http://localhost:9000`)
   - Login dengan credentials Anda

2. **Create New Stack**
   - Pilih **Stacks** dari sidebar
   - Klik **Add Stack**
   - Masukkan nama: `sentiplay`

3. **Copy Stack Configuration**
   
   Salin konfigurasi berikut ke Web Editor:

   ```yaml
   version: '3.8'

   services:
     sentiplay:
       image: python:3.9-slim
       container_name: sentiplay
       restart: unless-stopped
       ports:
         - "5000:5000"
       volumes:
         - sentiplay_data:/app/data
       environment:
         - FLASK_ENV=production
         - PYTHONUNBUFFERED=1
         - TZ=Asia/Jakarta
       working_dir: /app
       command: |
         bash -c "
           echo '🚀 Starting SentiPlay installation...'
           apt-get update && apt-get install -y git gcc g++ curl
           git clone https://github.com/danprat/sentiplay.git /app
           cd /app
           pip install --no-cache-dir -r requirements.txt
           python migrate_database.py
           echo '✅ Installation complete! Starting application...'
           python app.py --host=0.0.0.0 --port=5000
         "
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:5000/health || exit 1"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 60s

   volumes:
     sentiplay_data:
       driver: local

   networks:
     default:
       name: sentiplay_network
   ```

4. **Deploy Stack**
   - Klik **Deploy the stack**
   - Tunggu proses deployment selesai (2-3 menit)

5. **Akses Aplikasi**
   - Buka browser: `http://localhost:5000`
   - Atau `http://[SERVER_IP]:5000`

### Method 2: Full Stack dengan Nginx

Untuk production dengan load balancer:

```yaml
version: '3.8'

services:
  sentiplay:
    image: python:3.9-slim
    container_name: sentiplay-app
    restart: unless-stopped
    expose:
      - "5000"
    volumes:
      - sentiplay_data:/app/data
      - sentiplay_code:/app
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
      - TZ=Asia/Jakarta
    working_dir: /app
    command: |
      bash -c "
        echo '🚀 Installing SentiPlay...'
        apt-get update && apt-get install -y git gcc g++ curl
        git clone https://github.com/danprat/sentiplay.git /app
        cd /app
        pip install --no-cache-dir -r requirements.txt
        python migrate_database.py
        echo '✅ Starting application...'
        python app.py --host=0.0.0.0 --port=5000
      "
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    container_name: sentiplay-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - sentiplay
    environment:
      - TZ=Asia/Jakarta

volumes:
  sentiplay_data:
    driver: local
  sentiplay_code:
    driver: local

networks:
  default:
    name: sentiplay_network
```

## 📊 Monitoring & Management

### 1. **Container Status**
Di Portainer:
- **Containers** → Cari `sentiplay`
- Status harus **Running** dan **Healthy**

### 2. **Logs Monitoring**
```bash
# Via Portainer UI
Containers → sentiplay → Logs

# Via Docker CLI
docker logs -f sentiplay
```

### 3. **Resource Usage**
```bash
# Via Portainer UI
Containers → sentiplay → Stats

# Via Docker CLI
docker stats sentiplay
```

## 🔧 Configuration

### Environment Variables

Tambahkan di bagian **environment** jika diperlukan:

```yaml
environment:
  - FLASK_ENV=production
  - FLASK_DEBUG=false
  - DATABASE_PATH=/app/data/reviews.db
  - DEFAULT_LANG=id
  - DEFAULT_COUNTRY=id
  - MAX_WORKERS=4
  - CLEANUP_DAYS=7
  - TZ=Asia/Jakarta
```

### Volume Mapping

```yaml
volumes:
  # Data persistence
  - sentiplay_data:/app/data
  
  # Optional: Custom config
  - ./config:/app/config:ro
  
  # Optional: Logs
  - ./logs:/app/logs
```

### Port Configuration

```yaml
ports:
  # Default
  - "5000:5000"
  
  # Custom port
  - "8080:5000"
  
  # Multiple instances
  - "5001:5000"  # Instance 1
  - "5002:5000"  # Instance 2
```

## 🛠️ Troubleshooting

### Container Won't Start

1. **Check Logs**
   ```bash
   docker logs sentiplay
   ```

2. **Common Issues:**
   - Port 5000 already in use
   - Insufficient disk space
   - Network connectivity issues

3. **Solutions:**
   ```yaml
   # Change port
   ports:
     - "8080:5000"
   
   # Add resource limits
   deploy:
     resources:
       limits:
         memory: 1G
         cpus: '0.5'
   ```

### Application Errors

1. **Database Issues**
   ```bash
   # Reset database
   docker exec sentiplay rm -f /app/data/reviews.db
   docker exec sentiplay python /app/migrate_database.py
   ```

2. **Memory Issues**
   ```yaml
   # Add memory limit
   deploy:
     resources:
       limits:
         memory: 2G
   ```

3. **Network Issues**
   ```bash
   # Recreate network
   docker network rm sentiplay_network
   docker-compose up -d
   ```

### Performance Optimization

1. **Resource Limits**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
         cpus: '1.0'
       reservations:
         memory: 512M
         cpus: '0.5'
   ```

2. **Health Check Tuning**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
     interval: 60s  # Increase interval
     timeout: 15s   # Increase timeout
     retries: 5
     start_period: 120s  # More start time
   ```

## 🔄 Updates & Maintenance

### Update Application

1. **Via Portainer UI:**
   - Stacks → sentiplay → **Editor**
   - Modify image tag or environment
   - **Update the stack**

2. **Force Rebuild:**
   ```bash
   # Stop stack
   docker-compose down
   
   # Remove old images
   docker image prune -f
   
   # Start stack
   docker-compose up -d
   ```

### Backup Data

```bash
# Backup database
docker cp sentiplay:/app/data/reviews.db ./backup/

# Backup entire data volume
docker run --rm -v sentiplay_data:/data -v $(pwd):/backup alpine tar czf /backup/sentiplay_backup.tar.gz /data
```

### Restore Data

```bash
# Restore database
docker cp ./backup/reviews.db sentiplay:/app/data/

# Restore volume
docker run --rm -v sentiplay_data:/data -v $(pwd):/backup alpine tar xzf /backup/sentiplay_backup.tar.gz -C /
```

## 📈 Scaling

### Multiple Instances

```yaml
version: '3.8'

services:
  sentiplay-1:
    # ... same config
    ports:
      - "5001:5000"
  
  sentiplay-2:
    # ... same config  
    ports:
      - "5002:5000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    # Load balance between instances
```

### Load Balancer Configuration

```nginx
upstream sentiplay_cluster {
    server sentiplay-1:5000;
    server sentiplay-2:5000;
}

server {
    listen 80;
    location / {
        proxy_pass http://sentiplay_cluster;
    }
}
```

## 🔗 Useful Links

- **Repository**: https://github.com/danprat/sentiplay
- **Portainer Docs**: https://docs.portainer.io/
- **Docker Compose**: https://docs.docker.com/compose/
- **Issues**: https://github.com/danprat/sentiplay/issues

## 📞 Support

Jika ada masalah:
1. Check container logs di Portainer
2. Buat issue di GitHub repository
3. Join discussion di repository

---

**Happy Deploying! 🚀**
