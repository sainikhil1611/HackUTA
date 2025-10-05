import { router } from 'expo-router';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function HomeScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo row */}
        <View style={styles.logoContainer}>
          <Text style={styles.logo}>🏀</Text>
        </View>

        {/* Title */}
        <Text style={styles.title}>CoachVision</Text>

        {/* Subtitle */}
        <Text style={styles.subtitle}>
          Perfect your skills with AI-powered analysis.
        </Text>

        {/* Primary CTA Button */}
        <TouchableOpacity 
          style={styles.primaryButton}
          onPress={() => router.push('/sport')}
          activeOpacity={0.8}
        >
          <Text style={styles.primaryButtonText}>Log in with OAuth</Text>
        </TouchableOpacity>

        {/* Secondary links row */}
        <View style={styles.secondaryLinksContainer}>
          <TouchableOpacity 
            onPress={() => router.push('/sport')}
            style={styles.linkButton}
            activeOpacity={0.7}
          >
            <Text style={styles.linkText}>Skip to Sport</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            onPress={() => router.push('/session/preview')}
            style={styles.linkButton}
            activeOpacity={0.7}
          >
            <Text style={styles.linkText}>See Sample Session</Text>
          </TouchableOpacity>
        </View>
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
    paddingHorizontal: 24,
  },
  logoContainer: {
    marginBottom: 32,
  },
  logo: {
    fontSize: 48,
    textAlign: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1f2937',
    textAlign: 'center',
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 48,
    maxWidth: 320,
  },
  primaryButton: {
    backgroundColor: '#2563eb',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 8,
    minHeight: 44,
    minWidth: 200,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 32,
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
  },
  secondaryLinksContainer: {
    flexDirection: 'row',
    gap: 24,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  linkButton: {
    minHeight: 44,
    paddingHorizontal: 16,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  linkText: {
    color: '#2563eb',
    fontSize: 16,
    fontWeight: '500',
  },
});