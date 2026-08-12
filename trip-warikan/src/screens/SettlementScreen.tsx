import React, { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card } from '../components/Card';
import { formatMinor } from '../lib/currency';
import { settleTrip } from '../lib/settlement';
import type { ScreenProps } from '../navigation/types';
import { useTrips } from '../store/TripsContext';
import { colors, spacing } from '../theme';

export function SettlementScreen({ route }: ScreenProps<'Settlement'>) {
  const { tripId } = route.params;
  const { getTrip } = useTrips();
  const trip = getTrip(tripId);

  const settlement = useMemo(() => (trip ? settleTrip(trip) : null), [trip]);

  if (!trip || !settlement) {
    return (
      <View style={styles.missing}>
        <Text style={styles.missingText}>旅行が見つかりませんでした</Text>
      </View>
    );
  }

  const memberName = (id: string) => trip.members.find((m) => m.id === id)?.name ?? '不明';
  const { transfers, balances } = settlement;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Card title="支払い">
        {transfers.length === 0 ? (
          <Text style={styles.settled}>精算は完了しています</Text>
        ) : (
          transfers.map((transfer, index) => (
            <View key={`${transfer.fromId}-${transfer.toId}-${index}`} style={styles.transferRow}>
              <Text style={styles.transferPeople}>
                {memberName(transfer.fromId)} → {memberName(transfer.toId)}
              </Text>
              <Text style={styles.transferAmount}>
                {formatMinor(transfer.amountMinor, trip.currency)}
              </Text>
            </View>
          ))
        )}
      </Card>

      <Card title="精算完了まで">
        {balances.map((balance) => (
          <View key={balance.memberId} style={styles.balanceRow}>
            <Text style={styles.balanceName}>{memberName(balance.memberId)}</Text>
            <Text
              style={[
                styles.balanceText,
                balance.amountMinor > 0 && styles.plus,
                balance.amountMinor < 0 && styles.minus,
              ]}
            >
              {balance.amountMinor === 0
                ? '精算不要'
                : `${formatMinor(Math.abs(balance.amountMinor), trip.currency)}${
                    balance.amountMinor > 0 ? '受け取る' : '支払う'
                  }`}
            </Text>
          </View>
        ))}
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing.xl },
  missing: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  missingText: { fontSize: 16, color: colors.subText },
  settled: { fontSize: 15, color: colors.subText },
  transferRow: {
    paddingVertical: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  transferPeople: { fontSize: 16, fontWeight: '600', color: colors.text },
  transferAmount: { fontSize: 22, fontWeight: '700', color: colors.text, marginTop: spacing.xs },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  balanceName: { fontSize: 16, color: colors.text },
  balanceText: { fontSize: 16, fontWeight: '700', color: colors.subText },
  plus: { color: colors.plus },
  minus: { color: colors.minus },
});
