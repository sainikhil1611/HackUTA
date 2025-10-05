import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in .env file")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

DOCS_DIR = Path("docs")
KB_DIR = Path("kb")
KB_DIR.mkdir(exist_ok=True)

# Sport to PDF mapping
SPORT_DOCS = {
    "basketball": "Basketball_Knowledge_Base_for_AI.pdf",
    "soccer": "Soccer_Knowledge_Base_for_AI.pdf",
    "tennis": "Tennis_Knowledge_Base_for_AI.pdf"
}


def upload_knowledge_base(sport: str) -> str:
    """
    Upload and process the knowledge base PDF for a specific sport.
    Returns the file URI for use in Gemini API.
    """
    pdf_filename = SPORT_DOCS.get(sport.lower())
    if not pdf_filename:
        raise ValueError(f"No knowledge base found for sport: {sport}")

    pdf_path = DOCS_DIR / pdf_filename
    if not pdf_path.exists():
        raise FileNotFoundError(f"Knowledge base PDF not found: {pdf_path}")

    print(f"Uploading knowledge base for {sport}...")
    uploaded_file = genai.upload_file(path=str(pdf_path))
    print(f"Knowledge base uploaded: {uploaded_file.name}")

    return uploaded_file


def generate_coaching_summary(sport: str, analysis_data: dict) -> str:
    """
    Generate a comprehensive coaching summary using RAG.

    Args:
        sport: The sport type (basketball, soccer, or tennis)
        analysis_data: The analysis data from analyze_video

    Returns:
        A paragraph summarizing the session with coaching tips
    """
    # Upload the knowledge base for this sport
    kb_file = upload_knowledge_base(sport)

    # Create the model
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048,
        },
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )

    # Prepare the analysis summary
    if sport == "basketball":
        shots = analysis_data.get("shots", [])
        total_shots = len(shots)
        made_shots = sum(1 for s in shots if s.get("result") == "made")
        missed_shots = total_shots - made_shots
        shot_percentage = (made_shots / total_shots * 100) if total_shots > 0 else 0

        analysis_summary = f"""
Session Statistics:
- Total shots attempted: {total_shots}
- Shots made: {made_shots}
- Shots missed: {missed_shots}
- Shooting percentage: {shot_percentage:.1f}%

Shot-by-shot feedback:
"""
        for i, shot in enumerate(shots, 1):
            analysis_summary += f"\nShot {i} ({shot.get('shot_type', 'Unknown')}): {shot.get('result', 'Unknown')}\n"
            analysis_summary += f"Feedback: {shot.get('feedback', 'No feedback')}\n"

    elif sport == "soccer":
        events = analysis_data.get("events", [])
        total_events = len(events)
        goals = sum(1 for e in events if e.get("event_type") == "goal")

        analysis_summary = f"""
Session Statistics:
- Total events: {total_events}
- Goals scored: {goals}

Event-by-event feedback:
"""
        for i, event in enumerate(events, 1):
            analysis_summary += f"\nEvent {i} ({event.get('event_type', 'Unknown')}): {event.get('player_action', 'Unknown')}\n"
            analysis_summary += f"Feedback: {event.get('feedback', 'No feedback')}\n"

    elif sport == "tennis":
        shots = analysis_data.get("shots", [])
        total_shots = len(shots)
        winners = sum(1 for s in shots if s.get("result") == "winner")
        errors = sum(1 for s in shots if s.get("result") == "error")

        analysis_summary = f"""
Session Statistics:
- Total shots: {total_shots}
- Winners: {winners}
- Errors: {errors}

Shot-by-shot feedback:
"""
        for i, shot in enumerate(shots, 1):
            analysis_summary += f"\nShot {i} ({shot.get('shot_type', 'Unknown')}): {shot.get('result', 'Unknown')}\n"
            analysis_summary += f"Feedback: {shot.get('feedback', 'No feedback')}\n"

    else:
        analysis_summary = json.dumps(analysis_data, indent=2)

    # Create the prompt for coaching summary
    prompt = f"""
You are an expert {sport} coach with years of experience training athletes at all levels.

Based on the attached {sport} knowledge base document and the following session analysis,
provide a comprehensive coaching summary paragraph (4-6 sentences) that includes:

1. An overview of the player's performance in this session
2. Identification of 2-3 key strengths demonstrated
3. Identification of 2-3 areas for improvement or weaknesses
4. Specific drills or exercises the player should practice to address their weaknesses
5. Motivational closing that encourages continued practice

Session Analysis:
{analysis_summary}

Write the summary in a professional, encouraging, yet honest coaching tone.
Be specific and actionable with your recommendations.
Reference concepts from the knowledge base when relevant.

Provide ONLY the coaching summary paragraph, no additional formatting or preamble.
"""

    print("Generating coaching summary with RAG...")
    response = model.generate_content([kb_file, prompt])
    coaching_summary = response.text.strip()

    # Clean up the uploaded file
    try:
        genai.delete_file(kb_file.name)
        print("Cleaned up knowledge base file")
    except Exception as e:
        print(f"Warning: Could not delete knowledge base file: {e}")

    return coaching_summary


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python coaching_rag.py <sport> <analysis_json_path>")
        print("Example: python coaching_rag.py basketball sports.json")
        sys.exit(1)

    sport = sys.argv[1]
    analysis_path = sys.argv[2]

    with open(analysis_path, 'r') as f:
        analysis_data = json.load(f)

    summary = generate_coaching_summary(sport, analysis_data)
    print("\n" + "="*80)
    print("COACHING SUMMARY")
    print("="*80)
    print(summary)
    print("="*80)
