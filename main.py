from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
from pathlib import Path
from analysis import analyze_video
from ball import annotate_video

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
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

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
    - analysis: JSON analysis data
    - annotated_video_path: Path to the annotated video
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

    try:
        video_filename = f"{sport}_{video.filename}"
        video_path = UPLOAD_DIR / video_filename

        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        print(f"Video saved to: {video_path}")

        analysis_output_path = OUTPUT_DIR / "sports.json"

        print(f"Starting analysis for {sport}...")
        analysis_data = analyze_video(
            str(video_path),
            sport.lower(),
            str(analysis_output_path)
        )

        print(f"Analysis complete. Results saved to: {analysis_output_path}")

        annotated_video_path = OUTPUT_DIR / f"{sport}_annotated.mp4"

        print("Generating annotated video...")
        annotate_video(
            str(video_path),
            analysis_data,
            str(annotated_video_path),
            sport.lower()
        )

        return {
            "status": "success",
            "sport": sport,
            "analysis": analysis_data,
            "analysis_file": str(analysis_output_path),
            "annotated_video": str(annotated_video_path) if annotated_video_path.exists() else None
        }

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if video_path.exists():
            video_path.unlink()

@app.get("/download/analysis")
async def download_analysis():
    """Download the analysis JSON file"""
    analysis_path = OUTPUT_DIR / "sports.json"

    if not analysis_path.exists():
        raise HTTPException(status_code=404, detail="Analysis file not found")

    return FileResponse(
        path=analysis_path,
        media_type="application/json",
        filename="sports.json"
    )

@app.get("/download/video/{sport}")
async def download_annotated_video(sport: str):
    """Download the annotated video file"""
    video_path = OUTPUT_DIR / f"{sport}_annotated.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Annotated video not found")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"{sport}_annotated.mp4"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
