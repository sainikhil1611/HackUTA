from analysis import VideoAnalyzer

class TennisVideoAnalyzer(VideoAnalyzer):

    def create_analysis_prompt(self):
        return """
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
    
    def validate_output(self, data):
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
