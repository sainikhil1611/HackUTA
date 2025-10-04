import os
import time
import json
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in .env file")

SPORT_PROMPTS = {
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

def _validate_basketball(data):
    required_fields = ["timestamp", "shot_type", "result", "total_shots_made_so_far",
                       "total_shots_missed_so_far", "total_layups_made_so_far", "feedback"]
    if "shots" not in data:
        raise ValueError("Output must contain 'shots' array")
    for i, shot in enumerate(data["shots"]):
        for field in required_fields:
            if field not in shot:
                raise ValueError(f"Shot {i} missing required field: {field}")
        if shot["result"] not in ["made", "missed"]:
            raise ValueError(f"Shot {i} has invalid result: {shot['result']}")
    print("✓ Basketball output validation passed")

def _validate_soccer(data):
    required_fields = ["timestamp", "event_type", "player_action", "feedback"]
    if "events" not in data:
        raise ValueError("Output must contain 'events' array")
    for i, event in enumerate(data["events"]):
        for field in required_fields:
            if field not in event:
                raise ValueError(f"Event {i} missing required field: {field}")
        if event["event_type"] not in ["goal", "missed_shot", "pass", "foul"]:
            raise ValueError(f"Event {i} has invalid type: {event['event_type']}")
    print("✓ Soccer output validation passed")

def _validate_tennis(data):
    required_fields = ["timestamp", "shot_type", "result", "feedback"]
    if "shots" not in data:
        raise ValueError("Output must contain 'shots' array")
    for i, shot in enumerate(data["shots"]):
        for field in required_fields:
            if field not in shot:
                raise ValueError(f"Shot {i} missing required field: {field}")
        if shot["result"] not in ["winner", "error", "in_play"]:
            raise ValueError(f"Shot {i} has invalid result: {shot['result']}")
    print("✓ Tennis output validation passed")

VALIDATORS = {
    "basketball": _validate_basketball,
    "soccer": _validate_soccer,
    "tennis": _validate_tennis
}

def analyze_video(video_path, sport, output_path):
    """Analyze video using Gemini AI based on sport type"""
    genai.configure(api_key=GEMINI_API_KEY)

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
        print("Analyzing video with Gemini...")

        prompt = SPORT_PROMPTS[sport]
        response = model.generate_content([video_file, prompt])
        response_text = response.text.strip()
        print(f"Raw response: {response_text[:500]}...")

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

        VALIDATORS[sport](analysis_data)

        with open(output_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)

        print(f"Analysis complete! Results saved to: {output_path}")
        genai.delete_file(video_file.name)
        print("Cleaned up uploaded video file")

        return analysis_data

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python analysis.py <video_path> <sport> <output_path>")
        print("Example: python analysis.py final_ball.mp4 basketball sports.json")
        sys.exit(1)

    video_path = sys.argv[1]
    sport = sys.argv[2]
    output_path = sys.argv[3]

    analyze_video(video_path, sport, output_path)
