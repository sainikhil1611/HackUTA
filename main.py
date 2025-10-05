from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import shutil
from io import BytesIO
from pathlib import Path

# Import the agentic system
from sports_agent import SportsVideoAnalysisAgent

app = FastAPI(title="Sports Video Analysis API - Agentic Edition")

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

# Initialize agent system
agent_system = SportsVideoAnalysisAgent()

@app.get("/")
async def root():
    return {
        "message": "Sports Video Analysis API - Agentic Edition",
        "version": "2.0.0",
        "architecture": "LangChain + Agentuity",
        "agents": [
            "Video Analysis Specialist (Gemini AI)",
            "Video Visualization Engineer (OpenCV + MediaPipe)",
            "Sports Performance Coach (RAG + Knowledge Bases)"
        ]
    }

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
    Analyze a sports video using multi-agent system

    Parameters:
    - sport: The sport type (basketball, soccer, or tennis)
    - video: The video file to analyze

    Returns:
    - Annotated video file with analysis data and coaching summary in headers

    Architecture:
    1. Video Analysis Agent (Gemini) - Analyzes video and extracts performance data
    2. Visualization Agent (OpenCV/MediaPipe) - Annotates video with stats and feedback
    3. Coaching Agent (RAG) - Generates personalized coaching recommendations
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
        # Save uploaded video
        video_filename = f"{sport}_{video.filename}"
        video_path = UPLOAD_DIR / video_filename

        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        print(f"[FastAPI] Video saved to: {video_path}")

        # Run agentic analysis workflow
        print(f"[FastAPI] Starting agentic analysis for {sport}...")
        result = agent_system.analyze_video(
            str(video_path),
            sport.lower(),
            UPLOAD_DIR
        )

        annotated_video_path = Path(result["annotated_video_path"])

        # Check if annotated video was created
        if not annotated_video_path.exists():
            raise FileNotFoundError(f"Annotated video was not created at {annotated_video_path}")

        print("[FastAPI] Agent workflow complete!")

        # Read the video file into memory before cleanup
        with open(annotated_video_path, "rb") as f:
            video_bytes = f.read()

        # Prepare response headers with analysis data
        import json
        analysis_json = json.dumps(result["analysis_data"])
        coaching_summary = result["coaching_summary"]

        # Return the annotated video as a streaming response
        return StreamingResponse(
            BytesIO(video_bytes),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename={sport}_annotated.mp4",
                "X-Analysis-Data": analysis_json.replace('"', '\\"'),
                "X-Coaching-Summary": coaching_summary.replace('"', '\\"'),
                "X-Agentic-System": "LangChain + Agentuity"
            }
        )

    except Exception as e:
        print(f"[FastAPI] Error during analysis: {e}")
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

@app.get("/agents/info")
async def get_agents_info():
    """Get information about the agent system"""
    return {
        "agent_framework": "Agentuity + LangChain",
        "agents": [
            {
                "name": "Video Analysis Specialist",
                "role": "Analyze sports videos using Gemini AI",
                "tools": ["gemini_video_analyzer"],
                "capabilities": [
                    "Shot-by-shot analysis",
                    "Event detection",
                    "Technical feedback generation"
                ]
            },
            {
                "name": "Video Visualization Engineer",
                "role": "Annotate videos with OpenCV and MediaPipe",
                "tools": ["opencv_mediapipe_annotator", "elevenlabs_voice_generator"],
                "capabilities": [
                    "Pose tracking",
                    "Statistics overlays",
                    "Feedback visualization",
                    "Voice integration"
                ]
            },
            {
                "name": "Sports Performance Coach",
                "role": "Generate coaching recommendations using RAG",
                "tools": ["rag_coaching_summary"],
                "capabilities": [
                    "Strengths identification",
                    "Weakness analysis",
                    "Drill recommendations",
                    "Knowledge base integration"
                ]
            }
        ],
        "workflow": "Sequential task execution with context sharing between agents"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
