# Sports Video Analysis - Agentic Architecture

## Overview

This system uses **LangChain** agents with **Agentuity** orchestration for comprehensive sports video analysis. LangChain provides the tool execution framework while Agentuity manages the agent context and workflow orchestration.

## Architecture

### Agent Framework
- **Agent Framework**: LangChain ReAct Agent
- **Orchestration**: Agentuity (AgentContext, AgentRequest, AgentResponse)
- **LLM**: Google Gemini 2.5 Flash
- **Workflow**: Sequential task execution with Agentuity context tracking

### LangChain ReAct Agent

The system uses a single **LangChain ReAct Agent** that has access to multiple specialized tools. The agent uses Agentuity for context management and request/response handling.

**Agent Capabilities**:
- Analyzes videos using Gemini AI
- Annotates videos with OpenCV and MediaPipe
- Generates coaching summaries using RAG
- Orchestrates workflow across all tools

## Tools

### LangChain Tools (agent_tools.py)

1. **GeminiVideoAnalysisTool**
   - Uploads video to Gemini API
   - Applies sport-specific prompts
   - Extracts structured JSON analysis

2. **OpenCVMediaPipeAnnotationTool**
   - Uses OpenCV for video processing
   - Uses MediaPipe for pose detection
   - Adds overlays and counters
   - Integrates voice feedback

3. **ElevenLabsVoiceTool**
   - Converts feedback text to speech
   - Uses ElevenLabs API
   - Generates audio files for video integration

4. **RAGCoachingSummaryTool**
   - Loads sport-specific PDF knowledge bases
   - Uses Gemini with RAG
   - Generates personalized coaching advice

## Workflow

```
User uploads video + sport type
         ↓
FastAPI receives request
         ↓
Agentuity Agent Orchestrator
         ↓
┌─────────────────────────────────────────────┐
│  Step 1: Video Analysis                     │
│  Agentuity Request → LangChain Agent        │
│  Tool: Gemini Video Analyzer                │
│  Agentuity Context: sport, video_path       │
│  Output: analysis_data.json                 │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│  Step 2: Video Annotation                   │
│  Agentuity Request → LangChain Agent        │
│  Tool: OpenCV/MediaPipe Annotator           │
│  Agentuity Context: analysis_data           │
│  Output: annotated_video.mp4                │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│  Step 3: Coaching Summary                   │
│  Agentuity Request → LangChain Agent        │
│  Tool: RAG Coaching Summary                 │
│  Agentuity Context: analysis_data           │
│  Output: coaching_summary.txt               │
└─────────────────────────────────────────────┘
         ↓
Agentuity Response with all results
         ↓
FastAPI returns annotated video
with analysis data and coaching
summary in response headers
```

## File Structure

```
HackUTA/
├── main.py                    # FastAPI with agent integration
├── sports_agent.py           # Agentuity agent orchestrator
├── agent_tools.py            # LangChain tool definitions
├── analysis.py               # Legacy Gemini analysis (wrapped in tool)
├── ball.py                   # Legacy OpenCV/MediaPipe (wrapped in tool)
├── coaching_rag.py           # Legacy RAG system (wrapped in tool)
├── voice.py                  # ElevenLabs voice generation
├── docs/                     # Sport knowledge bases (PDFs)
│   ├── Basketball_Knowledge_Base_for_AI.pdf
│   ├── Soccer_Knowledge_Base_for_AI.pdf
│   └── Tennis_Knowledge_Base_for_AI.pdf
└── requirements.txt          # Dependencies including LangChain & Agentuity
```

## API Endpoints

### POST /analyze
Main endpoint for video analysis. Uses the agentic system to process videos.

**Parameters**:
- `sport`: basketball, soccer, or tennis
- `video`: Video file upload

**Returns**:
- Annotated video (streaming)
- Headers:
  - `X-Analysis-Data`: JSON analysis
  - `X-Coaching-Summary`: Coaching paragraph
  - `X-Agentic-System`: Framework info

### GET /agents/info
Returns information about the agent system and capabilities.

### GET /sports
Lists supported sports.

### GET /download/analysis
Downloads the analysis JSON file.

## Dependencies

```
# Core
fastapi
uvicorn[standard]
python-dotenv

# AI/ML
google-generativeai
langchain
langchain-google-genai
langchain-core
agentuity

# Video Processing
opencv-python
mediapipe
numpy

# Audio
elevenlabs
pydub

# Utils
requests
aiofiles
python-multipart
```

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

```bash
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

## Running the System

```bash
# Start FastAPI server
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Key Advantages of Agentic Architecture

1. **Modularity**: Each agent has a specific role and tools
2. **Scalability**: Easy to add new agents or tools
3. **Context Sharing**: Agents can pass information between tasks
4. **Maintainability**: Clear separation of concerns
5. **Observability**: Verbose logging from Agentuity crew
6. **Flexibility**: Can modify workflow without changing core logic

## Future Enhancements

- Add more specialized agents (e.g., injury risk assessment)
- Implement parallel task execution where possible
- Add agent memory for session continuity
- Integrate more LLM providers
- Add multi-language support for coaching
