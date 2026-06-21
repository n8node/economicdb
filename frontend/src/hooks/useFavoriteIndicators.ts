"use client";

import { useCallback, useEffect, useState } from "react";
import {
  FAVORITES_KEY,
  fetchFavoriteIndicators,
  loadIds,
  type IndicatorListItem,
} from "@/lib/indicators";

export function useFavoriteIndicators() {
  const [items, setItems] = useState<IndicatorListItem[]>([]);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    const ids = loadIds(FAVORITES_KEY);
    if (!ids.length) {
      setItems([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      setItems(await fetchFavoriteIndicators());
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();

    const onStorage = (event: StorageEvent) => {
      if (event.key === FAVORITES_KEY) void reload();
    };
    const onChanged = () => void reload();

    window.addEventListener("storage", onStorage);
    window.addEventListener("macro_favorites_changed", onChanged);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("macro_favorites_changed", onChanged);
    };
  }, [reload]);

  return { items, loading, reload };
}
