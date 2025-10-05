import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ImageBackground, Alert, TouchableOpacity, Dimensions, BackHandler, FlatList, useWindowDimensions } from 'react-native';
import BottomSheet, { BottomSheetFlatList } from '@gorhom/bottom-sheet';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLocalSearchParams, router } from 'expo-router';
import { Video, ResizeMode, Audio } from 'expo-av';
import Toast from 'react-native-toast-message';
import { getSession, getSessions, Session, Tip } from '../../lib/api';
import PastSessionsDrawer from '../../components/PastSessionsDrawer';

export default function SessionScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [firedTips, setFiredTips] = useState<Set<number>>(new Set());
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  
  const videoRef = useRef<Video>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const bottomSheetRef = useRef<BottomSheet>(null);
  const insets = useSafeAreaInsets();
  const { width: screenWidth, height: screenHeight } = useWindowDimensions();
  const isMobile = screenWidth < 700;

  // Bottom sheet snap points
  const snapPoints = useMemo(() => ['30%', '80%'], []);

  useEffect(() => {
    loadSession();
    loadSessions();
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [id]);

  // Android back handler for drawer
  useEffect(() => {
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (drawerOpen) {
        setDrawerOpen(false);
        return true; // Prevent default back behavior
      }
      return false; // Allow default back behavior
    });

    return () => backHandler.remove();
  }, [drawerOpen]);

  const loadSession = async () => {
    if (!id) {
      setError('No session ID provided');
      setLoading(false);
      return;
    }

    try {
      const sessionData = await getSession(id);
      if (!sessionData) {
        setError('Session not found');
        Toast.show({
          type: 'error',
          text1: 'Session not found',
          text2: 'The requested session could not be found.',
        });
      } else {
        setSession(sessionData);
      }
    } catch (err) {
      setError('Failed to load session');
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: 'Failed to load session data.',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadSessions = async () => {
    try {
      const sessionsData = await getSessions();
      setSessions(sessionsData);
    } catch (err) {
      console.error('Failed to load sessions:', err);
      // Don't show error toast for sessions loading failure as it's not critical
    }
  };

  const startTipPolling = () => {
    if (!session || !videoRef.current) return;

    pollIntervalRef.current = setInterval(async () => {
      try {
        const status = await videoRef.current?.getStatusAsync();
        if (status?.isLoaded && status.positionMillis) {
          const currentTimeSeconds = status.positionMillis / 1000;
          
          // Check for tips that should fire
          session.tips.forEach((tip, index) => {
            if (currentTimeSeconds >= tip.t && !firedTips.has(index)) {
              fireTip(tip, index);
            }
          });
        }
      } catch (error) {
        console.error('Error polling video time:', error);
      }
    }, 300);
  };

  const fireTip = async (tip: Tip, index: number) => {
    // Mark tip as fired
    setFiredTips(prev => new Set(prev).add(index));
    
    // Show toast
    Toast.show({
      type: 'info',
      text1: 'Coach Tip',
      text2: tip.text,
      visibilityTime: 4000,
    });

    // Play audio if available
    if (tip.voiceUrl) {
      try {
        const { sound } = await Audio.Sound.createAsync(
          { uri: tip.voiceUrl },
          { shouldPlay: true }
        );
        // Clean up sound after playing
        sound.setOnPlaybackStatusUpdate((status) => {
          if (status.isLoaded && status.didJustFinish) {
            sound.unloadAsync();
          }
        });
      } catch (error) {
        console.error('Error playing tip audio:', error);
      }
    }
  };

  const onVideoLoad = () => {
    startTipPolling();
  };

  const formatSkillName = (skill: string) => {
    return skill.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const handlePastSessionsPress = () => {
    setDrawerOpen(true);
  };

  // Bottom sheet callbacks
  const handleSheetChanges = useCallback((index: number) => {
    console.log('Bottom sheet changed to index:', index);
  }, []);

  // Calculate responsive panel width
  const panelWidth = Math.max(300, Math.min(420, screenWidth * 0.34));

  // Mobile layout render function
  const renderMobileLayout = () => (
    <View style={styles.mobileContainer}>
      {/* Mobile Title */}
      <View style={[styles.mobileTitle, { paddingTop: insets.top + 12 }]}>
        <Text style={styles.mobileTitleText}>
          {formatSkillName(session?.skill || 'jump_shot')} Analysis • Session #{session?.id || id}
        </Text>
      </View>

      {/* Mobile Video Section - 70% of screen */}
      {session?.annotatedVideoUrl && (
        <View style={[styles.mobileVideoContainer, { height: screenHeight * 0.7 }]}>
          <Video
            ref={videoRef}
            style={styles.mobileVideo}
            source={{ uri: session.annotatedVideoUrl }}
            useNativeControls
            resizeMode={ResizeMode.CONTAIN}
            shouldPlay
            isLooping
            onLoad={onVideoLoad}
          />
        </View>
      )}

      {/* Mobile Coach Tips Section - Bottom Sheet */}
      <BottomSheet
        ref={bottomSheetRef}
        index={0}
        snapPoints={snapPoints}
        onChange={handleSheetChanges}
        enablePanDownToClose={false}
        style={styles.bottomSheet}
      >
        {/* Tips Card Header */}
        <View style={styles.mobileCoachTipsHeader}>
          <Text style={styles.mobileCoachTipsTitle}>Coach Tips</Text>
          <TouchableOpacity
            style={styles.pastSessionsButton}
            onPress={handlePastSessionsPress}
          >
            <Text style={styles.pastSessionsButtonText}>Past Sessions</Text>
          </TouchableOpacity>
        </View>

        {/* Tips FlatList */}
        <BottomSheetFlatList
          data={session?.tips || []}
          keyExtractor={(_, index) => index.toString()}
          renderItem={({ item: tip, index }) => (
            <View style={styles.tipCard}>
              <Text style={styles.tipText}>{tip.text}</Text>
              <Text style={styles.tipTime}>@ {tip.t}s</Text>
            </View>
          )}
          contentContainerStyle={styles.mobileTipsListContent}
          showsVerticalScrollIndicator={false}
        />
      </BottomSheet>
    </View>
  );

  // Desktop layout render function
  const renderDesktopLayout = () => (
    <>
      {/* Main content with hero title */}
      <View style={styles.mainContent}>
        <View style={styles.heroSection}>
          <Text style={styles.title}>Jump Shot Analysis</Text>
          <Text style={styles.subtitle}>Session #{session?.id || id}</Text>
        </View>
      </View>

      {/* Floating right-side panel */}
      <View
        style={[
          styles.floatingPanel,
          {
            top: insets.top + 12,
            right: insets.right + 16,
            width: panelWidth,
          },
        ]}
      >
        {/* Panel header */}
        <View style={styles.panelHeader}>
          <Text style={styles.panelTitle}>Coach Tips</Text>
          <TouchableOpacity
            style={styles.pastSessionsButton}
            onPress={handlePastSessionsPress}
          >
            <Text style={styles.pastSessionsButtonText}>Past Sessions</Text>
          </TouchableOpacity>
        </View>

        {/* Tips list */}
        <ScrollView style={styles.tipsList} showsVerticalScrollIndicator={false}>
          {session?.tips.map((tip, index) => (
            <View key={index} style={styles.tipCard}>
              <Text style={styles.tipText}>{tip.text}</Text>
              <Text style={styles.tipTime}>@ {tip.t}s</Text>
            </View>
          ))}
        </ScrollView>
      </View>

      {/* PiP Video Player */}
      {session?.annotatedVideoUrl && (
        <View
          style={[
            styles.pipContainer,
            {
              bottom: insets.bottom + 20,
              right: 20,
            },
          ]}
        >
          <Video
            ref={videoRef}
            style={styles.pipVideo}
            source={{ uri: session.annotatedVideoUrl }}
            useNativeControls
            resizeMode={ResizeMode.CONTAIN}
            shouldPlay
            isLooping
            onLoad={onVideoLoad}
          />
        </View>
      )}
    </>
  );

  return (
    <View style={styles.container}>
      <ImageBackground
        source={{ uri: 'https://images.unsplash.com/photo-1546519638-68e109498ffc?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80' }}
        style={styles.backgroundImage}
        imageStyle={styles.backgroundImageStyle}
      >
        {loading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading session...</Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : (
          <>
            {isMobile ? renderMobileLayout() : renderDesktopLayout()}
          </>
        )}
      </ImageBackground>
      <Toast />
      
      {/* Past Sessions Drawer */}
      <PastSessionsDrawer
        visible={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        sessions={sessions}
        onSelect={(sessionId) => {
          setDrawerOpen(false);
          router.replace(`/session/${sessionId}`);
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  backgroundImage: {
    flex: 1,
  },
  backgroundImageStyle: {
    opacity: 0.3,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 18,
    color: '#fff',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 18,
    color: '#fff',
    textAlign: 'center',
  },
  mainContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  heroSection: {
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#ccc',
    textAlign: 'center',
  },
  floatingPanel: {
    position: 'absolute',
    backgroundColor: '#fff',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 3,
    },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 6,
    maxHeight: '70%',
    zIndex: 10,
  },
  panelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  panelTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  pastSessionsButton: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 10,
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  pastSessionsButtonText: {
    fontSize: 12,
    color: '#666',
  },
  tipsList: {
    flex: 1,
    padding: 16,
  },
  tipCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    padding: 10,
    marginBottom: 10,
  },
  tipText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
    marginBottom: 4,
  },
  tipTime: {
    fontSize: 12,
    color: '#94a3b8',
  },
  pipContainer: {
    position: 'absolute',
    borderRadius: 8,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    zIndex: 5,
  },
  pipVideo: {
    width: 200,
    height: 120,
  },
  // Mobile-specific styles
  mobileContainer: {
    flex: 1,
  },
  mobileTitle: {
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  mobileTitleText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.7)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  mobileVideoContainer: {
    marginHorizontal: 16,
    marginBottom: 8,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  mobileVideo: {
    width: '100%',
    height: '100%',
  },
  mobileCoachTipsCard: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingHorizontal: 16,
    paddingTop: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
  },
  mobileCoachTipsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  mobileCoachTipsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  mobileTipsList: {
    flex: 1,
  },
  mobileTipsListContent: {
    paddingBottom: 16,
  },
  bottomSheet: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
  },
});