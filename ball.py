import cv2
import mediapipe as mp
import numpy as np
import time
import os
import tempfile
from voice import generate_speech

def parse_timestamp(timestamp):
    minutes, seconds = timestamp.split(':')
    return float(minutes) * 60 + float(seconds)

def timestamp_to_frame(timestamp, fps):
    seconds = parse_timestamp(timestamp)
    return int(seconds * fps)

def wrap_text(text, font, scale, thickness, max_width):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        text_size = cv2.getTextSize(test_line, font, scale, thickness)[0]

        if text_size[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines

def get_animation_color(elapsed_time, animation_duration, is_success):
    if elapsed_time >= animation_duration:
        return (255, 255, 255)

    progress = elapsed_time / animation_duration

    if progress < 0.5:
        if is_success:
            return (int(255 * (1 - progress * 2)), 255, int(255 * (1 - progress * 2)))
        else:
            return (int(255 * (1 - progress * 2)), int(255 * (1 - progress * 2)), 255)
    else:
        if is_success:
            return (int(255 * ((progress - 0.5) * 2)), 255, int(255 * ((progress - 0.5) * 2)))
        else:
            return (int(255 * ((progress - 0.5) * 2)), int(255 * ((progress - 0.5) * 2)), 255)

def annotate_video(video_path, analysis_data, output_path, sport_type):
    """Annotate video with analysis data based on sport type"""

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    processed_frames = []
    last_head = None
    frame_count = 0
    process_every_n_frames = max(1, int(fps / 20))
    animation_duration = 1.25
    last_event_time = None
    last_event_result = None
    current_color = (255, 255, 255)

    # Create temporary directory for audio files
    temp_dir = tempfile.mkdtemp()
    audio_files = []

    # Prepare events based on sport type
    events = []
    if sport_type == "basketball":
        for i, shot in enumerate(analysis_data.get('shots', [])):
            timestamp = shot.get('timestamp_of_outcome') or shot.get('timestamp')
            audio_path = os.path.join(temp_dir, f"feedback_{i}.mp3")
            try:
                generate_speech(shot['feedback'], audio_path)
                audio_files.append((timestamp_to_frame(timestamp, fps), audio_path))
            except Exception as e:
                print(f"Warning: Could not generate audio for feedback {i}: {e}")

            events.append({
                'frame_number': timestamp_to_frame(timestamp, fps),
                'feedback_end_frame': timestamp_to_frame(timestamp, fps) + (4 * fps),
                'result': shot['result'],
                'feedback': shot['feedback'],
                'made_count': shot.get('total_shots_made_so_far', 0),
                'missed_count': shot.get('total_shots_missed_so_far', 0)
            })
    elif sport_type == "soccer":
        goals_scored = 0
        goals_missed = 0
        for i, event in enumerate(analysis_data.get('events', [])):
            is_goal = event['event_type'] in ['goal', 'missed_shot']
            if is_goal:
                if event['event_type'] == 'goal':
                    goals_scored += 1
                else:
                    goals_missed += 1

            audio_path = os.path.join(temp_dir, f"feedback_{i}.mp3")
            try:
                generate_speech(event['feedback'], audio_path)
                audio_files.append((timestamp_to_frame(event['timestamp'], fps), audio_path))
            except Exception as e:
                print(f"Warning: Could not generate audio for feedback {i}: {e}")

            events.append({
                'frame_number': timestamp_to_frame(event['timestamp'], fps),
                'feedback_end_frame': timestamp_to_frame(event['timestamp'], fps) + (4 * fps),
                'result': 'goal' if event['event_type'] == 'goal' else 'missed',
                'feedback': event['feedback'],
                'event_type': event['event_type'],
                'goals_scored': goals_scored,
                'goals_missed': goals_missed
            })
    elif sport_type == "tennis":
        successful_strokes = 0
        unsuccessful_strokes = 0
        for i, shot in enumerate(analysis_data.get('shots', [])):
            if shot['result'] == 'winner':
                successful_strokes += 1
            elif shot['result'] == 'error':
                unsuccessful_strokes += 1

            audio_path = os.path.join(temp_dir, f"feedback_{i}.mp3")
            try:
                generate_speech(shot['feedback'], audio_path)
                audio_files.append((timestamp_to_frame(shot['timestamp'], fps), audio_path))
            except Exception as e:
                print(f"Warning: Could not generate audio for feedback {i}: {e}")

            events.append({
                'frame_number': timestamp_to_frame(shot['timestamp'], fps),
                'feedback_end_frame': timestamp_to_frame(shot['timestamp'], fps) + (4 * fps),
                'result': shot['result'],
                'feedback': shot['feedback'],
                'shot_type': shot['shot_type'],
                'successful_strokes': successful_strokes,
                'unsuccessful_strokes': unsuccessful_strokes
            })

    print(f"Processing video: {video_path}")
    print(f"Total events to annotate: {len(events)}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Process pose detection
        if frame_count % process_every_n_frames == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)

            if results.pose_landmarks:
                head = results.pose_landmarks.landmark[0]
                head_x = int(head.x * width)
                head_y = int(head.y * height)
                last_head = (head_x, head_y)

        # Draw player indicator
        if last_head is not None:
            head_x, head_y = last_head
            arrow_height = 30
            arrow_width = 45
            arrow_tip_y = max(0, head_y - 110)
            pt1 = (head_x, arrow_tip_y + arrow_height)
            pt2 = (head_x - arrow_width // 2, arrow_tip_y)
            pt3 = (head_x + arrow_width // 2, arrow_tip_y)
            pts = np.array([pt1, pt2, pt3], np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(frame, [pts], (0, 0, 255))

            font = cv2.FONT_HERSHEY_SIMPLEX
            text = "Player"
            text_size = cv2.getTextSize(text, font, 0.8, 2)[0]
            text_x = head_x - text_size[0] // 2
            text_y = arrow_tip_y - 10
            cv2.putText(frame, text, (text_x, text_y), font, 0.8, (0, 0, 0), 6, cv2.LINE_AA)
            cv2.putText(frame, text, (text_x, text_y), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        # Update stats and feedback - only show feedback for the most recent active event
        current_stats = {}
        current_feedback = None
        active_event = None

        for event in events:
            if event['frame_number'] <= frame_count:
                if event['frame_number'] == frame_count:
                    last_event_time = time.time()
                    last_event_result = event['result']

                if sport_type == "basketball":
                    current_stats = {
                        'made': event.get('made_count', 0),
                        'missed': event.get('missed_count', 0)
                    }
                elif sport_type == "soccer":
                    current_stats = {
                        'scored': event.get('goals_scored', 0),
                        'missed': event.get('goals_missed', 0)
                    }
                elif sport_type == "tennis":
                    current_stats = {
                        'successful': event.get('successful_strokes', 0),
                        'unsuccessful': event.get('unsuccessful_strokes', 0)
                    }

                # Only keep the most recent active feedback
                if event['frame_number'] <= frame_count <= event['feedback_end_frame']:
                    active_event = event

        # Set current feedback only from the most recent active event
        if active_event:
            current_feedback = active_event['feedback']

        # Calculate animation color
        if last_event_time is not None:
            elapsed_time = time.time() - last_event_time
            if elapsed_time < animation_duration:
                is_success = last_event_result in ['made', 'success']
                current_color = get_animation_color(elapsed_time, animation_duration, is_success)
            else:
                current_color = (255, 255, 255)
                last_event_time = None

        # Draw statistics for all sports
        if current_stats:
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.8
            thickness = 2
            border_thickness = 4
            spacing = 35
            x = 20
            y = 40

            if sport_type == "basketball":
                made = current_stats.get('made', 0)
                missed = current_stats.get('missed', 0)

                made_text = f"Shots Made: {made}"
                cv2.putText(frame, made_text, (x, y), font, scale, (0, 0, 0), border_thickness, cv2.LINE_AA)
                made_color = current_color if last_event_result == 'made' else (255, 255, 255)
                cv2.putText(frame, made_text, (x, y), font, scale, made_color, thickness, cv2.LINE_AA)

                missed_text = f"Shots Missed: {missed}"
                cv2.putText(frame, missed_text, (x, y + spacing), font, scale, (0, 0, 0), border_thickness, cv2.LINE_AA)
                missed_color = current_color if last_event_result == 'missed' else (255, 255, 255)
                cv2.putText(frame, missed_text, (x, y + spacing), font, scale, missed_color, thickness, cv2.LINE_AA)

            elif sport_type == "soccer":
                scored = current_stats.get('scored', 0)
                missed = current_stats.get('missed', 0)

                scored_text = f"Goals Scored: {scored}"
                cv2.putText(frame, scored_text, (x, y), font, scale, (0, 0, 0), border_thickness, cv2.LINE_AA)
                scored_color = current_color if last_event_result == 'goal' else (255, 255, 255)
                cv2.putText(frame, scored_text, (x, y), font, scale, scored_color, thickness, cv2.LINE_AA)

                missed_text = f"Goals Missed: {missed}"
                cv2.putText(frame, missed_text, (x, y + spacing), font, scale, (0, 0, 0), border_thickness, cv2.LINE_AA)
                missed_color = current_color if last_event_result == 'missed' else (255, 255, 255)
                cv2.putText(frame, missed_text, (x, y + spacing), font, scale, missed_color, thickness, cv2.LINE_AA)

            elif sport_type == "tennis":
                successful = current_stats.get('successful', 0)
                unsuccessful = current_stats.get('unsuccessful', 0)

                successful_text = f"Successful Strokes: {successful}"
                cv2.putText(frame, successful_text, (x, y), font, scale, (0, 0, 0), border_thickness, cv2.LINE_AA)
                successful_color = current_color if last_event_result == 'winner' else (255, 255, 255)
                cv2.putText(frame, successful_text, (x, y), font, scale, successful_color, thickness, cv2.LINE_AA)

                unsuccessful_text = f"Unsuccessful Strokes: {unsuccessful}"
                cv2.putText(frame, unsuccessful_text, (x, y + spacing), font, scale, (0, 0, 0), border_thickness, cv2.LINE_AA)
                unsuccessful_color = current_color if last_event_result == 'error' else (255, 255, 255)
                cv2.putText(frame, unsuccessful_text, (x, y + spacing), font, scale, unsuccessful_color, thickness, cv2.LINE_AA)

        # Draw feedback - only show current feedback, clearing previous ones
        if current_feedback:
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.6
            thickness = 1
            border_thickness = 3
            max_width = int(width * 0.9)
            wrapped_lines = wrap_text(current_feedback, font, scale, thickness, max_width)
            feedback_text = current_feedback
            text_size = cv2.getTextSize(feedback_text, font, scale, thickness)[0]

            if text_size[0] > max_width:
                # Calculate total height needed for all lines
                line_height = 25
                total_height = len(wrapped_lines) * line_height
                feedback_y = height - 60 - total_height + line_height

                for line in wrapped_lines:
                    text_size = cv2.getTextSize(line, font, scale, thickness)[0]
                    feedback_x = (width - text_size[0]) // 2
                    cv2.putText(frame, line, (feedback_x, feedback_y), font, scale, (0, 0, 0), border_thickness, cv2.LINE_AA)
                    cv2.putText(frame, line, (feedback_x, feedback_y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
                    feedback_y += line_height
            else:
                feedback_x = (width - text_size[0]) // 2
                feedback_y = height - 60
                cv2.putText(frame, feedback_text, (feedback_x, feedback_y), font, scale, (0, 0, 0), border_thickness, cv2.LINE_AA)
                cv2.putText(frame, feedback_text, (feedback_x, feedback_y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

        processed_frames.append(frame.copy())

    cap.release()
    pose.close()
    cv2.destroyAllWindows()

    # Write output video
    print("Creating final video...")
    codecs_to_try = ['avc1', 'mp4v', 'XVID']

    out = None
    for codec in codecs_to_try:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if out.isOpened():
            print(f"Using codec: {codec}")
            break
        out.release()

    if out is None or not out.isOpened():
        raise RuntimeError("Failed to initialize video writer with any codec")

    for frame in processed_frames:
        out.write(frame)

    out.release()

    # Add audio to video using ffmpeg
    if audio_files:
        print("Adding audio to video...")
        temp_video_path = output_path.replace('.mp4', '_temp.mp4')
        os.rename(output_path, temp_video_path)

        # Create filter complex for audio
        filter_parts = []
        audio_inputs = []

        for i, (frame_num, audio_path) in enumerate(audio_files):
            timestamp_seconds = frame_num / fps
            audio_inputs.extend(['-i', audio_path])
            filter_parts.append(f"[{i+1}:a]adelay={int(timestamp_seconds * 1000)}|{int(timestamp_seconds * 1000)}[a{i}]")

        if filter_parts:
            filter_complex = ';'.join(filter_parts)
            mix_inputs = ''.join([f"[a{i}]" for i in range(len(audio_files))])
            filter_complex += f";{mix_inputs}amix=inputs={len(audio_files)}:duration=longest[aout]"

            import subprocess
            cmd = ['ffmpeg', '-i', temp_video_path] + audio_inputs + [
                '-filter_complex', filter_complex,
                '-map', '0:v',
                '-map', '[aout]',
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                '-y',
                output_path
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                os.remove(temp_video_path)
                print("Audio integrated successfully!")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Could not add audio to video: {e}")
                print(f"Error output: {e.stderr.decode()}")
                os.rename(temp_video_path, output_path)
            except FileNotFoundError:
                print("Warning: ffmpeg not found. Video saved without audio.")
                os.rename(temp_video_path, output_path)

    # Cleanup temporary audio files
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"Annotated video saved to: {output_path}")

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 4:
        print("Usage: python ball.py <video_path> <sports_json> <output_path> <sport_type>")
        print("Example: python ball.py final_ball.mp4 sports.json final.mp4 basketball")
        sys.exit(1)

    video_path = sys.argv[1]
    json_path = sys.argv[2]
    output_path = sys.argv[3]
    sport_type = sys.argv[4] if len(sys.argv) > 4 else "basketball"

    with open(json_path, 'r') as f:
        analysis_data = json.load(f)

    annotate_video(video_path, analysis_data, output_path, sport_type)
