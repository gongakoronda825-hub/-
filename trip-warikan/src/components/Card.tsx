import React from 'react';
import { StyleSheet, Text, View, ViewStyle } from 'react-native';

import { colors, radius, spacing } from '../theme';

type Props = {
  title?: string;
  children: React.ReactNode;
  style?: ViewStyle;
};

export function Card({ title, children, style }: Props) {
  return (
    <View style={[styles.card, style]}>
      {title ? <Text style={styles.title}>{title}</Text> : null}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  title: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.subText,
    marginBottom: spacing.md,
  },
});
