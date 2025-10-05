import React, { useEffect, useRef } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  FlatList,
  Image,
  Dimensions,
  Animated,
  StyleSheet,
  TouchableWithoutFeedback,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Session, Skill } from '../lib/api';

interface PastSessionsDrawerProps {
  visible: boolean;
  onClose: () => void;
  sessions: Session[];
  onSelect: (id: string) => void;
}

const { width: screenWidth } = Dimensions.get('window');

// Helper function to pretty-case skill names
const prettySkill = (skill: Skill): string => {
  switch (skill) {
    case 'jump_shot':
      return 'Jump Shot';
    case 'free_throw':
      return 'Free Throw';
    case 'layup':
      return 'Layup';
    case 'dribbling':
      return 'Dribbling';
    default:
      return skill;
  }
};

export default function PastSessionsDrawer({
  visible,
  onClose,
  sessions,
  onSelect,
}: PastSessionsDrawerProps) {
  const insets = useSafeAreaInsets();
  const slideAnim = useRef(new Animated.Value(screenWidth)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;

  // Calculate panel width: 82% of screen, clamped between 360-560px
  const panelWidth = Math.min(Math.max(screenWidth * 0.82, 360), 560);

  useEffect(() => {
    if (visible) {
      // Slide in animation
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(backdropAnim, {
          toValue: 0.45,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      // Slide out animation
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: screenWidth,
          duration: 250,
          useNativeDriver: true,
        }),
        Animated.timing(backdropAnim, {
          toValue: 0,
          duration: 250,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible, slideAnim, backdropAnim]);

  const renderSessionItem = ({ item }: { item: Session }) => {
    const createdDate = new Date(item.createdAt);
    
    return (
      <TouchableOpacity
        style={styles.sessionCard}
        onPress={() => onSelect(item.id)}
        activeOpacity={0.7}
        accessibilityLabel={`Open session ${item.id}`}
        accessibilityRole="button"
      >
        <View style={styles.sessionContent}>
          {/* Thumbnail placeholder */}
          <View style={styles.thumbnail}>
            <Text style={styles.thumbnailText}>🏀</Text>
          </View>
          
          {/* Session info */}
          <View style={styles.sessionInfo}>
            <Text style={styles.sessionTitle}>{prettySkill(item.skill)}</Text>
            <Text style={styles.sessionDate}>
              {createdDate.toLocaleString()}
            </Text>
          </View>
          
          {/* Chevron */}
          <Text style={styles.chevron}>›</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="none"
      onRequestClose={onClose}
    >
      {/* Backdrop */}
      <TouchableWithoutFeedback onPress={onClose}>
        <Animated.View
          style={[
            styles.backdrop,
            {
              opacity: backdropAnim,
            },
          ]}
        />
      </TouchableWithoutFeedback>

      {/* Right Panel */}
      <Animated.View
        style={[
          styles.panel,
          {
            width: panelWidth,
            paddingTop: insets.top + 12,
            paddingRight: insets.right + 16,
            paddingBottom: insets.bottom + 16,
            transform: [{ translateX: slideAnim }],
          },
        ]}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Past Sessions</Text>
          <TouchableOpacity
            style={styles.closeButton}
            onPress={onClose}
            accessibilityLabel="Close past sessions"
            accessibilityRole="button"
          >
            <Text style={styles.closeButtonText}>×</Text>
          </TouchableOpacity>
        </View>

        {/* Sessions List */}
        {sessions.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateText}>No sessions yet</Text>
          </View>
        ) : (
          <FlatList
            data={sessions}
            keyExtractor={(item) => item.id}
            renderItem={renderSessionItem}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
          />
        )}
      </Animated.View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#000',
  },
  panel: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderBottomLeftRadius: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    paddingLeft: 16,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: -2, height: 0 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#000',
  },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: 20,
    color: '#666',
    fontWeight: '300',
  },
  listContent: {
    paddingVertical: 4,
  },
  sessionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    padding: 12,
    marginBottom: 12,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  sessionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  thumbnail: {
    width: 56,
    height: 56,
    borderRadius: 8,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  thumbnailText: {
    fontSize: 24,
  },
  sessionInfo: {
    flex: 1,
  },
  sessionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  sessionDate: {
    fontSize: 14,
    color: '#666',
  },
  chevron: {
    fontSize: 20,
    color: '#ccc',
    fontWeight: '300',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
});