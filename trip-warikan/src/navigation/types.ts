import type { NativeStackScreenProps } from '@react-navigation/native-stack';

export type RootStackParamList = {
  Home: undefined;
  CreateTrip: undefined;
  TripDetail: { tripId: string };
  /** paymentId があれば編集、なければ新規登録 */
  PaymentForm: { tripId: string; paymentId?: string };
  Settlement: { tripId: string };
};

export type ScreenProps<T extends keyof RootStackParamList> = NativeStackScreenProps<
  RootStackParamList,
  T
>;
