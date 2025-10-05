// Mock API functions for the AI Basketball Coach app

export type Skill = 'jump_shot' | 'free_throw' | 'layup' | 'dribbling';
export type Sport = 'basketball' | 'soccer' | 'tennis';

export interface SessionResponse {
  id: string;
}

export interface VideoAnalysisResponse {
  status: 'success' | 'error';
  sport: Sport;
  analysis: any; // Analysis data structure
  analysis_file: string;
  annotated_video: string;
}

export interface VideoAnalysisRequest {
  sport: Sport;
  videoFile: File;
}

export interface Tip {
  t: number; // timestamp in seconds
  text: string;
  voiceUrl?: string; // optional audio URL
}

export interface Session {
  id: string;
  sport: string;
  skill: Skill;
  annotatedVideoUrl: string;
  tips: Tip[];
  createdAt: string; // ISO string
}

/**
 * Mock function to create a new session
 * Simulates a POST /api/session request
 * @param skill - The basketball skill being practiced
 * @returns Promise resolving to a session object with generated ID
 */
export async function createSession(skill: Skill): Promise<SessionResponse> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300));
  
  // Generate a timestamp-based session ID
  const timestamp = Date.now();
  const randomSuffix = Math.random().toString(36).substring(2, 8);
  const sessionId = `session_${timestamp}_${randomSuffix}`;
  
  return {
    id: sessionId
  };
}

/**
 * Mock function to get session data
 * Simulates a GET /api/session/:id request
 * @param id - The session ID
 * @returns Promise resolving to session data or null if not found
 */
export async function getSession(id: string): Promise<Session | null> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 200));
  
  // Mock session data - in a real app this would come from a database
  const mockSession: Session = {
    id,
    sport: 'basketball',
    skill: 'jump_shot', // This would be determined from the actual session
    annotatedVideoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4', // Sample basketball training video
    tips: [
        {
          t: 2.5,
          text: 'Keep your elbow aligned under the ball',
          voiceUrl: undefined // No audio for this tip
        },
        {
          t: 5.8,
          text: 'Follow through with your wrist snap',
          voiceUrl: undefined
        },
        {
          t: 9.2,
          text: 'Maintain consistent shooting form',
          voiceUrl: undefined
        },
        {
          t: 12.1,
          text: 'Focus on your target before shooting',
          voiceUrl: undefined
        },
        {
          t: 15.3,
          text: 'Use your legs for power, not just your arms',
          voiceUrl: undefined
        },
        {
          t: 18.7,
          text: 'Keep your shooting hand centered on the ball',
          voiceUrl: undefined
        }
      ],
    createdAt: new Date().toISOString()
  };
  
  // Simulate potential session not found
  if (id.includes('notfound')) {
    return null;
  }
  
  return mockSession;
}

/**
 * Mock function to get all sessions
 * Simulates a GET /api/sessions request
 * @returns Promise resolving to array of sessions
 */
export async function getSessions(): Promise<Session[]> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300));
  
  // Mock sessions data - in a real app this would come from a database
  const mockSessions: Session[] = [
    {
      id: 'session_1703123456789_abc123',
      sport: 'basketball',
      skill: 'jump_shot',
      annotatedVideoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
      tips: [
        { t: 2.5, text: 'Keep your elbow aligned under the ball' },
        { t: 5.8, text: 'Follow through with your wrist snap' }
      ],
      createdAt: new Date(Date.now() - 86400000).toISOString() // 1 day ago
    },
    {
      id: 'session_1703037056789_def456',
      sport: 'basketball',
      skill: 'free_throw',
      annotatedVideoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
      tips: [
        { t: 1.2, text: 'Establish consistent routine' },
        { t: 4.5, text: 'Focus on the back of the rim' }
      ],
      createdAt: new Date(Date.now() - 172800000).toISOString() // 2 days ago
    },
    {
      id: 'session_1702950656789_ghi789',
      sport: 'basketball',
      skill: 'layup',
      annotatedVideoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
      tips: [
        { t: 3.1, text: 'Use proper footwork approach' },
        { t: 6.8, text: 'Soft touch on the backboard' }
      ],
      createdAt: new Date(Date.now() - 259200000).toISOString() // 3 days ago
    },
    {
      id: 'session_1702864256789_jkl012',
      sport: 'basketball',
      skill: 'dribbling',
      annotatedVideoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
      tips: [
        { t: 2.0, text: 'Keep your head up while dribbling' },
        { t: 7.3, text: 'Use fingertips, not palm' }
      ],
      createdAt: new Date(Date.now() - 345600000).toISOString() // 4 days ago
    }
  ];
  
  return mockSessions;
}

/**
 * Function to analyze video using the sports analysis API
 * @param sport - The sport type for analysis
 * @param videoFile - The video file to analyze (React Native file object with uri, type, name)
 * @param baseUrl - The base URL of the analysis server (default: http://10.234.129.141:8000)
 * @returns Promise resolving to analysis response
 */
export async function analyzeVideo(
  sport: Sport, 
  videoFile: any, // React Native file object
  baseUrl: string = 'http://10.234.129.141:8000'
): Promise<VideoAnalysisResponse> {
  try {
    // Validate inputs
    if (!sport || !videoFile) {
      throw new Error('Sport and video file are required for analysis');
    }

    // Check if video file is valid (React Native format)
    if (!videoFile.type || !videoFile.type.startsWith('video/')) {
      throw new Error('Invalid file type. Please provide a video file.');
    }

    const formData = new FormData();
    formData.append('sport', sport);
    
    // For React Native, append the file with uri, type, and name
    formData.append('video', videoFile as any);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout

    console.log(`Starting video analysis request to: ${baseUrl}/analyze`);
    console.log(`Video file info:`, { type: videoFile.type, name: videoFile.name });

    try {
      const response = await fetch(`${baseUrl}/analyze`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log(`Analysis response status: ${response.status}`);

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorMessage = `Analysis failed with status ${response.status}`;
        
        switch (response.status) {
          case 400:
            errorMessage = 'Invalid video format or sport type. Please check your inputs.';
            break;
          case 404:
            errorMessage = 'Analysis service not found. Please check server connection.';
            break;
          case 413:
            errorMessage = 'Video file is too large. Please use a smaller file.';
            break;
          case 500:
            errorMessage = 'Server error during analysis. Please try again later.';
            break;
          case 503:
            errorMessage = 'Analysis service is temporarily unavailable. Please try again later.';
            break;
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      
      // Validate response structure
      if (!result.status || !result.sport) {
        throw new Error('Invalid response format from analysis service');
      }

      return result;
    } catch (fetchError: any) {
      clearTimeout(timeoutId);
      
      if (fetchError.name === 'AbortError') {
        throw new Error('Analysis request timed out after 2 minutes. The server may be processing or unavailable.');
      }
      
      throw fetchError;
    }
  } catch (error: any) {
    console.error('Video analysis failed:', error);
    
    // Enhance error messages for common network issues
    if (error.message?.includes('fetch')) {
      throw new Error('Network error: Unable to connect to analysis server. Please check your internet connection.');
    }
    
    throw error;
  }
}

/**
 * Function to get supported sports from the analysis API
 * @param baseUrl - The base URL of the analysis server (default: http://10.234.129.141:8000)
 * @returns Promise resolving to array of supported sports
 */
export async function getSupportedSports(baseUrl: string = 'http://10.234.129.141:8000'): Promise<Sport[]> {
  try {
    const response = await fetch(`${baseUrl}/sports`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const sports = await response.json();
    return sports;
  } catch (error) {
    console.error('Failed to get supported sports:', error);
    // Return default sports if API fails
    return ['basketball', 'soccer', 'tennis'];
  }
}

/**
 * Function to download analysis JSON from the analysis API
 * @param baseUrl - The base URL of the analysis server (default: http://10.234.129.141:8000)
 * @returns Promise resolving to analysis JSON data
 */
export async function downloadAnalysis(baseUrl: string = 'http://10.234.129.141:8000'): Promise<any> {
  try {
    const response = await fetch(`${baseUrl}/download/analysis`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const analysis = await response.json();
    return analysis;
  } catch (error) {
    console.error('Failed to download analysis:', error);
    throw error;
  }
}

/**
 * Function to get annotated video URL from the analysis API
 * @param sport - The sport type
 * @param baseUrl - The base URL of the analysis server (default: http://10.234.129.141:8000)
 * @returns URL string for the annotated video
 */
export function getAnnotatedVideoUrl(sport: Sport, baseUrl: string = 'http://10.234.129.141:8000'): string {
  return `${baseUrl}/download/video/${sport}`;
}