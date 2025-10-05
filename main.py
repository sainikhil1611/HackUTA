from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import shutil
import os
from pathlib import Path
from analysis import analyze_video as analyze_video_with_ai
from ball import annotate_video
from coaching_rag import generate_coaching_summary

app = FastAPI(title="Sports Video Analysis API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

SUPPORTED_SPORTS = ["basketball", "soccer", "tennis"]

@app.get("/")
async def root():
    return {"message": "Sports Video Analysis API", "version": "1.0.0"}

@app.get("/sports")
async def get_supported_sports():
    """Get list of supported sports"""
    return {"sports": SUPPORTED_SPORTS}

@app.post("/analyze")
async def analyze_video(
    sport: str = Form(...),
    video: UploadFile = File(...)
):
    """
    Analyze a sports video

    Parameters:
    - sport: The sport type (basketball, soccer, or tennis)
    - video: The video file to analyze

    Returns:
    - Annotated video file directly
    - Headers include analysis JSON and coaching summary
    """

    if sport.lower() not in SUPPORTED_SPORTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported sport: {sport}. Supported sports: {SUPPORTED_SPORTS}"
        )

    # Validate video file
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be a video"
        )

    video_path = None
    annotated_video_path = None

    try:
        video_filename = f"{sport}_{video.filename}"
        video_path = UPLOAD_DIR / video_filename

        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        print(f"Video saved to: {video_path}")

        # Store JSON in root directory
        analysis_output_path = Path("sports.json")

        print(f"Starting analysis for {sport}...")
        analysis_data = analyze_video_with_ai(
            str(video_path),
            sport.lower(),
            str(analysis_output_path)
        )

        print(f"Analysis complete. Results saved to: {analysis_output_path}")

        # Create temporary annotated video
        annotated_video_path = UPLOAD_DIR / f"{sport}_annotated_temp.mp4"

        print("Generating annotated video...")
        annotate_video(
            str(video_path),
            analysis_data,
            str(annotated_video_path),
            sport.lower()
        )

        # Check if annotated video was created
        if not annotated_video_path.exists():
            raise FileNotFoundError(f"Annotated video was not created at {annotated_video_path}")

        print("Generating coaching summary using RAG...")
        coaching_summary = generate_coaching_summary(sport.lower(), analysis_data)
        print(f"Coaching summary generated successfully")

        # Read the video file into memory before cleanup
        with open(annotated_video_path, "rb") as f:
            video_bytes = f.read()

        # Return the annotated video as a streaming response
        from io import BytesIO

        return StreamingResponse(
            BytesIO(video_bytes),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename={sport}_annotated.mp4",
                "X-Analysis-Data": str(analysis_data).replace('"', '\\"'),
                "X-Coaching-Summary": coaching_summary.replace('"', '\\"')
            }
        )

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temporary files
        if video_path and video_path.exists():
            video_path.unlink()
        if annotated_video_path and annotated_video_path.exists():
            annotated_video_path.unlink()

@app.get("/download/analysis")
async def download_analysis():
    """Download the analysis JSON file"""
    analysis_path = Path("sports.json")

    if not analysis_path.exists():
        raise HTTPException(status_code=404, detail="Analysis file not found")

    return FileResponse(
        path=analysis_path,
        media_type="application/json",
        filename="sports.json"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
