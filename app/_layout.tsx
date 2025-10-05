import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import 'react-native-reanimated';

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="login" />
          <Stack.Screen name="sport" />
          <Stack.Screen name="session/preview" />
        </Stack>
        <StatusBar style="dark" backgroundColor="#f8fafc" />
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
