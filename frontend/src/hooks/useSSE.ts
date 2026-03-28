import { useEffect, useRef, useState } from "react";

export interface SSEEvent {
  event: string;
  data: unknown;
}

export function useSSE(url: string | null) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!url) return;

    const source = new EventSource(url);
    sourceRef.current = source;

    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);

    const eventTypes = ["progress", "game_added", "game_skipped", "completed", "error"];
    for (const type of eventTypes) {
      source.addEventListener(type, (e: MessageEvent) => {
        const data: unknown = JSON.parse(e.data as string);
        setEvents((prev) => [...prev, { event: type, data }]);
      });
    }

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [url]);

  return { events, connected };
}
