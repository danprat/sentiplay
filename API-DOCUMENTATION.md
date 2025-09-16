# SentiPlay API Documentation

## Base URL
```
https://sentiplay.ruangdany.com
```

## Endpoints

### 1. Home Page
**GET** `/`
```bash
curl -X GET "https://sentiplay.ruangdany.com/"
```
- **Description**: Halaman utama aplikasi SentiPlay
- **Response**: HTML page

---

### 2. Health Check
**GET** `/health`
```bash
curl -X GET "https://sentiplay.ruangdany.com/health"
```
- **Description**: Endpoint untuk monitoring kesehatan aplikasi
- **Response**: 
```json
{
  "status": "healthy",
  "timestamp": "2025-09-16T12:00:00Z"
}
```

---

### 3. Start Scraping
**POST** `/api/scrape`
```bash
curl -X POST "https://sentiplay.ruangdany.com/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "com.duolingo",
    "lang": "id",
    "country": "id",
    "filter_score": null,
    "count": 100
  }'
```

**Request Body Parameters:**
- `app_id` (string, required): Google Play Store app ID (e.g., "com.duolingo")
- `lang` (string, optional): Language code (default: "id")
- `country` (string, optional): Country code (default: "id") 
- `filter_score` (integer, optional): Filter reviews by rating (1-5, null for all)
- `count` (integer, optional): Number of reviews to scrape (default: 100)

**Response:**
```json
{
  "success": true,
  "session_id": 123,
  "message": "Scraping started successfully"
}
```

---

### 4. Check Scraping Status
**GET** `/api/scrape/status/{session_id}`
```bash
curl -X GET "https://sentiplay.ruangdany.com/api/scrape/status/123"
```

**Response:**
```json
{
  "session_id": 123,
  "status": "completed",
  "review_count": 95,
  "processed_count": 95,
  "app_info": {
    "title": "Duolingo",
    "description": "Learn languages for free...",
    "genre": "Education",
    "version": "5.123.4"
  }
}
```

**Status Values:**
- `running`: Scraping masih berjalan
- `completed`: Scraping selesai
- `error`: Terjadi error
- `not_found`: Session tidak ditemukan

---

### 5. Get Reviews Data
**GET** `/api/reviews/{session_id}`
```bash
# Get first page (10 reviews per page)
curl -X GET "https://sentiplay.ruangdany.com/api/reviews/123?page=1&limit=10"

# Get specific page with custom limit
curl -X GET "https://sentiplay.ruangdany.com/api/reviews/123?page=2&limit=25"
```

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Items per page (default: 10, max: 100)

**Response:**
```json
{
  "reviews": [
    {
      "id": 1,
      "user_name": "John Doe",
      "content": "Aplikasi yang sangat bagus untuk belajar bahasa",
      "score": 5,
      "thumbs_up_count": 12,
      "at": "2025-09-15T10:30:00Z",
      "sentiment": "positive",
      "processed_content": "aplikasi sangat bagus belajar bahasa"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 10,
    "total_reviews": 95,
    "per_page": 10
  }
}
```

---

### 6. Get Statistics
**GET** `/api/statistics/{session_id}`
```bash
curl -X GET "https://sentiplay.ruangdany.com/api/statistics/123"
```

**Response:**
```json
{
  "app_info": {
    "app_id": "com.duolingo",
    "title": "Duolingo",
    "description": "Learn languages for free...",
    "genre": "Education",
    "version": "5.123.4",
    "country": "id",
    "lang": "id"
  },
  "total_reviews": 95,
  "sentiment_distribution": {
    "positive": 65,
    "negative": 20,
    "neutral": 10
  },
  "rating_distribution": {
    "1": 5,
    "2": 8,
    "3": 12,
    "4": 25,
    "5": 45
  },
  "average_rating": 4.2,
  "review_period": {
    "start_date": "2025-08-01",
    "end_date": "2025-09-15",
    "days_span": 45
  },
  "top_words": [
    {"word": "bagus", "count": 23},
    {"word": "mudah", "count": 18},
    {"word": "belajar", "count": 15}
  ]
}
```

---

### 7. Get Rating Chart
**GET** `/api/rating-chart/{session_id}`
```bash
curl -X GET "https://sentiplay.ruangdany.com/api/rating-chart/123" \
  --output rating_chart.png
```

**Response**: PNG image of rating distribution chart
- **Content-Type**: `image/png`
- **Description**: Bar chart showing rating distribution (1-5 stars)

---

### 8. Get Word Cloud
**GET** `/api/wordcloud/{session_id}`
```bash
curl -X GET "https://sentiplay.ruangdany.com/api/wordcloud/123" \
  --output wordcloud.png
```

**Response**: PNG image of word cloud
- **Content-Type**: `image/png`
- **Description**: Word cloud visualization of most frequent words in reviews

---

### 9. Download CSV
**GET** `/api/download/{session_id}`
```bash
curl -X GET "https://sentiplay.ruangdany.com/api/download/123" \
  --output reviews_data.csv
```

**Response**: CSV file containing all review data
- **Content-Type**: `text/csv`
- **Filename**: `{app_title}_reviews_{timestamp}.csv`
- **Columns**: 
  - `review_id`, `user_name`, `content`, `score`, `thumbs_up_count`
  - `review_date`, `sentiment`, `cleaned_content`, `processed_content`
  - `app_id`, `app_title`, `app_genre`

---

## Example Workflow

### Complete Scraping and Analysis Workflow:

```bash
# 1. Start scraping for Duolingo app
RESPONSE=$(curl -s -X POST "https://sentiplay.ruangdany.com/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "com.duolingo",
    "lang": "id",
    "country": "id",
    "count": 50
  }')

# Extract session ID from response
SESSION_ID=$(echo $RESPONSE | grep -o '"session_id":[0-9]*' | grep -o '[0-9]*')
echo "Session ID: $SESSION_ID"

# 2. Monitor scraping status
while true; do
  STATUS=$(curl -s "https://sentiplay.ruangdany.com/api/scrape/status/$SESSION_ID" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  
  sleep 5
done

# 3. Get statistics when completed
curl -s "https://sentiplay.ruangdany.com/api/statistics/$SESSION_ID" | jq '.'

# 4. Download visualizations
curl "https://sentiplay.ruangdany.com/api/rating-chart/$SESSION_ID" --output "rating_chart_$SESSION_ID.png"
curl "https://sentiplay.ruangdany.com/api/wordcloud/$SESSION_ID" --output "wordcloud_$SESSION_ID.png"

# 5. Download CSV data
curl "https://sentiplay.ruangdany.com/api/download/$SESSION_ID" --output "reviews_data_$SESSION_ID.csv"

# 6. Get paginated reviews data
curl -s "https://sentiplay.ruangdany.com/api/reviews/$SESSION_ID?page=1&limit=20" | jq '.reviews[]'
```

---

## Error Responses

### Common Error Formats:

**400 Bad Request:**
```json
{
  "error": "Invalid app_id format",
  "message": "App ID must be in format com.example.app"
}
```

**404 Not Found:**
```json
{
  "error": "Session not found",
  "session_id": 123
}
```

**500 Internal Server Error:**
```json
{
  "error": "Scraping failed",
  "message": "Unable to fetch app data from Google Play Store"
}
```

---

## Rate Limiting

- **Scraping**: Max 1 concurrent scraping session per IP
- **API Calls**: Max 100 requests per minute per IP
- **File Downloads**: Max 10 downloads per minute per IP

---

## Authentication

Currently, the API is **publicly accessible** without authentication.

---

## Response Headers

All API responses include:
```
Content-Type: application/json (for JSON endpoints)
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1695729600
Access-Control-Allow-Origin: *
```

---

## Notes

1. **App IDs**: Must be valid Google Play Store package names (e.g., `com.duolingo`, `com.spotify.music`)
2. **Language/Country Codes**: Use ISO 639-1 for language and ISO 3166-1 alpha-2 for country
3. **Session Persistence**: Sessions are automatically cleaned up after 7 days
4. **File Formats**: Charts and word clouds are returned as PNG images, data exports as CSV
5. **Caching**: Results are not cached - each scraping session creates fresh data

---

**Last Updated**: September 16, 2025  
**Version**: 1.0.0
