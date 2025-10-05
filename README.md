# HackUTA

# SportSense

# Sports Video Analysis - Agentic AI System

An intelligent sports video analysis platform that uses **LangChain agents**, **Agentuity orchestration**, and **multi-modal AI** to provide comprehensive performance analysis for basketball, soccer, and tennis.

## 🎯 Overview

This system analyzes sports videos and generates:
- **Annotated videos** with pose tracking, statistics, and real-time feedback
- **Shot-by-shot/event-by-event analysis** with technical feedback
- **AI-powered coaching summaries** with strengths, weaknesses, and improvement drills
- **Voice-narrated feedback** using ElevenLabs text-to-speech

## 🏗️ Architecture

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Agent Framework** | LangChain ReAct Agent |
| **Orchestration** | Agentuity |
| **LLM** | Google Gemini 2.5 Flash |
| **Computer Vision** | OpenCV + MediaPipe |
| **RAG Knowledge Base** | Sport-specific PDFs + Gemini |
| **Voice Synthesis** | ElevenLabs API |
| **API Framework** | FastAPI |
| **Video Processing** | FFmpeg |

### System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER UPLOADS VIDEO                      │
│                  (FastAPI: main.py)                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              AGENTIC ORCHESTRATION LAYER                    │
│           (LangChain Agent: sports_agent.py)                │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  LangChain ReAct Agent with 4 Specialized Tools    │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        │                                            │
        ▼                                            ▼
┌──────────────────┐                    ┌──────────────────────┐
│   STEP 1: ANALYSIS                    │   STEP 2: ANNOTATION │
│                  │                    │                      │
│  Tool: Gemini    │                    │  Tool: OpenCV +      │
│  Video Analyzer  │                    │  MediaPipe           │
│                  │                    │                      │
│  • Upload video  │                    │  • Pose detection    │
│  • Apply prompts │                    │  • Stats overlays    │
│  • Extract data  │                    │  • Feedback text     │
│  • Save JSON     │                    │  • Voice integration │
└──────────────────┘                    └──────────────────────┘
        │                                            │
        └─────────────────────┬─────────────────────┘
                              ▼
                    ┌──────────────────┐
                    │  STEP 3: COACHING│
                    │                  │
                    │  Tool: RAG       │
                    │  Summary         │
                    │                  │
                    │  • Load KB PDF   │
                    │  • Analyze data  │
                    │  • Generate tips │
                    └──────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    RETURN TO USER                           │
│  • Annotated Video (streaming)                              │
│  • Analysis JSON (in headers)                               │
│  • Coaching Summary (in headers)                            │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
HackUTA/
├── main.py                      # FastAPI server with agentic integration
├── sports_agent.py              # LangChain agent orchestrator
├── agent_tools.py               # LangChain tool definitions
├── analysis.py                  # Gemini video analysis (legacy, wrapped in tool)
├── ball.py                      # OpenCV/MediaPipe annotation (legacy, wrapped in tool)
├── coaching_rag.py              # RAG coaching system (legacy, wrapped in tool)
├── voice.py                     # ElevenLabs voice generation
│
├── docs/                        # Sport knowledge bases
│   ├── Basketball_Knowledge_Base_for_AI.pdf
│   ├── Soccer_Knowledge_Base_for_AI.pdf
│   └── Tennis_Knowledge_Base_for_AI.pdf
│
├── uploads/                     # Temporary video storage
├── sports.json                  # Analysis output (root directory)
│
├── requirements.txt             # Python dependencies
├── .env                         # API keys (not in git)
├── README.md                    # This file
└── AGENT_ARCHITECTURE.md        # Detailed architecture docs
```

## 🔧 Core Components

### 1. FastAPI Server (`main.py`)

**Purpose**: HTTP API endpoint for video uploads and analysis requests

**Key Endpoints**:
- `POST /analyze` - Main video analysis endpoint
- `GET /sports` - List supported sports
- `GET /download/analysis` - Download analysis JSON
- `GET /agents/info` - Get agent system information

**Flow**:
1. Receives video upload and sport type
2. Saves video to `uploads/` directory
3. Calls `SportsVideoAnalysisAgent` to orchestrate analysis
4. Streams annotated video back to client
5. Includes analysis data and coaching summary in response headers
6. Cleans up temporary files

### 2. Agent Orchestrator (`sports_agent.py`)

**Purpose**: LangChain ReAct agent that orchestrates the entire workflow

**Architecture**:
- **LangChain ReAct Agent** - Decision-making and tool execution
- **Agentuity-Compatible** - Ready for deployment via Agentuity server
- **Sequential Workflow** - Three-step process with context sharing

**Workflow Steps**:

#### Step 1: Video Analysis
```python
# Prompt structure
Use gemini_video_analyzer tool
Input: {"video_path": "...", "sport": "...", "output_path": "sports.json"}
Output: JSON with shots/events, timestamps, results, feedback
```

#### Step 2: Video Annotation
```python
# Prompt structure
Use opencv_mediapipe_annotator tool
Input: {"video_path": "...", "analysis_data": "{...}", "output_path": "...", "sport": "..."}
Output: Annotated video file path
```

#### Step 3: Coaching Summary
```python
# Prompt structure
Use rag_coaching_summary tool
Input: {"sport": "...", "analysis_data": "{...}"}
Output: Coaching summary paragraph
```

### 3. LangChain Tools (`agent_tools.py`)

**Purpose**: Wraps existing functionality as LangChain tools for agent use

#### Tool 1: GeminiVideoAnalysisTool
- **Function**: Analyzes video using Gemini AI
- **Input**: `video_path`, `sport`, `output_path`
- **Process**:
  1. Upload video to Gemini API
  2. Apply sport-specific prompt (basketball/soccer/tennis)
  3. Extract structured JSON analysis
  4. Validate output format
  5. Save to JSON file
- **Output**: Analysis data with timestamps, shot types, results, technical feedback

#### Tool 2: OpenCVMediaPipeAnnotationTool
- **Function**: Annotates video with visual overlays
- **Input**: `video_path`, `analysis_data`, `output_path`, `sport`
- **Process**:
  1. Load video with OpenCV
  2. Detect pose with MediaPipe
  3. Add player indicator arrow
  4. Display sport-specific stats:
     - Basketball: Shots Made/Missed
     - Soccer: Goals Scored/Missed
     - Tennis: Successful/Unsuccessful Strokes
  5. Overlay feedback text at timestamps
  6. Generate voice audio with ElevenLabs
  7. Merge audio with video using FFmpeg
- **Output**: Annotated video file

#### Tool 3: ElevenLabsVoiceTool
- **Function**: Generate speech from text
- **Input**: `text`, `output_path`
- **Process**: Call ElevenLabs API to convert text to MP3
- **Output**: Audio file path

#### Tool 4: RAGCoachingSummaryTool
- **Function**: Generate coaching recommendations using RAG
- **Input**: `sport`, `analysis_data`
- **Process**:
  1. Load sport-specific PDF knowledge base
  2. Upload PDF to Gemini
  3. Analyze performance data with KB context
  4. Generate summary with:
     - Performance overview
     - 2-3 key strengths
     - 2-3 areas for improvement
     - Specific drills/exercises
     - Motivational closing
- **Output**: Coaching summary paragraph

### 4. Video Analysis (`analysis.py`)

**Purpose**: Gemini-based video analysis (wrapped by GeminiVideoAnalysisTool)

**Sport-Specific Prompts**:

**Basketball**:
- Identifies: shot type, result (made/missed), timestamp
- Feedback on: form, balance, follow-through, footwork
- Tracks: total shots made/missed, layups made
- Output format: Concise 10-12 word feedback per shot

**Soccer**:
- Identifies: event type (goal/missed_shot/pass/foul), player action, timestamp
- Feedback on: shooting, passing, positioning, ball control
- Output format: Technical coaching tips per event

**Tennis**:
- Identifies: shot type (forehand/backhand/serve), result (winner/error/in_play), timestamp
- Feedback on: grip, footwork, swing, follow-through
- Output format: Technique improvement suggestions

### 5. Video Annotation (`ball.py`)

**Purpose**: OpenCV/MediaPipe-based video annotation (wrapped by OpenCVMediaPipeAnnotationTool)

**Features**:

1. **Pose Detection** (MediaPipe):
   - Tracks player head position
   - Adds red arrow indicator above player

2. **Statistics Display**:
   - Basketball: "Shots Made: X" / "Shots Missed: X"
   - Soccer: "Goals Scored: X" / "Goals Missed: X"
   - Tennis: "Successful Strokes: X" / "Unsuccessful Strokes: X"
   - Color animation on events (green=success, red=fail)

3. **Feedback Overlay**:
   - Displays technical feedback at bottom of frame
   - Appears for 4 seconds after each event
   - Text wrapping for long feedback

4. **Voice Integration**:
   - Generates MP3 audio for each feedback using ElevenLabs
   - Syncs audio with video timestamps using FFmpeg
   - Mixes multiple audio tracks

5. **Video Codecs**:
   - Tries codecs in order: 'avc1', 'mp4v', 'XVID'
   - Ensures compatibility across platforms

### 6. RAG Coaching System (`coaching_rag.py`)

**Purpose**: Generate personalized coaching using sport knowledge bases

**Knowledge Bases**:
- `Basketball_Knowledge_Base_for_AI.pdf` - Basketball fundamentals, drills, techniques
- `Soccer_Knowledge_Base_for_AI.pdf` - Soccer skills, tactics, training methods
- `Tennis_Knowledge_Base_for_AI.pdf` - Tennis strokes, strategy, practice routines

**Process**:
1. Upload sport-specific PDF to Gemini
2. Create prompt with:
   - Session statistics summary
   - Shot-by-shot/event-by-event feedback recap
   - Request for coaching analysis
3. Gemini generates summary referencing KB content
4. Output: 4-6 sentence paragraph with actionable advice

### 7. Voice Generation (`voice.py`)

**Purpose**: Text-to-speech using ElevenLabs API

**Configuration**:
- Voice ID: Configurable via `ELEVENLABS_VOICE_ID`
- Default voice: "EXAVITQu4vr4xnSDxMaL" (professional male coach)
- Output: MP3 format

**Integration**:
- Called by `ball.py` for each feedback item
- Audio files stored in temp directory
- Synced with video using FFmpeg filter_complex

## 🚀 Setup & Installation

### Prerequisites
- Python 3.8+
- FFmpeg (for audio/video processing)
- API Keys:
  - Google Gemini API
  - ElevenLabs API

### Installation

1. **Clone repository**:
```bash
cd HackUTA
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
Create `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id  # Optional
```

5. **Install FFmpeg**:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Running the Server

```bash
# Development mode
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server runs on: `http://localhost:8000`

API docs: `http://localhost:8000/docs`

## 📡 API Usage

### Analyze Video

**Endpoint**: `POST /analyze`

**Request**:
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "sport=basketball" \
  -F "video=@path/to/video.mp4"
```

**Response**:
- **Body**: Annotated video file (streaming)
- **Headers**:
  - `X-Analysis-Data`: JSON analysis string
  - `X-Coaching-Summary`: Coaching paragraph
  - `X-Agentic-System`: "LangChain + Agentuity"

### Download Analysis JSON

**Endpoint**: `GET /download/analysis`

**Response**: `sports.json` file

### Get Agent Info

**Endpoint**: `GET /agents/info`

**Response**:
```json
{
  "agent_framework": "Agentuity + LangChain",
  "agents": [...],
  "workflow": "Sequential task execution with context sharing between agents"
}
```

## 🎾 Supported Sports

### Basketball
- **Shot Types**: Layup, mid-range, three-pointer, free throw
- **Metrics**: Shots made/missed, shooting percentage
- **Feedback Focus**: Form, balance, follow-through, elbow position

### Soccer
- **Events**: Goals, missed shots, passes, fouls
- **Metrics**: Goals scored/missed
- **Feedback Focus**: Ball control, body positioning, technique

### Tennis
- **Shot Types**: Forehand, backhand, serve
- **Metrics**: Winners, errors, successful strokes
- **Feedback Focus**: Grip, footwork, swing mechanics, shoulder rotation

## 🧪 Example Workflow

1. **User uploads basketball video** via API or web interface

2. **Agent Step 1 - Analysis**:
   - Video uploaded to Gemini
   - AI identifies 5 shots:
     - Shot 1: Mid-range (missed) - "Elbow under ball, follow through higher"
     - Shot 2: Layup (made) - "Good extension, keep shoulders square"
     - ...
   - Saves to `sports.json`

3. **Agent Step 2 - Annotation**:
   - OpenCV loads video
   - MediaPipe tracks player pose
   - Overlays stats: "Shots Made: 3 | Shots Missed: 2"
   - Adds feedback text at timestamps
   - ElevenLabs generates voice narration
   - FFmpeg merges audio

4. **Agent Step 3 - Coaching**:
   - Loads `Basketball_Knowledge_Base_for_AI.pdf`
   - Gemini analyzes: 60% shooting, good layups, weak mid-range
   - Generates summary:
     > "Your session showed strong finishing at the rim with 100% layup accuracy,
     > demonstrating excellent body control near the basket. However, your mid-range
     > shooting needs attention - focus on keeping your elbow aligned under the ball
     > and following through higher. Practice the form shooting drill from 10-15 feet,
     > taking 50 shots daily with emphasis on elbow position. Your footwork is solid,
     > which is a great foundation to build upon."

5. **Response to User**:
   - Streams annotated video
   - Headers contain analysis JSON and coaching summary

## 🔑 Key Advantages

### Agentic Architecture Benefits

1. **Modularity**: Each tool is independent and swappable
2. **Scalability**: Easy to add new sports or analysis types
3. **Context Awareness**: Agents share information across workflow
4. **Intelligent Routing**: LangChain agent decides tool execution
5. **Error Handling**: Agent retries and adapts to failures
6. **Observability**: Verbose logging from agent executor

### Technical Advantages

1. **Multi-Modal AI**: Combines vision (Gemini), speech (ElevenLabs), reasoning (LangChain)
2. **RAG Integration**: Knowledge bases provide expert coaching context
3. **Real-Time Processing**: Streaming video responses
4. **Professional Output**: Annotated videos with stats, feedback, and voice

## 🛠️ Development

### Adding a New Sport

1. **Update `analysis.py`**:
   - Add sport-specific prompt to `SPORT_PROMPTS`
   - Add validation function

2. **Update `ball.py`**:
   - Add stat counters for the sport
   - Define event tracking logic
   - Add display formatting

3. **Add Knowledge Base**:
   - Place PDF in `docs/` directory
   - Update `coaching_rag.py` with PDF mapping

4. **Update `main.py`**:
   - Add sport to `SUPPORTED_SPORTS` list

### Testing Tools Individually

```python
# Test Gemini analysis
from agent_tools import GeminiVideoAnalysisTool
tool = GeminiVideoAnalysisTool()
result = tool._run(tool_input='{"video_path": "video.mp4", "sport": "basketball", "output_path": "output.json"}')

# Test annotation
from agent_tools import OpenCVMediaPipeAnnotationTool
tool = OpenCVMediaPipeAnnotationTool()
result = tool._run(tool_input='{"video_path": "video.mp4", "analysis_data": "{...}", "output_path": "out.mp4", "sport": "basketball"}')

# Test RAG
from agent_tools import RAGCoachingSummaryTool
tool = RAGCoachingSummaryTool()
result = tool._run(tool_input='{"sport": "basketball", "analysis_data": "{...}"}')
```

## 📊 Performance Metrics

- **Video Analysis**: ~30-60 seconds (depends on video length)
- **Annotation**: ~10-30 seconds per minute of video
- **Coaching Summary**: ~10-20 seconds
- **Total Processing**: ~1-2 minutes for typical 30-second video

## 🚨 Troubleshooting

### Common Issues

**1. Protobuf Version Conflicts**
```bash
pip install "protobuf>=4.25.3,<5.0" --force-reinstall
```

**2. FFmpeg Not Found**
```bash
# Install FFmpeg (see installation section)
# Ensure it's in system PATH
```

**3. Gemini API Errors**
- Check API key in `.env`
- Verify quota/billing on Google Cloud Console
- Ensure video file is accessible

**4. Agent Tool Parsing Errors**
- Ensure prompts include exact JSON format
- Check tool input is valid JSON string
- Review agent verbose output for debugging

**5. MediaPipe Errors**
- Ensure video file is valid (not corrupted)
- Check OpenCV can read the video codec
- Try converting video to MP4 with H.264 codec

## 📝 License

Copyright 2025 HackUTA Team

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 🔗 Links

- [LangChain Documentation](https://python.langchain.com/)
- [Agentuity Documentation](https://agentuity.com/docs)
- [Google Gemini API](https://ai.google.dev/)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [MediaPipe](https://google.github.io/mediapipe/)

## 👥 Team

Built with ❤️ for HackUTA 2025

---

**Note**: This is an AI-powered system. Analysis quality depends on video quality, lighting, and camera angle. For best results, use clear, well-lit videos with full player visibility.
