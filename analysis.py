import os
import time
import json
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Load environment variables from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in .env file")

class VideoAnalyzer:
    """Generic video analyzer using Gemini API"""

    def __init__(self, api_key=GEMINI_API_KEY, model_name="gemini-2.5-flash"):
        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(
            model_name=model_name,
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

    def upload_video(self, video_path):
        """Upload video to Gemini and wait for processing"""
        print(f"Uploading video: {video_path}")
        video_file = genai.upload_file(path=video_path)
        print(f"Video uploaded: {video_file.name}")

        while video_file.state.name == "PROCESSING":
            print("Processing video...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError(f"Video processing failed: {video_file.state}")

        print("Video processing complete!")
        return video_file

    def analyze_video(self, video_path, prompt, output_path):
        """Analyze video using a provided prompt and save results"""
        try:
            video_file = self.upload_video(video_path)
            print("Analyzing video with Gemini...")
            response = self.model.generate_content([video_file, prompt])

            response_text = response.text.strip()
            print(f"Raw response: {response_text[:500]}...")

            analysis_data = self._parse_response(response_text)
            self.validate_output(analysis_data)  # Will call subclass method

            with open(output_path, 'w') as f:
                json.dump(analysis_data, f, indent=2)

            print(f"Analysis complete! Results saved to: {output_path}")
            genai.delete_file(video_file.name)
            print("Cleaned up uploaded video file")
            return analysis_data

        except Exception as e:
            print(f"Error during analysis: {e}")
            raise

    def _parse_response(self, response_text):
        """Extract JSON from response"""
        try:
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            return json.loads(response_text)
        except json.JSONDecodeError:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                return json.loads(response_text[start_idx:end_idx])
            else:
                raise ValueError("Could not extract valid JSON from response")

    def validate_output(self, data):
        """Sport-specific validation must be implemented in subclass"""
        raise NotImplementedError("Subclasses must implement validate_output()")
