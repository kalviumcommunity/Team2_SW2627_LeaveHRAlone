"use client";

import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/config";

type HealthResponse = {
  status: string;
  service: string;
  environment: string;
};

export function ApiStatus() {
  const [label, setLabel] = useState("Checking API…");
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        const response = await fetch(`${apiUrl}/health`);
        if (!response.ok) {
          throw new Error("Health check failed");
        }
        const data = (await response.json()) as HealthResponse;
        if (!cancelled) {
          setOk(true);
          setLabel(`${data.service} API is running`);
        }
      } catch {
        if (!cancelled) {
          setOk(false);
          setLabel("API is not reachable. Start the FastAPI backend.");
        }
      }
    }

    void check();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <p className="flex items-center gap-2 text-sm text-zinc-600">
      <span
        className={`inline-block h-2 w-2 rounded-full ${
          ok === null ? "bg-zinc-400" : ok ? "bg-emerald-500" : "bg-amber-500"
        }`}
        aria-hidden
      />
      {label}
    </p>
  );
}
