import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { createId } from '../lib/id';
import { loadTrips, saveTrips } from '../storage/tripStorage';
import type { CurrencyCode, Payment, Trip } from '../types';

export type NewPayment = Omit<Payment, 'id' | 'createdAt'>;

type TripsContextValue = {
  trips: Trip[];
  /** 初回読み込み中かどうか */
  loading: boolean;
  getTrip: (tripId: string) => Trip | undefined;
  createTrip: (input: { name: string; currency: CurrencyCode; memberNames: string[] }) => Trip;
  addPayment: (tripId: string, payment: NewPayment) => void;
  updatePayment: (tripId: string, paymentId: string, payment: NewPayment) => void;
  deletePayment: (tripId: string, paymentId: string) => void;
};

const TripsContext = createContext<TripsContextValue | null>(null);

export function TripsProvider({ children }: { children: React.ReactNode }) {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    loadTrips()
      .then((stored) => {
        if (!cancelled) setTrips(stored);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  /** 状態更新と永続化を必ずセットで行う入口。 */
  const commit = useCallback((update: (current: Trip[]) => Trip[]) => {
    setTrips((current) => {
      const next = update(current);
      void saveTrips(next);
      return next;
    });
  }, []);

  const updateTrip = useCallback(
    (tripId: string, update: (trip: Trip) => Trip) => {
      commit((current) => current.map((t) => (t.id === tripId ? update(t) : t)));
    },
    [commit]
  );

  const createTrip = useCallback<TripsContextValue['createTrip']>(
    ({ name, currency, memberNames }) => {
      const trip: Trip = {
        id: createId('trip'),
        name: name.trim(),
        currency,
        members: memberNames
          .map((n) => n.trim())
          .filter((n) => n !== '')
          .map((n) => ({ id: createId('member'), name: n })),
        payments: [],
        createdAt: new Date().toISOString(),
      };
      commit((current) => [trip, ...current]);
      return trip;
    },
    [commit]
  );

  const addPayment = useCallback<TripsContextValue['addPayment']>(
    (tripId, payment) => {
      const newPayment: Payment = {
        ...payment,
        id: createId('payment'),
        createdAt: new Date().toISOString(),
      };
      updateTrip(tripId, (trip) => ({ ...trip, payments: [...trip.payments, newPayment] }));
    },
    [updateTrip]
  );

  const updatePayment = useCallback<TripsContextValue['updatePayment']>(
    (tripId, paymentId, payment) => {
      updateTrip(tripId, (trip) => ({
        ...trip,
        payments: trip.payments.map((p) => (p.id === paymentId ? { ...p, ...payment } : p)),
      }));
    },
    [updateTrip]
  );

  const deletePayment = useCallback<TripsContextValue['deletePayment']>(
    (tripId, paymentId) => {
      updateTrip(tripId, (trip) => ({
        ...trip,
        payments: trip.payments.filter((p) => p.id !== paymentId),
      }));
    },
    [updateTrip]
  );

  const value = useMemo<TripsContextValue>(
    () => ({
      trips,
      loading,
      getTrip: (tripId) => trips.find((t) => t.id === tripId),
      createTrip,
      addPayment,
      updatePayment,
      deletePayment,
    }),
    [trips, loading, createTrip, addPayment, updatePayment, deletePayment]
  );

  return <TripsContext.Provider value={value}>{children}</TripsContext.Provider>;
}

export function useTrips(): TripsContextValue {
  const value = useContext(TripsContext);
  if (!value) {
    throw new Error('useTrips は TripsProvider の中で使ってください');
  }
  return value;
}
