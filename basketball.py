from analysis import VideoAnalyzer

class BasketballVideoAnalyzer(VideoAnalyzer):

    def create_analysis_prompt(self):
        return """
This is a slowed-down basketball video.
For each shot in the video, identify the outcome (made or missed), the type of shot (layup, mid-range, three-pointer, etc.), and the timestamp.
Provide specific, technical feedback on technique (form, balance, follow-through, footwork) in a demanding, professional style.

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
            "feedback": "You're pushing that ball, not shooting it; get your elbow under, extend fully, and follow through."
        }
    ]
}
"""
    
    def validate_output(self, data):
        required_fields = [
            "timestamp",
            "shot_type",
            "result",
            "total_shots_made_so_far",
            "total_shots_missed_so_far",
            "total_layups_made_so_far",
            "feedback"
        ]

        if "shots" not in data:
            raise ValueError("Output must contain 'shots' array")

        for i, shot in enumerate(data["shots"]):
            for field in required_fields:
                if field not in shot:
                    raise ValueError(f"Shot {i} missing required field: {field}")
            if shot["result"] not in ["made", "missed"]:
                raise ValueError(f"Shot {i} has invalid result: {shot['result']}")

        print("✓ Basketball output validation passed")
