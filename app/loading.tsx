import React, { useEffect } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';

// Screen copy constants
const SCREEN_COPY = {
  title: 'Analyzing your moves…',
  subtitle: 'Our AI is reviewing your technique',
  loadingDelay: 2200, // 2.2 seconds
};

export default function LoadingScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  useEffect(() => {
    // Navigate to session screen after delay
    const timer = setTimeout(() => {
      if (id) {
        router.replace(`/session/${id}`);
      }
    }, SCREEN_COPY.loadingDelay);

    // Cleanup timer on unmount
    return () => clearTimeout(timer);
  }, [id]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Loading Spinner */}
        <ActivityIndicator
          size="large"
          color="#3b82f6"
          style={styles.spinner}
          accessibilityLabel="Analyzing"
        />
        
        {/* Title */}
        <Text style={styles.title}>{SCREEN_COPY.title}</Text>
        
        {/* Subtitle */}
        <Text style={styles.subtitle}>{SCREEN_COPY.subtitle}</Text>
        
        {/* Debug info (remove in production) */}
        {__DEV__ && id && (
          <View style={styles.debugInfo}>
            <Text style={styles.debugText}>Session ID: {id}</Text>
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
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  spinner: {
    marginBottom: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e293b',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 24,
    maxWidth: 280,
  },
  debugInfo: {
    position: 'absolute',
    bottom: 40,
    left: 20,
    right: 20,
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