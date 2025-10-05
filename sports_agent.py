"""
Sports Video Analysis Agent using LangChain with Agentuity deployment support
Orchestrates LangChain tools for comprehensive video analysis
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

from agent_tools import get_all_tools

load_dotenv()


class SportsVideoAnalysisAgent:
    """
    Main agent for sports video analysis workflow
    Uses LangChain ReAct agent with Agentuity-compatible tools
    """

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1
        )

        # Initialize LangChain tools
        self.tools = get_all_tools()

        # Create LangChain ReAct agent
        prompt = PromptTemplate.from_template("""
You are a sports video analysis expert that orchestrates multiple specialized tools.

Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action as a JSON object with required parameters
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: Action Input must be valid JSON.
For gemini_video_analyzer, use: {{"video_path": "path", "sport": "sport_name", "output_path": "output.json"}}
For opencv_mediapipe_annotator, use: {{"video_path": "path", "analysis_data": "json_string", "output_path": "out.mp4", "sport": "sport_name"}}
For rag_coaching_summary, use: {{"sport": "sport_name", "analysis_data": "json_string"}}

Question: {input}
Thought: {agent_scratchpad}
""")

        self.agent = create_react_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )

    def analyze_video(self, video_path: str, sport: str, output_dir: Path) -> Dict[str, Any]:
        """
        Main workflow to analyze a sports video

        Args:
            video_path: Path to input video
            sport: Sport type (basketball, soccer, tennis)
            output_dir: Directory for output files

        Returns:
            Dictionary with analysis results, annotated video path, and coaching summary
        """

        print(f"\n{'='*80}")
        print(f"AGENTUITY-POWERED SPORTS VIDEO ANALYSIS")
        print(f"Sport: {sport.upper()}")
        print(f"Video: {video_path}")
        print(f"{'='*80}\n")

        # Define output paths
        analysis_json_path = str(Path("sports.json"))
        annotated_video_path = str(output_dir / f"{sport}_annotated_temp.mp4")

        # Step 1: Video Analysis
        print("\n[Agent] Step 1: Video Analysis with Gemini...")
        analysis_prompt = f"""
        Use the gemini_video_analyzer tool to analyze the sports video.
        Call it with this exact JSON input:
        {{"video_path": "{video_path}", "sport": "{sport}", "output_path": "{analysis_json_path}"}}
        """

        try:
            self.agent_executor.invoke({"input": analysis_prompt})
            print(f"[Agent] Analysis complete")
        except Exception as e:
            print(f"[Agent] Error in analysis: {e}")
            raise

        # Load analysis data
        with open(analysis_json_path, 'r') as f:
            analysis_data = json.load(f)

        # Step 2: Video Annotation
        print("\n[Agent] Step 2: Video Annotation with OpenCV/MediaPipe...")
        annotation_prompt = f"""
        Use the opencv_mediapipe_annotator tool to annotate the video.
        Call it with this exact JSON input:
        {{"video_path": "{video_path}", "analysis_data": '{json.dumps(analysis_data)}', "output_path": "{annotated_video_path}", "sport": "{sport}"}}
        """

        try:
            self.agent_executor.invoke({"input": annotation_prompt})
            print(f"[Agent] Annotation complete")
        except Exception as e:
            print(f"[Agent] Error in annotation: {e}")
            raise

        # Step 3: Coaching Summary with RAG
        print("\n[Agent] Step 3: Generating Coaching Summary with RAG...")
        coaching_prompt = f"""
        Use the rag_coaching_summary tool to generate a coaching summary.
        Call it with this exact JSON input:
        {{"sport": "{sport}", "analysis_data": '{json.dumps(analysis_data)}'}}
        """

        try:
            coaching_result = self.agent_executor.invoke({"input": coaching_prompt})
            # Extract the coaching summary from the agent's output
            coaching_summary = coaching_result.get('output', str(coaching_result))
            print(f"[Agent] Coaching summary generated")
        except Exception as e:
            print(f"[Agent] Error in coaching summary: {e}")
            raise

        print(f"\n[Agent] Workflow complete!")

        return {
            "status": "success",
            "sport": sport,
            "analysis_data": analysis_data,
            "annotated_video_path": annotated_video_path,
            "coaching_summary": coaching_summary,
            "analysis_json_path": analysis_json_path
        }


def run_analysis(video_path: str, sport: str, output_dir: str = "uploads") -> Dict[str, Any]:
    """
    Convenience function to run sports video analysis

    Args:
        video_path: Path to video file
        sport: Sport type (basketball, soccer, tennis)
        output_dir: Output directory for results

    Returns:
        Analysis results dictionary
    """
    agent_system = SportsVideoAnalysisAgent()
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    return agent_system.analyze_video(video_path, sport.lower(), output_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python sports_agent.py <video_path> <sport>")
        print("Example: python sports_agent.py final_ball.mp4 basketball")
        sys.exit(1)

    video_path = sys.argv[1]
    sport = sys.argv[2]

    result = run_analysis(video_path, sport)

    print("\n" + "="*80)
    print("AGENTUITY-POWERED ANALYSIS COMPLETE")
    print("="*80)
    print(f"Analysis JSON: {result['analysis_json_path']}")
    print(f"Annotated Video: {result['annotated_video_path']}")
    print(f"\nCoaching Summary:")
    print(result['coaching_summary'])
    print("="*80)
