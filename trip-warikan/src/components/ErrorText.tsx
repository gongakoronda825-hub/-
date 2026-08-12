import React from 'react';
import { StyleSheet, Text } from 'react-native';

import { colors, radius, spacing } from '../theme';

export function ErrorText({ message }: { message: string | null }) {
  if (!message) return null;
  return <Text style={styles.text}>{message}</Text>;
}

const styles = StyleSheet.create({
  text: {
    backgroundColor: colors.errorBackground,
    color: colors.danger,
    borderRadius: radius.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: spacing.md,
  },
});
