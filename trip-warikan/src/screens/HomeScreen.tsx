import React from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';

import { PrimaryButton } from '../components/PrimaryButton';
import { currencyInfo } from '../lib/currency';
import type { ScreenProps } from '../navigation/types';
import { useTrips } from '../store/TripsContext';
import { colors, radius, spacing } from '../theme';
import type { Trip } from '../types';

export function HomeScreen({ navigation }: ScreenProps<'Home'>) {
  const { trips, loading } = useTrips();

  const renderTrip = ({ item }: { item: Trip }) => (
    <Pressable
      accessibilityRole="button"
      onPress={() => navigation.navigate('TripDetail', { tripId: item.id })}
      style={({ pressed }) => [styles.tripRow, pressed && styles.pressed]}
    >
      <Text style={styles.tripName}>{item.name}</Text>
      <Text style={styles.tripMeta}>
        {currencyInfo(item.currency).label}（{item.currency}）・{item.members.length}人・支払い
        {item.payments.length}件
      </Text>
    </Pressable>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={trips}
        keyExtractor={(trip) => trip.id}
        renderItem={renderTrip}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          loading ? null : (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>旅行を作成してください</Text>
            </View>
          )
        }
      />
      <View style={styles.footer}>
        <PrimaryButton title="＋ 新しい旅行" onPress={() => navigation.navigate('CreateTrip')} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  listContent: { padding: spacing.lg, paddingBottom: spacing.lg },
  tripRow: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  pressed: { opacity: 0.75 },
  tripName: { fontSize: 18, fontWeight: '700', color: colors.text },
  tripMeta: { fontSize: 13, color: colors.subText, marginTop: spacing.xs },
  empty: { paddingVertical: spacing.xl * 2, alignItems: 'center' },
  emptyText: { fontSize: 16, color: colors.subText },
  footer: {
    padding: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
  },
});
