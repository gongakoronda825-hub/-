import React, { useState } from 'react';
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
import { CURRENCIES } from '../lib/currency';
import { validateTrip } from '../lib/validation';
import type { ScreenProps } from '../navigation/types';
import { useTrips } from '../store/TripsContext';
import { colors, radius, spacing } from '../theme';
import type { CurrencyCode } from '../types';

/** 最低2人なので、入力欄も最初から2つ出しておく。 */
const INITIAL_MEMBERS = ['', ''];

export function CreateTripScreen({ navigation }: ScreenProps<'CreateTrip'>) {
  const { createTrip } = useTrips();
  const [name, setName] = useState('');
  const [currency, setCurrency] = useState<CurrencyCode>('JPY');
  const [memberNames, setMemberNames] = useState<string[]>(INITIAL_MEMBERS);
  const [error, setError] = useState<string | null>(null);

  const setMemberAt = (index: number, value: string) => {
    setMemberNames((current) => current.map((n, i) => (i === index ? value : n)));
  };

  const removeMemberAt = (index: number) => {
    setMemberNames((current) => current.filter((_, i) => i !== index));
  };

  const handleCreate = () => {
    const message = validateTrip({ name, memberNames });
    if (message) {
      setError(message);
      return;
    }
    const trip = createTrip({ name, currency, memberNames });
    // 作成画面に戻れても意味がないので、履歴を置き換えて旅行詳細へ進む
    navigation.replace('TripDetail', { tripId: trip.id });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <ErrorText message={error} />

        <Card title="旅行名">
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="韓国旅行2026"
            placeholderTextColor={colors.subText}
          />
        </Card>

        <Card title="通貨">
          <View style={styles.currencyGrid}>
            {CURRENCIES.map((c) => {
              const selected = c.code === currency;
              return (
                <Pressable
                  key={c.code}
                  accessibilityRole="radio"
                  accessibilityState={{ selected }}
                  onPress={() => setCurrency(c.code)}
                  style={[styles.currencyChip, selected && styles.currencyChipSelected]}
                >
                  <Text style={[styles.currencyCode, selected && styles.currencyTextSelected]}>
                    {c.code}
                  </Text>
                  <Text style={[styles.currencyLabel, selected && styles.currencyTextSelected]}>
                    {c.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </Card>

        <Card title="メンバー（2人以上）">
          {memberNames.map((memberName, index) => (
            <View key={index} style={styles.memberRow}>
              <TextInput
                style={[styles.input, styles.memberInput]}
                value={memberName}
                onChangeText={(value) => setMemberAt(index, value)}
                placeholder={`メンバー${index + 1}`}
                placeholderTextColor={colors.subText}
              />
              {memberNames.length > 2 ? (
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={`メンバー${index + 1}を削除`}
                  onPress={() => removeMemberAt(index)}
                  style={styles.removeButton}
                >
                  <Text style={styles.removeButtonText}>✕</Text>
                </Pressable>
              ) : null}
            </View>
          ))}
          <PrimaryButton
            title="＋ メンバーを追加"
            variant="secondary"
            onPress={() => setMemberNames((current) => [...current, ''])}
          />
        </Card>

        <PrimaryButton title="この内容で作成" onPress={handleCreate} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: 16,
    color: colors.text,
    backgroundColor: colors.surface,
    minHeight: 48,
  },
  currencyGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  currencyChip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    minWidth: 96,
  },
  currencyChipSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  currencyCode: { fontSize: 15, fontWeight: '700', color: colors.text },
  currencyLabel: { fontSize: 12, color: colors.subText },
  currencyTextSelected: { color: colors.primaryText },
  memberRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
  memberInput: { flex: 1 },
  removeButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.sm,
  },
  removeButtonText: { fontSize: 18, color: colors.subText },
});
