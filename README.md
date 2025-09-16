# SentiPlay - Google Play Store Reviews Sentiment Analysis

SentiPlay adalah aplikasi web untuk menganalisis sentimen review aplikasi dari Google Play Store. Aplikasi ini memungkinkan pengguna untuk melakukan scraping review, analisis sentimen, dan visualisasi data review dengan berbagai filter.

![SentiPlay Demo](https://via.placeholder.com/800x400/4CAF50/FFFFFF?text=SentiPlay+Demo)

## ✨ Fitur Utama

- 📱 **Scraping Review Google Play Store** - Ambil review aplikasi dengan berbagai filter
- 🔍 **Filter Rating** - Filter review berdasarkan rating (1-5 bintang) 
- 📊 **Visualisasi Data** - Wordcloud dan chart distribusi rating
- 📥 **Export CSV** - Download hasil review dalam format CSV
- 🧹 **Text Preprocessing** - Pembersihan teks dengan Sastrawi (Indonesian NLP)
- 📈 **Statistik Lengkap** - Total review, rating rata-rata, kata yang sering muncul
- 🔄 **Real-time Processing** - Proses scraping dan analisis secara background
- 💾 **Database Storage** - Penyimpanan data review dan hasil preprocessing
- 🗑️ **Auto Cleanup** - Pembersihan otomatis data lama (>7 hari) untuk menghemat storage
- ⚡ **No Caching** - Data selalu fresh tanpa cache untuk hasil analisis yang akurat

## 🛠️ Teknologi yang Digunakan

### Backend
- **Flask** - Web framework Python
- **SQLite** - Database penyimpanan
- **google-play-scraper** - Library untuk scraping Google Play Store
- **Sastrawi** - Indonesian text processing
- **matplotlib** - Visualisasi chart
- **wordcloud** - Pembuatan word cloud

### Frontend
- **HTML5/CSS3** - User interface
- **JavaScript** - Interactive functionality
- **Bootstrap** (optional) - Responsive design

## 🚀 Instalasi

### Metode 1: Instalasi Manual

#### Prerequisites
- Python 3.9+
- pip
- git

#### Langkah Instalasi

1. **Clone Repository**
   ```bash
   git clone https://github.com/danprat/sentiplay.git
   cd sentiplay
   ```

2. **Buat Virtual Environment**
   ```bash
   python3 -m venv gplay_scraper_env
   source gplay_scraper_env/bin/activate  # Linux/macOS
   # atau
   gplay_scraper_env\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Database**
   ```bash
   python migrate_database.py
   ```

5. **Jalankan Aplikasi**
   ```bash
   python app.py
   ```

6. **Akses Aplikasi**
   Buka browser dan akses: `http://localhost:5000`

### Metode 2: Menggunakan Docker 🐳

#### Prerequisites
- Docker
- Docker Compose

#### Quick Start dengan Docker

1. **Clone Repository**
   ```bash
   git clone https://github.com/danprat/sentiplay.git
   cd sentiplay
   ```

2. **Build dan Jalankan dengan Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Akses Aplikasi**
   Buka browser dan akses: `http://localhost:5000`

#### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Initialize database
RUN python migrate_database.py

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py", "--host=0.0.0.0"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  sentiplay:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_ENV=production
    restart: unless-stopped

  # Optional: Add nginx for production
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - sentiplay
    restart: unless-stopped
```

## 📖 Panduan Penggunaan

### 1. Scraping Review

1. Buka aplikasi di browser (`http://localhost:5000`)
2. Masukkan **App ID** aplikasi dari Google Play Store
   - Contoh: `com.duolingo` untuk aplikasi Duolingo
   - App ID bisa ditemukan di URL Google Play Store
3. Pilih pengaturan scraping:
   - **Language**: Bahasa review (default: `id` untuk Indonesia)
   - **Country**: Negara (default: `id` untuk Indonesia)
   - **Filter Score**: Rating tertentu (1-5) atau kosong untuk semua
   - **Count**: Jumlah review yang ingin diambil
4. Klik **"Start Scraping"**
5. Tunggu proses selesai (progress akan ditampilkan)

### 2. Melihat Hasil Analisis

Setelah scraping selesai, Anda akan melihat:

#### Dashboard Statistik
- **Total Reviews**: Jumlah total review yang berhasil diambil
- **Average Rating**: Rating rata-rata
- **Rating Distribution**: Distribusi rating 1-5 bintang

#### Visualisasi
- **Word Cloud**: Kata-kata yang sering muncul dalam review
- **Rating Chart**: Grafik batang distribusi rating  
- **Reviews Table**: Tabel review dengan pagination
- **CSV Export**: Download semua review data dalam format CSV untuk analisis lanjutan

### 3. Export Data ke CSV

Setelah scraping selesai, Anda dapat mengunduh data review dalam format CSV:

1. **Klik tombol "📥 Download CSV"** di bagian Analysis Results
2. File CSV akan berisi kolom:
   - `user_name`: Nama pengguna
   - `score`: Rating (1-5)  
   - `at`: Tanggal review
   - `content`: Isi review lengkap
   - `original_content`: Teks asli sebelum preprocessing
   - `cleaned_content`: Teks setelah pembersihan
   - `stemmed_content`: Teks setelah stemming
3. **Format nama file**: `reviews_[app_id]_[session_id]_[timestamp].csv`

### 4. Filter dan Analisis Lanjutan

#### Filter berdasarkan Rating
```json
{
  "app_id": "com.duolingo",
  "filter_score": 5,    // Hanya review 5 bintang
  "count": 100
}
```

#### Filter berdasarkan Negara/Bahasa
```json
{
  "app_id": "com.duolingo",
  "lang": "en",         // Review dalam bahasa Inggris
  "country": "us",      // Dari pengguna AS
  "count": 200
}
```

### 5. Sistem Auto Cleanup

Aplikasi secara otomatis menghapus data lama untuk menghemat space:

- **Pembersihan Otomatis**: Data session > 7 hari akan dihapus otomatis
- **Trigger**: Pembersihan terjadi setiap kali scraping baru dimulai
- **Data yang Dihapus**:
  - Raw reviews dari session lama
  - Processed reviews terkait
  - Scraping sessions metadata
- **Log**: Informasi pembersihan akan ditampilkan di console

```bash
# Manual cleanup (jika diperlukan)
python -c "
from database import DatabaseManager
db = DatabaseManager()
deleted = db.cleanup_old_sessions()
print(f'Deleted {deleted} old sessions')
"
```

## 🔧 Konfigurasi

### Environment Variables

Buat file `.env` di root directory:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_PATH=data/reviews.db

# Scraping Configuration
DEFAULT_LANG=id
DEFAULT_COUNTRY=id
DEFAULT_COUNT=100

# Processing Configuration
MAX_WORKERS=4
TIMEOUT_SECONDS=300
```

### Kustomisasi Preprocessing

Edit `preprocessing.py` untuk menyesuaikan preprocessing teks:

```python
def clean_text(self, text: str) -> str:
    """Kustomisasi pembersihan teks"""
    # Tambah logika kustomisasi di sini
    pass
```

## 📊 API Endpoints

### Scraping Endpoints

```bash
# Start scraping
POST /api/scrape
Content-Type: application/json
{
  "app_id": "com.duolingo",
  "lang": "id",
  "country": "id", 
  "filter_score": 5,
  "count": 100
}

# Check scraping status
GET /api/scrape/status/{session_id}
```

### Data Endpoints

```bash
# Get statistics
GET /api/statistics/{session_id}

# Get reviews data
GET /api/reviews/{session_id}?page=1&limit=20

# Download CSV file
GET /api/download/{session_id}/csv

# Get wordcloud image
GET /api/wordcloud/{session_id}

# Get rating chart
GET /api/rating-chart/{session_id}
```

### Response Examples

#### Statistics Response
```json
{
  "total_reviews": 100,
  "average_rating": 4.2,
  "rating_distribution": {
    "1": 5,
    "2": 10,
    "3": 15,
    "4": 30,
    "5": 40
  },
  "most_common_words": {
    "bagus": 25,
    "aplikasi": 20,
    "belajar": 18,
    "mudah": 15,
    "suka": 12
  }
}
```

## 🗄️ Database Schema

### Tabel `scraping_sessions`
```sql
CREATE TABLE scraping_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id TEXT NOT NULL,
    lang TEXT,
    country TEXT,
    filter_score INTEGER,
    count INTEGER,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    status TEXT
);
```

### Tabel `raw_reviews`
```sql
CREATE TABLE raw_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    app_id TEXT NOT NULL,
    review_id TEXT,
    user_name TEXT,
    content TEXT,
    score INTEGER,
    at DATETIME,
    FOREIGN KEY (session_id) REFERENCES scraping_sessions (id)
);
```

### Tabel `processed_reviews`
```sql
CREATE TABLE processed_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT UNIQUE,
    original_content TEXT,
    cleaned_content TEXT,
    stopwords_removed TEXT,
    stemmed_content TEXT,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Testing

### Unit Tests
```bash
# Install testing dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v --cov=.

# Run specific test
pytest tests/test_scraper.py -v
```

### Integration Tests
```bash
# Test API endpoints
pytest tests/test_api.py -v

# Test database operations
pytest tests/test_database.py -v
```

### Manual Testing
```bash
# Test scraping
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"app_id": "com.duolingo", "count": 10}'

# Test statistics
curl http://localhost:5000/api/statistics/1
```

## 🚀 Deployment

### Production dengan Docker

1. **Build Production Image**
   ```bash
   docker build -t sentiplay:latest .
   ```

2. **Run dengan Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Deployment ke Cloud

#### Heroku
```bash
# Login ke Heroku
heroku login

# Create app
heroku create sentiplay-app

# Deploy
git push heroku main
```

#### AWS EC2
```bash
# Setup EC2 instance
# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start

# Deploy aplikasi
git clone https://github.com/danprat/sentiplay.git
cd sentiplay
sudo docker-compose up -d
```

## 🔍 Troubleshooting

### Common Issues

#### 1. SSL Error saat Scraping
```bash
Error: SSL: CERTIFICATE_VERIFY_FAILED
```
**Solusi**: Update sertifikat atau gunakan proxy

#### 2. Memory Error pada Dataset Besar
```bash
MemoryError: Unable to allocate array
```
**Solusi**: Kurangi batch size atau tambah RAM

#### 3. Database Locked
```bash
sqlite3.OperationalError: database is locked
```
**Solusi**: Restart aplikasi atau check file lock

#### 4. CSV Download Gagal
```bash
Error 500: Failed to generate CSV
```
**Solusi**: 
- Pastikan session_id valid dan scraping sudah completed
- Check permission write di direktori aplikasi
- Restart aplikasi jika persistent

#### 5. Analysis Results Tidak Update
```bash
Total Reviews: 1000, Average Rating: 1.0 (stuck)
```
**Solusi**:
- Pastikan tidak menggunakan data cached
- Lakukan scraping baru dengan parameter berbeda  
- Check session status di database: `SELECT status FROM scraping_sessions WHERE id = [session_id]`

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
export PYTHONPATH=/path/to/sentiplay

# Run dengan debug
python app.py --debug
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Development Setup
```bash
# Clone repo
git clone https://github.com/danprat/sentiplay.git
cd sentiplay

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 📝 Changelog

### v1.3.0 (Current)
- ✅ **NEW**: Added CSV export functionality for reviews data
- ✅ **NEW**: Implemented automatic cleanup system for old data (>7 days)
- ✅ **IMPROVED**: Disabled caching to prevent stale Analysis Results
- ✅ **FIX**: Fixed session status updates for proper completion tracking
- ✅ **IMPROVED**: Enhanced data management to prevent database bloat
- ✅ **UX**: Added download progress indicator and better error handling

### v1.2.0
- ✅ Fixed rating filter functionality
- ✅ Improved session-based data isolation
- ✅ Added matplotlib Agg backend for web compatibility
- ✅ Enhanced database schema with foreign key relationships
- ✅ Added comprehensive error handling

### v1.1.0
- ✅ Added wordcloud generation
- ✅ Implemented rating distribution charts
- ✅ Added Indonesian text preprocessing with Sastrawi
- ✅ Created RESTful API endpoints

### v1.0.0
- ✅ Basic Google Play Store scraping
- ✅ SQLite database integration
- ✅ Web interface with Flask
- ✅ Basic statistics and review display

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Dany Pratmanto** - *Initial work* - [@danprat](https://github.com/danprat)

## 🙏 Acknowledgments

- **google-play-scraper** - For providing the scraping functionality
- **Sastrawi** - For Indonesian text processing
- **Flask** - For the web framework
- **matplotlib** & **wordcloud** - For data visualization

## 📞 Support

Untuk pertanyaan atau bantuan:
- 📧 Email: dany.pratmanto@example.com
- 💬 GitHub Issues: [Create an issue](https://github.com/danprat/sentiplay/issues)
- 📖 Documentation: [Wiki](https://github.com/danprat/sentiplay/wiki)

---

⭐ **Jika project ini membantu, berikan star di GitHub!** ⭐
