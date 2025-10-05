"""
LangChain Tools for Sports Video Analysis
Each tool wraps a specific functionality component
"""

import os
import json
from typing import Dict, Any, ClassVar
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import time
import cv2
import mediapipe as mp
import numpy as np
from voice import generate_speech
import tempfile

load_dotenv()


# ========== GEMINI VIDEO ANALYSIS TOOL ==========

class GeminiAnalysisInput(BaseModel):
    video_path: str = Field(description="Path to the video file to analyze")
    sport: str = Field(description="Sport type: basketball, soccer, or tennis")
    output_path: str = Field(description="Path to save the analysis JSON output")


class GeminiVideoAnalysisTool(BaseTool):
    name: str = "gemini_video_analyzer"
    description: str = """
    Uses Google Gemini AI to analyze sports videos and generate detailed shot-by-shot or event-by-event analysis.
    Input: JSON with video_path (str), sport (str), output_path (str)
    Returns JSON data with timestamps, shot types, results, and technical feedback.
    """

    SPORT_PROMPTS: ClassVar[Dict[str, str]] = {
        "basketball": """
This is a slowed-down basketball video.
For each shot in the video, identify the outcome (made or missed), the type of shot (layup, mid-range, three-pointer, etc.), and the timestamp.
Provide specific, technical feedback on technique (form, balance, follow-through, footwork) in a demanding, professional style.

IMPORTANT: Keep feedback CONCISE - maximum 10-12 words. Focus on ONE key improvement point per shot.

Output MUST be valid JSON in this format:

{
    "shots": [
        {
            "timestamp": "0:07.5",
            "shot_type": "Mid-range jump shot (right wing)",
            "result": "missed",
            "total_shots_made_so_far": 0,
            "total_shots_missed_so_far": 1,
            "total_layups_made_so_far": 0,
            "feedback": "Elbow under ball, follow through higher"
        }
    ]
}

Remember: Feedback must be SHORT (10-12 words max), direct, and actionable.
""",
        "soccer": """
This is a slowed-down soccer video.
For each event in the video, identify the type of event (goal, missed_shot, pass, foul), the timestamp, and the player action.
Provide specific, technical feedback on technique (shooting, passing, positioning, ball control) in a demanding, professional style.

Output MUST be valid JSON in this format:

{
    "events": [
        {
            "timestamp": "0:12.3",
            "event_type": "goal",
            "player_action": "right-footed shot",
            "feedback": "Keep your body over the ball for more control"
        }
    ]
}
""",
        "tennis": """
This is a slowed-down tennis video.
For each shot in the video, identify the outcome (winner, error, in_play), the type of shot (forehand, backhand, serve), and the timestamp.
Provide specific, technical feedback on technique (grip, footwork, swing, follow-through) in a demanding, professional style.

Output MUST be valid JSON in this format:

{
    "shots": [
        {
            "timestamp": "0:05.6",
            "shot_type": "forehand",
            "result": "winner",
            "feedback": "Good shoulder rotation but step forward more for power"
        }
    ]
}
"""
    }

    def _run(self, tool_input: str = "", **kwargs) -> Dict[str, Any]:
        """Execute Gemini video analysis"""
        # Parse JSON input if it's a string
        if isinstance(tool_input, str) and tool_input:
            try:
                params = json.loads(tool_input)
                video_path = params.get('video_path', '')
                sport = params.get('sport', '')
                output_path = params.get('output_path', '')
            except json.JSONDecodeError:
                video_path = kwargs.get('video_path', '')
                sport = kwargs.get('sport', '')
                output_path = kwargs.get('output_path', '')
        else:
            video_path = kwargs.get('video_path', '')
            sport = kwargs.get('sport', '')
            output_path = kwargs.get('output_path', '')

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

        try:
            print(f"[Gemini Tool] Uploading video: {video_path}")
            video_file = genai.upload_file(path=video_path)

            while video_file.state.name == "PROCESSING":
                print("[Gemini Tool] Processing video...")
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                raise ValueError(f"Video processing failed: {video_file.state}")

            print("[Gemini Tool] Analyzing video...")
            prompt = self.SPORT_PROMPTS[sport]
            response = model.generate_content([video_file, prompt])
            response_text = response.text.strip()

            # Clean JSON response
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            try:
                analysis_data = json.loads(response_text)
            except json.JSONDecodeError:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    analysis_data = json.loads(response_text[start_idx:end_idx])
                else:
                    raise ValueError("Could not extract valid JSON from response")

            # Save to file
            with open(output_path, 'w') as f:
                json.dump(analysis_data, f, indent=2)

            # Cleanup
            genai.delete_file(video_file.name)
            print(f"[Gemini Tool] Analysis complete: {output_path}")

            return analysis_data

        except Exception as e:
            print(f"[Gemini Tool] Error: {e}")
            raise

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented")


# ========== OPENCV + MEDIAPIPE VISUALIZATION TOOL ==========

class VideoAnnotationInput(BaseModel):
    video_path: str = Field(description="Path to the input video file")
    analysis_data: str = Field(description="JSON string of analysis data")
    output_path: str = Field(description="Path to save annotated video")
    sport: str = Field(description="Sport type: basketball, soccer, or tennis")


class OpenCVMediaPipeAnnotationTool(BaseTool):
    name: str = "opencv_mediapipe_annotator"
    description: str = """
    Uses OpenCV and MediaPipe to annotate videos with pose detection, statistics overlays, and feedback text.
    Input: JSON with video_path (str), analysis_data (str), output_path (str), sport (str)
    Tracks player movements and adds visual indicators and counters.
    """

    def _run(self, tool_input: str = "", **kwargs) -> str:
        """Execute video annotation with OpenCV and MediaPipe"""
        # Parse JSON input if it's a string
        if isinstance(tool_input, str) and tool_input:
            try:
                params = json.loads(tool_input)
                video_path = params.get('video_path', '')
                analysis_data = params.get('analysis_data', '{}')
                output_path = params.get('output_path', '')
                sport = params.get('sport', '')
            except json.JSONDecodeError:
                video_path = kwargs.get('video_path', '')
                analysis_data = kwargs.get('analysis_data', '{}')
                output_path = kwargs.get('output_path', '')
                sport = kwargs.get('sport', '')
        else:
            video_path = kwargs.get('video_path', '')
            analysis_data = kwargs.get('analysis_data', '{}')
            output_path = kwargs.get('output_path', '')
            sport = kwargs.get('sport', '')

        # Parse analysis data if it's a string
        if isinstance(analysis_data, str):
            analysis_data = json.loads(analysis_data)

        print(f"[OpenCV/MediaPipe Tool] Starting annotation for {sport}")

        # Import the existing annotate_video function
        from ball import annotate_video

        # Execute annotation
        annotate_video(video_path, analysis_data, output_path, sport)

        print(f"[OpenCV/MediaPipe Tool] Annotation complete: {output_path}")
        return output_path

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented")


# ========== ELEVENLABS VOICE TOOL ==========

class VoiceGenerationInput(BaseModel):
    text: str = Field(description="Text to convert to speech")
    output_path: str = Field(description="Path to save audio file")


class ElevenLabsVoiceTool(BaseTool):
    name: str = "elevenlabs_voice_generator"
    description: str = """
    Uses ElevenLabs API to generate natural-sounding voice feedback from text.
    Input: JSON with text (str), output_path (str)
    Used for audio coaching feedback in videos.
    """

    def _run(self, tool_input: str = "", **kwargs) -> str:
        """Generate speech from text"""
        # Parse JSON input if it's a string
        if isinstance(tool_input, str) and tool_input:
            try:
                params = json.loads(tool_input)
                text = params.get('text', '')
                output_path = params.get('output_path', '')
            except json.JSONDecodeError:
                text = kwargs.get('text', '')
                output_path = kwargs.get('output_path', '')
        else:
            text = kwargs.get('text', '')
            output_path = kwargs.get('output_path', '')

        print(f"[ElevenLabs Tool] Generating speech: '{text[:50]}...'")

        try:
            generate_speech(text, output_path)
            print(f"[ElevenLabs Tool] Audio saved: {output_path}")
            return output_path
        except Exception as e:
            print(f"[ElevenLabs Tool] Warning: {e}")
            return None

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented")


# ========== RAG COACHING SUMMARY TOOL ==========

class CoachingSummaryInput(BaseModel):
    sport: str = Field(description="Sport type: basketball, soccer, or tennis")
    analysis_data: str = Field(description="JSON string of analysis data")


class RAGCoachingSummaryTool(BaseTool):
    name: str = "rag_coaching_summary"
    description: str = """
    Uses RAG (Retrieval-Augmented Generation) with sport-specific knowledge bases to generate
    comprehensive coaching summaries with strengths, weaknesses, and improvement drills.
    Input: JSON with sport (str), analysis_data (str)
    """

    def _run(self, tool_input: str = "", **kwargs) -> str:
        """Generate coaching summary using RAG"""
        # Parse JSON input if it's a string
        if isinstance(tool_input, str) and tool_input:
            try:
                params = json.loads(tool_input)
                sport = params.get('sport', '')
                analysis_data = params.get('analysis_data', '{}')
            except json.JSONDecodeError:
                sport = kwargs.get('sport', '')
                analysis_data = kwargs.get('analysis_data', '{}')
        else:
            sport = kwargs.get('sport', '')
            analysis_data = kwargs.get('analysis_data', '{}')

        # Parse analysis data if it's a string
        if isinstance(analysis_data, str):
            analysis_data = json.loads(analysis_data)

        print(f"[RAG Tool] Generating coaching summary for {sport}")

        from coaching_rag import generate_coaching_summary

        summary = generate_coaching_summary(sport, analysis_data)

        print(f"[RAG Tool] Coaching summary generated")
        return summary

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented")


# Export all tools
def get_all_tools():
    """Returns list of all available tools"""
    return [
        GeminiVideoAnalysisTool(),
        OpenCVMediaPipeAnnotationTool(),
        ElevenLabsVoiceTool(),
        RAGCoachingSummaryTool()
    ]
