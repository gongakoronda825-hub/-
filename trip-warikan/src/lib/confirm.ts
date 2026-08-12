import { Alert, Platform } from 'react-native';

/**
 * 取り消せない操作の前に確認を取る。
 * react-native-web の Alert は何も表示しない実装なので、
 * web だけはブラウザ標準の確認ダイアログにフォールバックする。
 */
export function confirmDestructive(options: {
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => void;
}): void {
  const { title, message, confirmLabel, onConfirm } = options;

  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined' && window.confirm(`${title}\n${message}`)) {
      onConfirm();
    }
    return;
  }

  Alert.alert(title, message, [
    { text: 'キャンセル', style: 'cancel' },
    { text: confirmLabel, style: 'destructive', onPress: onConfirm },
  ]);
}
