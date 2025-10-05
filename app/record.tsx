import { CameraType, CameraView, useCameraPermissions, useMicrophonePermissions } from 'expo-camera';
import * as FileSystem from 'expo-file-system/legacy';
import { router, useLocalSearchParams } from 'expo-router';
import React, { useEffect, useRef, useState } from 'react';
import { Alert, BackHandler, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createSession, type Skill, type Sport, analyzeVideo } from '../lib/api';
import { s3PresignUpload } from '../lib/stubs';

// Screen copy constants for extensibility
const SCREEN_COPY = {
  title: 'Record Your Move',
  subtitle: 'Position yourself in frame and hit record when ready',
  permissionTitle: 'Camera Access Required',
  permissionMessage: 'We need access to your camera to record your practice videos.',
  enableCamera: 'Enable Camera',
  recordIdle: 'Tap to start recording',
  recordActive: 'Tap to stop',
  processing: 'Processing...',
  maxDuration: 12, // seconds
};

export default function RecordScreen() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [cameraType, setCameraType] = useState<CameraType>('back');
  const [cameraReady, setCameraReady] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();
  const [micPermission, requestMicPermission] = useMicrophonePermissions();
  
  const cameraRef = useRef<CameraView>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const recordingStartTime = useRef<number | null>(null);
  const recordPromiseRef = useRef<Promise<any> | null>(null);
  
  // Get query parameters with fallback logic
  const { sport, skill } = useLocalSearchParams<{
    sport?: string;
    skill?: Skill;
  }>();

  // Resolve skill with priority: URL param > fallback "jump_shot"
  // Resolve sport with fallback "basketball" for MVP
  const resolvedSport = sport || "basketball";
  const resolvedSkill: Skill = skill || "jump_shot";

  // Request permissions on mount
  useEffect(() => {
    const requestPermissions = async () => {
      // Request camera permission
      if (!permission?.granted && permission?.canAskAgain) {
        await requestPermission();
      }
      
      // Request microphone permission for video recording with audio
      if (!micPermission?.granted && micPermission?.canAskAgain) {
        await requestMicPermission();
      }
    };
    
    requestPermissions();
  }, []);

  // Handle Android back button while recording
  useEffect(() => {
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (isRecording) {
        // Prevent exit while recording - stop recording first
        handleStopRecording();
        return true; // Prevent default back behavior
      }
      return false; // Allow default back behavior
    });

    return () => backHandler.remove();
  }, [isRecording]);

  // Timer for recording duration
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          // Auto-stop at max duration
          if (newTime >= SCREEN_COPY.maxDuration) {
            handleStopRecording();
          }
          return newTime;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setRecordingTime(0);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartRecording = async () => {
    // Guard against multiple starts or invalid states
    if (isStarting || isRecording || !cameraReady || !cameraRef.current) return;

    try {
      setIsStarting(true);
      
      // Start recording with proper configuration
      const recordPromise = cameraRef.current.recordAsync({
        maxDuration: SCREEN_COPY.maxDuration,
      });
      
      recordPromiseRef.current = recordPromise;
      recordingStartTime.current = Date.now();
      setIsRecording(true);
      setIsStarting(false);
      
      const video = await recordPromise;
      
      // Check if video was recorded successfully
      if (video && video.uri) {
        // Save to persistent storage
        await handleVideoRecorded(video.uri);
      } else {
        throw new Error('Video recording failed - no video data received');
      }
    } catch (error) {
      console.error('Recording failed:', error);
      Alert.alert('Recording Error', 'Failed to start recording. Please try again.');
      setIsRecording(false);
      setIsStarting(false);
      recordingStartTime.current = null;
      recordPromiseRef.current = null;
    }
  };

  const handleStopRecording = async () => {
    // Guard against multiple stops or invalid states
    if (!isRecording || isStopping || !cameraRef.current) return;

    try {
      setIsStopping(true);

      // Check minimum recording duration (900ms as specified)
      const MIN_RECORDING_DURATION = 900; // 900ms as per requirements
      if (recordingStartTime.current) {
        const recordingDuration = Date.now() - recordingStartTime.current;
        if (recordingDuration < MIN_RECORDING_DURATION) {
          // Wait for the remaining time to ensure minimum duration
          const remainingTime = MIN_RECORDING_DURATION - recordingDuration;
          await new Promise(resolve => setTimeout(resolve, remainingTime));
        }
      }

      // Stop the recording
      await cameraRef.current.stopRecording();
      
      // Wait for the record promise to resolve and validate result
      if (recordPromiseRef.current) {
        const result = await recordPromiseRef.current;
        if (!result || !result.uri) {
          throw new Error('Video recording failed - no video data received');
        }
      }

      // Reset flags to idle state
      setIsRecording(false);
      setIsStopping(false);
      recordingStartTime.current = null;
      recordPromiseRef.current = null;
      
    } catch (error) {
      console.error('Stop recording failed:', error);
      Alert.alert('Recording Error', 'Failed to stop recording properly. Please try again.');
      
      // Reset flags on error
      setIsRecording(false);
      setIsStopping(false);
      recordingStartTime.current = null;
      recordPromiseRef.current = null;
    }
  };

  const handleVideoRecorded = async (videoUri: string) => {
    try {
      setIsProcessing(true);
      
      // Create a persistent file name
      const timestamp = Date.now();
      const fileName = `video_${timestamp}.mp4`;
      const cacheDir = FileSystem.cacheDirectory;
      
      const persistentUri = `${cacheDir}${fileName}`;
      
      // Move video to persistent storage
      await FileSystem.moveAsync({
        from: videoUri,
        to: persistentUri,
      });

      console.log('Video saved to:', persistentUri);

      // Mock upload simulation
      await s3PresignUpload(persistentUri);
      
      // Create session with resolved skill
      const session = await createSession(resolvedSkill);
      
      // Convert video file for analysis
      const videoFile = await createVideoFile(persistentUri);
      
      // Analyze the video using the API
      try {
        const analysisResult = await analyzeVideo(resolvedSport as Sport, videoFile);
        console.log('Video analysis completed:', analysisResult);
        
        // Navigate to loading screen with session ID, video URI, and analysis result
        router.replace({
          pathname: '/loading',
          params: { 
            id: session.id,
            videoUri: persistentUri,
            analysisResult: JSON.stringify(analysisResult)
          }
        });
      } catch (analysisError: any) {
        console.error('Video analysis failed:', analysisError);
        
        // Determine error message based on error type
        let errorMessage = 'Video analysis failed. Please try again.';
        if (analysisError.message?.includes('Network')) {
          errorMessage = 'Network error. Please check your connection and try again.';
        } else if (analysisError.message?.includes('400')) {
          errorMessage = 'Invalid video format or sport type. Please try recording again.';
        } else if (analysisError.message?.includes('500')) {
          errorMessage = 'Server error during analysis. Please try again later.';
        } else if (analysisError.message?.includes('fetch')) {
          errorMessage = 'Unable to connect to analysis server. Please check your network connection.';
        }
        
        // Show user-friendly error alert
        Alert.alert(
          'Analysis Failed', 
          errorMessage + '\n\nYou can still view your recorded video.',
          [
            {
              text: 'View Video',
              onPress: () => {
                router.replace({
                  pathname: '/loading',
                  params: { 
                    id: session.id,
                    videoUri: persistentUri,
                    analysisError: errorMessage
                  }
                });
              }
            },
            {
              text: 'Try Again',
              onPress: () => {
                // Reset to allow user to record again
                setIsProcessing(false);
              }
            }
          ]
        );
        return; // Don't navigate automatically on analysis error
      }
    } catch (error) {
      console.error('Video processing failed:', error);
      Alert.alert('Processing Error', 'Failed to process video. Please try again.');
    } finally {
      setIsRecording(false);
      setIsProcessing(false);
      recordingStartTime.current = null; // Reset start time when processing is complete
    }
  };

  // Helper function to create a File-like object from video URI for React Native
  const createVideoFile = async (videoUri: string): Promise<any> => {
    try {
      const fileName = videoUri.split('/').pop() || 'video.mp4';
      
      // For React Native, we need to create a file object that works with FormData
      return {
        uri: videoUri,
        type: 'video/mp4',
        name: fileName,
      };
    } catch (error) {
      console.error('Error creating video file:', error);
      throw new Error('Failed to prepare video for analysis. Please try recording again.');
    }
  };

  const handleRecordToggle = () => {
    if (isRecording) {
      handleStopRecording();
    } else {
      handleStartRecording();
    }
  };

  const toggleCameraType = () => {
    setCameraType((current: CameraType) => 
      current === 'back' ? 'front' : 'back'
    );
  };

  // Permission not granted UI
  if (!permission?.granted || !micPermission?.granted) {
    const needsCamera = !permission?.granted;
    const needsMicrophone = !micPermission?.granted;
    
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionTitle}>
            {needsCamera && needsMicrophone 
              ? 'Camera & Microphone Access Required'
              : needsCamera 
                ? 'Camera Access Required'
                : 'Microphone Access Required'
            }
          </Text>
          <Text style={styles.permissionMessage}>
            {needsCamera && needsMicrophone
              ? 'We need access to your camera and microphone to record practice videos with audio.'
              : needsCamera
                ? 'We need access to your camera to record your practice videos.'
                : 'We need access to your microphone to record videos with audio.'
            }
          </Text>
          <TouchableOpacity
            style={styles.permissionButton}
            onPress={async () => {
              if (needsCamera) await requestPermission();
              if (needsMicrophone) await requestMicPermission();
            }}
          >
            <Text style={styles.permissionButtonText}>
              {needsCamera && needsMicrophone 
                ? 'Enable Camera & Microphone'
                : needsCamera 
                  ? 'Enable Camera'
                  : 'Enable Microphone'
              }
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>{SCREEN_COPY.title}</Text>
          <Text style={styles.subtitle}>{SCREEN_COPY.subtitle}</Text>
        </View>

        {/* Camera Preview */}
        <View style={styles.cameraContainer}>
          <CameraView
            ref={cameraRef}
            style={styles.camera}
            facing={cameraType}
            mode="video"
            onCameraReady={() => setCameraReady(true)}
          >
            {/* Camera overlay */}
            <View style={styles.cameraOverlay}>
              {/* Timer overlay */}
              {isRecording && (
                <View style={styles.timerContainer}>
                  <View style={styles.recordingDot} />
                  <Text style={styles.timerText}>{formatTime(recordingTime)}</Text>
                </View>
              )}

              {/* Camera flip button */}
              <TouchableOpacity
                style={styles.flipButton}
                onPress={toggleCameraType}
                disabled={isRecording}
              >
                <Text style={styles.flipButtonText}>🔄</Text>
              </TouchableOpacity>
            </View>
          </CameraView>
        </View>

        {/* Record Toggle Button */}
        <View style={styles.controlsContainer}>
          <TouchableOpacity
            style={[
              styles.recordButton,
              isRecording ? styles.recordButtonActive : styles.recordButtonIdle,
              (!cameraReady || !permission?.granted || !micPermission?.granted) && styles.recordButtonDisabled
            ]}
            onPress={handleRecordToggle}
            disabled={isProcessing || !cameraReady || !permission?.granted || !micPermission?.granted}
            activeOpacity={0.8}
            testID="record-toggle"
            accessibilityLabel={isRecording ? 'Stop recording' : 'Start recording'}
            accessibilityRole="button"
          >
            <View style={styles.recordButtonInner}>
              {isProcessing ? (
                <Text style={styles.recordButtonText}>{SCREEN_COPY.processing}</Text>
              ) : (
                <Text style={[
                  styles.recordButtonText,
                  isRecording ? styles.recordButtonTextActive : styles.recordButtonTextIdle
                ]}>
                  {isRecording ? SCREEN_COPY.recordActive : SCREEN_COPY.recordIdle}
                </Text>
              )}
            </View>
          </TouchableOpacity>
        </View>

        {/* Debug info (remove in production) */}
        {__DEV__ && (
          <View style={styles.debugInfo}>
            <Text style={styles.debugText}>
              Sport: {resolvedSport} | Skill: {resolvedSkill}
            </Text>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  content: {
    flex: 1,
  },
  header: {
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#e2e8f0',
    textAlign: 'center',
    lineHeight: 24,
  },
  cameraContainer: {
    flex: 1,
    margin: 12,
    borderRadius: 12,
    overflow: 'hidden',
  },
  camera: {
    flex: 1,
  },
  cameraOverlay: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'space-between',
    padding: 20,
  },
  timerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ef4444',
    marginRight: 8,
  },
  timerText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    fontFamily: 'monospace',
  },
  flipButton: {
    alignSelf: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  flipButtonText: {
    fontSize: 20,
  },
  controlsContainer: {
    alignItems: 'center',
    paddingVertical: 30,
    paddingHorizontal: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  recordButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 5,
  },
  recordButtonIdle: {
    backgroundColor: '#10b981', // Green
  },
  recordButtonActive: {
    backgroundColor: '#ef4444', // Red
  },
  recordButtonDisabled: {
    backgroundColor: '#6b7280', // Gray for disabled state
    opacity: 0.6,
  },
  recordButtonInner: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordButtonText: {
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
    color: '#ffffff',
  },
  recordButtonTextIdle: {
    color: '#ffffff',
  },
  recordButtonTextActive: {
    color: '#ffffff',
  },
  debugInfo: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 12,
    backgroundColor: 'rgba(241, 245, 249, 0.9)',
    borderRadius: 8,
  },
  debugText: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'center',
  },
  // Permission UI styles
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f8fafc',
  },
  permissionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e293b',
    textAlign: 'center',
    marginBottom: 16,
  },
  permissionMessage: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  permissionButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  permissionButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});