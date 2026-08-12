import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import type { RootStackParamList } from './src/navigation/types';
import { CreateTripScreen } from './src/screens/CreateTripScreen';
import { HomeScreen } from './src/screens/HomeScreen';
import { PaymentFormScreen } from './src/screens/PaymentFormScreen';
import { SettlementScreen } from './src/screens/SettlementScreen';
import { TripDetailScreen } from './src/screens/TripDetailScreen';
import { TripsProvider } from './src/store/TripsContext';
import { colors } from './src/theme';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <SafeAreaProvider>
      <TripsProvider>
        <NavigationContainer>
          <Stack.Navigator
            screenOptions={{
              headerStyle: { backgroundColor: colors.surface },
              headerTintColor: colors.text,
              headerTitleStyle: { fontWeight: '700' },
              contentStyle: { backgroundColor: colors.background },
            }}
          >
            <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'Trip割り勘' }} />
            <Stack.Screen
              name="CreateTrip"
              component={CreateTripScreen}
              options={{ title: '新しい旅行' }}
            />
            <Stack.Screen name="TripDetail" component={TripDetailScreen} options={{ title: '旅行' }} />
            <Stack.Screen
              name="PaymentForm"
              component={PaymentFormScreen}
              options={{ title: '支払いを追加' }}
            />
            <Stack.Screen
              name="Settlement"
              component={SettlementScreen}
              options={{ title: '精算結果' }}
            />
          </Stack.Navigator>
        </NavigationContainer>
        <StatusBar style="dark" />
      </TripsProvider>
    </SafeAreaProvider>
  );
}
