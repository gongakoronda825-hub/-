import React, { useLayoutEffect, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { Card } from '../components/Card';
import { ErrorText } from '../components/ErrorText';
import { PrimaryButton } from '../components/PrimaryButton';
import { confirmDestructive } from '../lib/confirm';
import { currencyInfo } from '../lib/currency';
import { parseAmount, validatePayment } from '../lib/validation';
import type { ScreenProps } from '../navigation/types';
import { useTrips } from '../store/TripsContext';
import { colors, radius, spacing } from '../theme';
import type { Trip } from '../types';

export function PaymentFormScreen({ route, navigation }: ScreenProps<'PaymentForm'>) {
  const { tripId, paymentId } = route.params;
  const { getTrip } = useTrips();
  const trip = getTrip(tripId);

  useLayoutEffect(() => {
    navigation.setOptions({ title: paymentId ? '支払いの詳細' : '支払いを追加' });
  }, [navigation, paymentId]);

  if (!trip) {
    return (
      <View style={styles.missing}>
        <Text style={styles.missingText}>旅行が見つかりませんでした</Text>
      </View>
    );
  }

  return <PaymentForm trip={trip} paymentId={paymentId} navigation={navigation} />;
}

function PaymentForm({
  trip,
  paymentId,
  navigation,
}: {
  trip: Trip;
  paymentId?: string;
  navigation: ScreenProps<'PaymentForm'>['navigation'];
}) {
  const { addPayment, updatePayment, deletePayment } = useTrips();
  const existing = paymentId ? trip.payments.find((p) => p.id === paymentId) : undefined;
  const { decimals } = currencyInfo(trip.currency);

  const [payerId, setPayerId] = useState<string | null>(existing?.payerId ?? null);
  const [amountText, setAmountText] = useState(
    existing ? String(existing.amount) : ''
  );
  const [description, setDescription] = useState(existing?.description ?? '');
  // 新規登録では全員が対象。これが最も多いケースなので初期値にする。
  const [participantIds, setParticipantIds] = useState<string[]>(
    existing?.participantIds ?? trip.members.map((m) => m.id)
  );
  const [error, setError] = useState<string | null>(null);

  const toggleParticipant = (memberId: string) => {
    setParticipantIds((current) =>
      current.includes(memberId)
        ? current.filter((id) => id !== memberId)
        : // メンバーの並び順を保って追加する（端数の配分順を安定させるため）
          trip.members.map((m) => m.id).filter((id) => current.includes(id) || id === memberId)
    );
  };

  const allSelected = participantIds.length === trip.members.length;

  const handleSave = () => {
    const message = validatePayment({ payerId, amountText, participantIds });
    if (message) {
      setError(message);
      return;
    }
    const amount = parseAmount(amountText) as number;
    const payload = {
      payerId: payerId as string,
      // 通貨の最小単位より細かい入力は丸めて保存する
      amount: Math.round(amount * 10 ** decimals) / 10 ** decimals,
      description: description.trim(),
      participantIds,
    };

    if (existing) {
      updatePayment(trip.id, existing.id, payload);
    } else {
      addPayment(trip.id, payload);
    }
    navigation.goBack();
  };

  const handleDelete = () => {
    if (!existing) return;
    confirmDestructive({
      title: 'この支払いを削除しますか？',
      message: '削除すると元に戻せません。',
      confirmLabel: '削除',
      onConfirm: () => {
        deletePayment(trip.id, existing.id);
        navigation.goBack();
      },
    });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <ErrorText message={error} />

        <Card title="支払った人">
          <View style={styles.chipRow}>
            {trip.members.map((member) => {
              const selected = member.id === payerId;
              return (
                <Pressable
                  key={member.id}
                  accessibilityRole="radio"
                  accessibilityState={{ selected }}
                  onPress={() => setPayerId(member.id)}
                  style={[styles.chip, selected && styles.chipSelected]}
                >
                  <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
                    {member.name}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </Card>

        <Card title={`金額（${trip.currency}）`}>
          <TextInput
            style={styles.amountInput}
            value={amountText}
            onChangeText={setAmountText}
            // 旅行中に素早く打てるよう数字キーボードを出す
            keyboardType={decimals > 0 ? 'decimal-pad' : 'number-pad'}
            placeholder="0"
            placeholderTextColor={colors.subText}
          />
        </Card>

        <Card title="内容">
          <TextInput
            style={styles.input}
            value={description}
            onChangeText={setDescription}
            placeholder="タクシー / レストラン / ホテル など"
            placeholderTextColor={colors.subText}
          />
        </Card>

        <Card title="支払い対象者">
          <Pressable
            accessibilityRole="button"
            onPress={() =>
              setParticipantIds(allSelected ? [] : trip.members.map((m) => m.id))
            }
            style={styles.selectAll}
          >
            <Text style={styles.selectAllText}>
              {allSelected ? 'すべて外す' : '全員を選ぶ'}
            </Text>
          </Pressable>
          {trip.members.map((member) => {
            const checked = participantIds.includes(member.id);
            return (
              <Pressable
                key={member.id}
                accessibilityRole="checkbox"
                accessibilityState={{ checked }}
                onPress={() => toggleParticipant(member.id)}
                style={styles.checkRow}
              >
                <Text style={styles.checkBox}>{checked ? '☑' : '☐'}</Text>
                <Text style={styles.checkLabel}>{member.name}</Text>
              </Pressable>
            );
          })}
        </Card>

        <PrimaryButton title="保存" onPress={handleSave} />
        {existing ? (
          <PrimaryButton
            title="削除"
            variant="danger"
            onPress={handleDelete}
            style={styles.deleteButton}
          />
        ) : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  missing: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  missingText: { fontSize: 16, color: colors.subText },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    minHeight: 48,
    justifyContent: 'center',
  },
  chipSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { fontSize: 16, color: colors.text },
  chipTextSelected: { color: colors.primaryText, fontWeight: '700' },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: 16,
    color: colors.text,
    minHeight: 48,
  },
  amountInput: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: 28,
    fontWeight: '700',
    color: colors.text,
    textAlign: 'right',
    minHeight: 60,
  },
  selectAll: { alignSelf: 'flex-start', paddingVertical: spacing.sm, marginBottom: spacing.xs },
  selectAllText: { fontSize: 14, fontWeight: '700', color: colors.primary },
  checkRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md },
  checkBox: { fontSize: 22, width: 32, color: colors.text },
  checkLabel: { fontSize: 16, color: colors.text },
  deleteButton: { marginTop: spacing.md },
});
