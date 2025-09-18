"""FastAPI application entry point for Sentily service."""

from __future__ import annotations

import csv
import sys
import threading
from io import StringIO
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

from scraper import PlayStoreScraper
from preprocessing import TextPreprocessor
from visualization import DataVisualizer
from database import DatabaseManager


class ScrapeRequest(BaseModel):
    """Request body for initiating a scraping session."""

    app_id: str
    lang: str = "en"
    country: str = "us"
    filter_score: Optional[int] = None
    count: int = 100
    sort: str = "NEWEST"
    force_new: bool = False


# Load environment variables before instantiating application components
load_dotenv()

# Instantiate FastAPI application
app = FastAPI(title="Sentily", description="Google Play review scraping service", version="1.0.0")

# Configure CORS policy similar to the previous Flask implementation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Template configuration for the existing UI assets
templates = Jinja2Templates(directory="templates")

# Initialize core service components
db_manager = DatabaseManager()
scraper = PlayStoreScraper()
preprocessor = TextPreprocessor()
visualizer = DataVisualizer()


def scrape_reviews_background(
    session_id: int,
    app_id: str,
    lang: str,
    country: str,
    filter_score: Optional[int],
    count: int,
    sort: str = "NEWEST",
) -> None:
    """Background worker used to fetch, persist, and preprocess reviews."""

    try:
        db_manager.update_session_status(session_id, "scraping")

        # Store application metadata if available
        try:
            app_details = scraper.get_app_details(app_id=app_id, lang=lang, country=country)
            if app_details:
                db_manager.update_session_app_info(session_id, app_details)
        except Exception as metadata_error:  # pylint: disable=broad-except
            print(f"Failed to store app metadata for session {session_id}: {metadata_error}")

        # Map sort string to enum accepted by google_play_scraper
        from google_play_scraper import Sort

        sort_enum = Sort.NEWEST if sort == "NEWEST" else Sort.MOST_RELEVANT

        reviews, _ = scraper.scrape_reviews(
            app_id=app_id,
            lang=lang,
            country=country,
            sort=sort_enum,
            filter_score_with=filter_score,
            count=count,
        )

        saved_count = db_manager.save_reviews(reviews, session_id, app_id, lang, country)
        print(f"Saved {saved_count} reviews for session {session_id}")

        if saved_count == 0:
            print(f"No reviews saved for session {session_id}")
            db_manager.update_session_status(session_id, "failed")
            return

        db_manager.update_session_status(session_id, "processing")

        processed_count = preprocessor.preprocess_all_reviews(session_id)
        print(f"Processed {processed_count} out of {saved_count} reviews for session {session_id}")

        if saved_count > 0:
            db_manager.update_session_status(session_id, "completed")
            print(
                "Scraping completed for session %s. Saved %s reviews, processed %s reviews."
                % (session_id, saved_count, processed_count)
            )
        else:
            db_manager.update_session_status(session_id, "failed")

    except Exception as exc:  # pylint: disable=broad-except
        print(f"Error in scraping background task for session {session_id}: {exc}")
        import traceback

        traceback.print_exc()
        db_manager.update_session_status(session_id, "failed")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Serve the main dashboard page."""

    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/cors-test.html")
async def cors_test() -> FileResponse:
    """Expose standalone CORS test page."""

    return FileResponse("cors-test.html", media_type="text/html")


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe endpoint for container orchestration."""

    return {"status": "healthy", "service": "sentiplay"}


@app.post("/api/scrape")
def scrape_reviews_endpoint(payload: ScrapeRequest) -> dict[str, object]:
    """Start review scraping workflow and spawn background worker."""

    if not payload.app_id:
        raise HTTPException(status_code=400, detail="App ID is required")

    print(f"Starting fresh scraping for app_id: {payload.app_id}, filter_score: {payload.filter_score}")

    cleanup_count = db_manager.cleanup_old_data(keep_days=3, keep_sessions=5)
    if cleanup_count > 0:
        print(f"Cleaned up {cleanup_count} old sessions")

    session_id = db_manager.create_scraping_session(
        app_id=payload.app_id,
        lang=payload.lang,
        country=payload.country,
        filter_score=payload.filter_score,
        count=payload.count,
    )

    thread = threading.Thread(
        target=scrape_reviews_background,
        args=(
            session_id,
            payload.app_id,
            payload.lang,
            payload.country,
            payload.filter_score,
            payload.count,
            payload.sort,
        ),
        daemon=True,
    )
    thread.start()

    return {
        "session_id": session_id,
        "status": "started",
        "message": "Scraping started successfully",
        "cached": False,
    }


@app.get("/api/scrape/status/{session_id}")
def scrape_status(session_id: int) -> dict[str, object]:
    """Report progress of a scraping session."""

    session_data = db_manager.get_session_status(session_id)

    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    review_count = db_manager.get_reviews_count(session_id)
    processed_count = db_manager.get_processed_reviews_count(session_id)

    return {
        "session_id": session_id,
        "status": session_data["status"],
        "review_count": review_count,
        "processed_count": processed_count,
        "app_id": session_data["app_id"],
        "lang": session_data["lang"],
        "country": session_data["country"],
    }


@app.get("/api/wordcloud/{session_id}")
def wordcloud_image(session_id: int) -> Response:
    """Return generated word cloud image for a session."""

    wordcloud_bytes = visualizer.generate_wordcloud(session_id)
    if not wordcloud_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate wordcloud")

    return Response(content=wordcloud_bytes, media_type="image/png")


@app.get("/api/rating-chart/{session_id}")
def rating_chart(session_id: int) -> Response:
    """Return rating distribution image for a session."""

    chart_bytes = visualizer.generate_rating_chart(session_id)
    if not chart_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate rating chart")

    return Response(content=chart_bytes, media_type="image/png")


@app.get("/api/statistics/{session_id}")
def statistics(session_id: int) -> dict[str, object]:
    """Return aggregated statistics for a session."""

    stats = visualizer.get_statistics(session_id)
    if not stats:
        raise HTTPException(status_code=500, detail="Failed to get statistics")

    return stats


@app.get("/api/reviews/{session_id}")
def reviews_data(
    session_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
) -> dict[str, object]:
    """Return paginated review data for the specified session."""

    reviews = visualizer.get_reviews_data(session_id, page, limit)
    if reviews is None:
        raise HTTPException(status_code=500, detail="Failed to get reviews data")

    return reviews


@app.get("/api/download/reviews/{session_id}")
def download_reviews_csv(session_id: int) -> Response:
    """Generate and download all reviews for a session as CSV."""

    reviews_data = visualizer.get_all_reviews_for_download(session_id)
    if not reviews_data:
        raise HTTPException(status_code=404, detail="No reviews found for this session")

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "Session ID",
            "App ID",
            "Review ID",
            "User Name",
            "Rating",
            "Date",
            "Content",
            "Original Content",
            "Cleaned Content",
            "Processed Content",
            "Thumbs Up",
        ]
    )

    for review in reviews_data:
        writer.writerow(
            [
                review.get("session_id", ""),
                review.get("app_id", ""),
                review.get("review_id", ""),
                review.get("user_name", ""),
                review.get("score", ""),
                review.get("at", ""),
                review.get("content", ""),
                review.get("original_content", ""),
                review.get("cleaned_content", ""),
                review.get("stemmed_content", ""),
                review.get("thumbs_up_count", ""),
            ]
        )

    output.seek(0)
    session_info = db_manager.get_session_status(session_id) or {}
    app_id = session_info.get("app_id", "unknown")
    filename = f"reviews_{app_id}_{session_id}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


def _parse_cli_arguments() -> tuple[str, int, bool]:
    """Parse CLI arguments to maintain backwards compatibility with Flask runner."""

    host = "127.0.0.1"
    port = 5000
    debug = False

    for arg in sys.argv[1:]:
        if arg.startswith("--host="):
            host = arg.split("=", maxsplit=1)[1]
        elif arg.startswith("--port="):
            try:
                port = int(arg.split("=", maxsplit=1)[1])
            except ValueError:
                print(f"Invalid port provided: {arg}")
        elif arg == "--host":
            host = "0.0.0.0"

    from os import environ

    if environ.get("FASTAPI_ENV") == "production" or environ.get("FLASK_ENV") == "production":
        debug = False
        host = "0.0.0.0"

    return host, port, debug


# Mount static files - this should be done after all routes are defined
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn

    host, port, debug = _parse_cli_arguments()
    print(f"Starting Sentiplay FastAPI server on {host}:{port} (reload={debug})")
    uvicorn.run("app:app", host=host, port=port, reload=debug)
