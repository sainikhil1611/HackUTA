import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { createSession, type Skill } from '../lib/api';

// Screen copy constants for extensibility
const SCREEN_COPY = {
  title: 'Record Your Move',
  subtitle: 'Position yourself in frame and hit record when ready',
  cameraPlaceholder: 'Camera preview will appear here',
  recordIdle: 'Tap to start recording',
  recordActive: 'Tap to stop',
  cameraIcon: '📹'
};

export default function RecordScreen() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Get query parameters with fallback logic
  const { sport, skill } = useLocalSearchParams<{
    sport?: string;
    skill?: Skill;
  }>();

  // Resolve skill with priority: URL param > fallback "jump_shot"
  // Resolve sport with fallback "basketball" for MVP
  const resolvedSport = sport || "basketball";
  const resolvedSkill: Skill = skill || "jump_shot";

  const handleRecordToggle = async () => {
    if (!isRecording) {
      // Start recording
      setIsRecording(true);
    } else {
      // Stop recording and create session
      try {
        setIsProcessing(true);
        
        // Call mock API to create session with resolved skill
        const session = await createSession(resolvedSkill);
        
        // Navigate to loading screen with session ID
        router.replace({
          pathname: '/loading',
          params: { id: session.id }
        });
      } catch (error) {
        Alert.alert('Error', 'Failed to create session. Please try again.');
        setIsRecording(false);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  // Prevent navigation while recording (optional guard)
  React.useEffect(() => {
    if (isRecording) {
      const unsubscribe = router.canGoBack;
      // Note: This is a simple implementation. In a real app, you might want
      // to show a confirmation dialog before allowing navigation away while recording
    }
  }, [isRecording]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>{SCREEN_COPY.title}</Text>
          <Text style={styles.subtitle}>{SCREEN_COPY.subtitle}</Text>
        </View>

        {/* Camera Preview Placeholder */}
        <View style={styles.cameraContainer}>
          <View 
            style={styles.cameraPreview}
            testID="camera-preview"
          >
            <Text style={styles.cameraIcon}>{SCREEN_COPY.cameraIcon}</Text>
            <Text style={styles.cameraPlaceholder}>
              {SCREEN_COPY.cameraPlaceholder}
            </Text>
          </View>
        </View>

        {/* Record Toggle Button */}
        <View style={styles.controlsContainer}>
          <TouchableOpacity
            style={[
              styles.recordButton,
              isRecording ? styles.recordButtonActive : styles.recordButtonIdle
            ]}
            onPress={handleRecordToggle}
            disabled={isProcessing}
            activeOpacity={0.8}
            testID="record-toggle"
            accessibilityLabel={isRecording ? 'Stop recording' : 'Start recording'}
            accessibilityRole="button"
          >
            <Text style={[
              styles.recordButtonText,
              isRecording ? styles.recordButtonTextActive : styles.recordButtonTextIdle
            ]}>
              {isProcessing 
                ? 'Processing...' 
                : isRecording 
                  ? SCREEN_COPY.recordActive 
                  : SCREEN_COPY.recordIdle
              }
            </Text>
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
    backgroundColor: '#f8fafc',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1e293b',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 24,
  },
  cameraContainer: {
    flex: 1,
    marginBottom: 24,
  },
  cameraPreview: {
    flex: 1,
    backgroundColor: '#e2e8f0',
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 400,
  },
  cameraIcon: {
    fontSize: 48,
    marginBottom: 16,
    opacity: 0.6,
  },
  cameraPlaceholder: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
  },
  controlsContainer: {
    alignItems: 'center',
    paddingBottom: 20,
  },
  recordButton: {
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 50,
    minWidth: 200,
    minHeight: 44, // Accessibility minimum touch target
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  recordButtonIdle: {
    backgroundColor: '#10b981', // Green
  },
  recordButtonActive: {
    backgroundColor: '#ef4444', // Red
  },
  recordButtonText: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
  recordButtonTextIdle: {
    color: '#ffffff',
  },
  recordButtonTextActive: {
    color: '#ffffff',
  },
  debugInfo: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#f1f5f9',
    borderRadius: 8,
  },
  debugText: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'center',
  },
});