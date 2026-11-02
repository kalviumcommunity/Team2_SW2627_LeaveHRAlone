"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface MyTicketsModalProps {
  onClose: () => void;
}

export function MyTicketsModal({ onClose }: MyTicketsModalProps) {
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTickets() {
      try {
        const res = await api.getMyTickets();
        setTickets(res);
      } catch (err) {
        console.error("Failed to load employee tickets", err);
      } finally {
        setLoading(false);
      }
    }
    fetchTickets();
  }, []);

  return (
    <div className="admin-overlay" onClick={onClose}>
      <div
        className="admin-container"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 650, padding: 24, maxHeight: "85vh", overflowY: "auto" }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 800 }}>My Escalated HR Inquiries</h2>
            <p style={{ fontSize: 12, color: "var(--neutral-500)" }}>
              Direct questions sent to your HR Administrator when policy answers needed official clarification.
            </p>
          </div>
          <button className="admin-close-btn" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div style={{ padding: 32, textAlign: "center", color: "var(--neutral-400)" }}>
            Loading your inquiries...
          </div>
        ) : tickets.length === 0 ? (
          <div style={{ padding: 32, textAlign: "center", color: "var(--neutral-400)" }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>📋</div>
            <div style={{ fontWeight: 600 }}>No escalated tickets found.</div>
            <div style={{ fontSize: 12, marginTop: 4 }}>
              When a query requires HR review, click &quot;Ask HR ↗&quot; in the chat to escalate.
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {tickets.map((t) => (
              <div
                key={t.id}
                style={{
                  border: "1.5px solid var(--neutral-200)",
                  borderRadius: 10,
                  padding: 16,
                  background: "white",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 800,
                      padding: "2px 8px",
                      borderRadius: 4,
                      background: t.status === "resolved" ? "#dcfce7" : "#fef3c7",
                      color: t.status === "resolved" ? "#166534" : "#92400e",
                      textTransform: "uppercase",
                    }}
                  >
                    {t.status === "resolved" ? "✓ Resolved by HR" : "⏳ Pending Review"}
                  </span>
                  <span style={{ fontSize: 11, color: "var(--neutral-400)" }}>
                    {new Date(t.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--neutral-900)", marginBottom: 8 }}>
                  {t.question}
                </div>

                {t.resolution_notes ? (
                  <div
                    style={{
                      marginTop: 10,
                      background: "#f0fdf4",
                      borderLeft: "4px solid #16a34a",
                      padding: "10px 12px",
                      borderRadius: "0 6px 6px 0",
                    }}
                  >
                    <div style={{ fontSize: 11, fontWeight: 700, color: "#166534", marginBottom: 2 }}>
                      HR Administrator Official Response:
                    </div>
                    <div style={{ fontSize: 13, color: "#14532d", lineHeight: 1.5 }}>
                      {t.resolution_notes}
                    </div>
                  </div>
                ) : (
                  <div style={{ fontSize: 12, color: "var(--neutral-400)", fontStyle: "italic", marginTop: 6 }}>
                    An HR representative has been notified and will provide guidance shortly.
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
