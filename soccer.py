from analysis import VideoAnalyzer

class SoccerVideoAnalyzer(VideoAnalyzer):

    def create_analysis_prompt(self):
        return """
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
"""
    
    def validate_output(self, data):
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
