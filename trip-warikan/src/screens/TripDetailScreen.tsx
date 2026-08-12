import React, { useLayoutEffect, useMemo } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card } from '../components/Card';
import { PrimaryButton } from '../components/PrimaryButton';
import { currencyInfo, formatMinor, formatSignedMinor } from '../lib/currency';
import { iconForDescription } from '../lib/icons';
import { toMinor } from '../lib/money';
import { settleTrip } from '../lib/settlement';
import type { ScreenProps } from '../navigation/types';
import { useTrips } from '../store/TripsContext';
import { colors, radius, spacing } from '../theme';
import type { Payment, Trip } from '../types';

/** 新しい支払いほど上に出す。 */
function sortedForHistory(payments: Payment[]): Payment[] {
  return payments
    .map((payment, index) => ({ payment, index }))
    .sort(
      (a, b) =>
        Date.parse(b.payment.createdAt) - Date.parse(a.payment.createdAt) || b.index - a.index
    )
    .map((entry) => entry.payment);
}

export function TripDetailScreen({ route, navigation }: ScreenProps<'TripDetail'>) {
  const { tripId } = route.params;
  const { getTrip, loading } = useTrips();
  const trip = getTrip(tripId);

  useLayoutEffect(() => {
    navigation.setOptions({ title: trip?.name ?? '旅行' });
  }, [navigation, trip?.name]);

  if (!trip) {
    return (
      <View style={styles.missing}>
        <Text style={styles.missingText}>
          {loading ? '読み込み中…' : '旅行が見つかりませんでした'}
        </Text>
      </View>
    );
  }

  return <TripDetailContent trip={trip} navigation={navigation} />;
}

function TripDetailContent({
  trip,
  navigation,
}: {
  trip: Trip;
  navigation: ScreenProps<'TripDetail'>['navigation'];
}) {
  const { balances } = useMemo(() => settleTrip(trip), [trip]);
  const history = useMemo(() => sortedForHistory(trip.payments), [trip.payments]);
  const memberName = (id: string) => trip.members.find((m) => m.id === id)?.name ?? '不明';
  const decimals = currencyInfo(trip.currency).decimals;

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.tripName}>{trip.name}</Text>
          <Text style={styles.tripCurrency}>
            {currencyInfo(trip.currency).label}（{trip.currency}）
          </Text>
        </View>

        <Card title="精算状況">
          {balances.map((balance) => (
            <View key={balance.memberId} style={styles.balanceRow}>
              <Text style={styles.balanceName}>{memberName(balance.memberId)}</Text>
              <Text
                style={[
                  styles.balanceAmount,
                  balance.amountMinor > 0 && styles.plus,
                  balance.amountMinor < 0 && styles.minus,
                ]}
              >
                {formatSignedMinor(balance.amountMinor, trip.currency)}
              </Text>
            </View>
          ))}
          <Text style={styles.balanceHint}>「＋」は受け取る側、「−」は支払う側です。</Text>
        </Card>

        <PrimaryButton
          title="精算結果を見る"
          variant="secondary"
          onPress={() => navigation.navigate('Settlement', { tripId: trip.id })}
          style={styles.settlementButton}
        />

        <Card title="支払い履歴">
          {history.length === 0 ? (
            <Text style={styles.emptyText}>まだ支払いがありません</Text>
          ) : (
            history.map((payment) => (
              <Pressable
                key={payment.id}
                accessibilityRole="button"
                onPress={() =>
                  navigation.navigate('PaymentForm', { tripId: trip.id, paymentId: payment.id })
                }
                style={({ pressed }) => [styles.paymentRow, pressed && styles.pressed]}
              >
                <Text style={styles.paymentIcon}>{iconForDescription(payment.description)}</Text>
                <View style={styles.paymentBody}>
                  <Text style={styles.paymentDescription}>{payment.description || '支払い'}</Text>
                  <Text style={styles.paymentMeta}>
                    {memberName(payment.payerId)}が立て替え・
                    {payment.participantIds.length}人で割り勘
                  </Text>
                </View>
                <Text style={styles.paymentAmount}>
                  {formatMinor(toMinor(payment.amount, decimals), trip.currency)}
                </Text>
              </Pressable>
            ))
          )}
        </Card>
      </ScrollView>

      <View style={styles.footer}>
        <PrimaryButton
          title="＋ 支払いを追加"
          onPress={() => navigation.navigate('PaymentForm', { tripId: trip.id })}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing.xl },
  missing: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  missingText: { fontSize: 16, color: colors.subText },
  header: { marginBottom: spacing.lg },
  tripName: { fontSize: 24, fontWeight: '700', color: colors.text },
  tripCurrency: { fontSize: 14, color: colors.subText, marginTop: spacing.xs },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  balanceName: { fontSize: 16, color: colors.text, flex: 1 },
  balanceAmount: { fontSize: 17, fontWeight: '700', color: colors.subText },
  plus: { color: colors.plus },
  minus: { color: colors.minus },
  balanceHint: { fontSize: 12, color: colors.subText, marginTop: spacing.sm },
  settlementButton: { marginBottom: spacing.lg },
  emptyText: { fontSize: 14, color: colors.subText },
  paymentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  pressed: { opacity: 0.6 },
  paymentIcon: { fontSize: 22, width: 34 },
  paymentBody: { flex: 1, paddingRight: spacing.sm },
  paymentDescription: { fontSize: 16, fontWeight: '600', color: colors.text },
  paymentMeta: { fontSize: 12, color: colors.subText, marginTop: 2 },
  paymentAmount: { fontSize: 16, fontWeight: '700', color: colors.text },
  footer: {
    padding: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
  },
});
