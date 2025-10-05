import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';

// Text copy constants for easy edits
const SCREEN_COPY = {
  title: 'Choose Your Sport',
  subtitle: 'Select a sport to begin your training session',
  basketball: {
    title: 'Basketball',
    subtitle: 'Shooting, dribbling, and more',
  },
  soccer: {
    title: 'Soccer',
    subtitle: 'Coming soon',
  },
  fitness: {
    title: 'Fitness',
    subtitle: 'Coming soon',
  },
};

interface SportCardProps {
  title: string;
  subtitle: string;
  icon: string;
  isActive: boolean;
  onPress?: () => void;
  testID: string;
  accessibilityLabel?: string;
}

function SportCard({ 
  title, 
  subtitle, 
  icon, 
  isActive, 
  onPress, 
  testID, 
  accessibilityLabel 
}: SportCardProps) {
  return (
    <TouchableOpacity
      style={[styles.card, !isActive && styles.cardDisabled]}
      onPress={isActive ? onPress : undefined}
      activeOpacity={isActive ? 0.8 : 1}
      testID={testID}
      accessibilityLabel={accessibilityLabel}
      disabled={!isActive}
    >
      <View style={styles.cardContent}>
        <Text style={styles.cardIcon}>{icon}</Text>
        <Text style={[styles.cardTitle, !isActive && styles.cardTitleDisabled]}>
          {title}
        </Text>
        <Text style={[styles.cardSubtitle, !isActive && styles.cardSubtitleDisabled]}>
          {subtitle}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

export default function SportScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>{SCREEN_COPY.title}</Text>
            <Text style={styles.subtitle}>{SCREEN_COPY.subtitle}</Text>
          </View>

          {/* Cards row */}
          <View style={styles.cardsContainer}>
            <SportCard
              title={SCREEN_COPY.basketball.title}
              subtitle={SCREEN_COPY.basketball.subtitle}
              icon="🏀"
              isActive={true}
              onPress={() => router.push({ 
                pathname: "/record", 
                params: { sport: "basketball", skill: "jump_shot" } 
              })}
              testID="card-basketball"
              accessibilityLabel="Basketball, select"
            />
            
            <SportCard
              title={SCREEN_COPY.soccer.title}
              subtitle={SCREEN_COPY.soccer.subtitle}
              icon="⚽"
              isActive={false}
              testID="card-soccer"
            />
            
            <SportCard
              title={SCREEN_COPY.fitness.title}
              subtitle={SCREEN_COPY.fitness.subtitle}
              icon="💪"
              isActive={false}
              testID="card-fitness"
            />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 32,
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1f2937',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 24,
  },
  cardsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 16,
    maxWidth: 400,
  },
  card: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 16,
    padding: 24,
    minHeight: 44,
    minWidth: 120,
    maxWidth: 160,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardDisabled: {
    opacity: 0.5,
  },
  cardContent: {
    alignItems: 'center',
    gap: 8,
  },
  cardIcon: {
    fontSize: 32,
    marginBottom: 4,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    textAlign: 'center',
  },
  cardTitleDisabled: {
    color: '#9ca3af',
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  cardSubtitleDisabled: {
    color: '#9ca3af',
  },
});