"use client";

import { useEffect, useState } from "react";
import { api, LibraryDocument } from "@/lib/api";

interface KnowledgeLibraryModalProps {
  isOpen: boolean;
  onClose: () => void;
  region: string;
}

export function KnowledgeLibraryModal({
  isOpen,
  onClose,
  region,
}: KnowledgeLibraryModalProps) {
  const [docs, setDocs] = useState<LibraryDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setIsLoading(true);
    api
      .getLibrary(region)
      .then(setDocs)
      .catch(() => setDocs([]))
      .finally(() => setIsLoading(false));
  }, [isOpen, region]);

  if (!isOpen) return null;

  const categoryIcon: Record<string, string> = {
    Leave: "🏖️",
    "Benefits & Insurance": "❤️",
    "Workplace Policies": "📋",
    "Remote Work": "🏠",
    General: "📄",
  };

  const formatBytes = (b: number) => {
    if (b < 1024) return `${b} B`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(0)} KB`;
    return `${(b / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (!acknowledged) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-panel" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
          <div className="modal-body" style={{ padding: "32px 32px 0" }}>
            <div className="modal-hero">
              <span>📚</span>
              <span>✅</span>
              <span>✏️</span>
            </div>
            <div className="modal-hero-text">Good answers start with good sources.</div>
            <div className="modal-hero-sub">
              {docs.length === 0 && !isLoading
                ? "No HR documents have been connected. Your organization's policies will appear here once the knowledge library is set up."
                : `${docs.length} policy document${docs.length !== 1 ? "s" : ""} available for ${region}.`}
            </div>
          </div>
          <div className="modal-footer">
            <button
              className="btn-primary"
              onClick={() => setAcknowledged(true)}
              id="btn-library-got-it"
            >
              Got it ✓
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">📚 Your knowledge library</div>
            <div className="modal-subtitle">
              Organization policies and source documents · {region}
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} id="btn-close-library">
            ✕
          </button>
        </div>

        <div className="modal-body">
          {isLoading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="skeleton"
                  style={{ height: 56, borderRadius: "var(--radius-md)" }}
                />
              ))}
            </div>
          ) : docs.length === 0 ? (
            <div style={{ textAlign: "center", padding: "32px 16px" }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>📭</div>
              <div
                style={{
                  fontWeight: 700,
                  color: "var(--neutral-700)",
                  marginBottom: 6,
                }}
              >
                No documents yet
              </div>
              <div style={{ fontSize: 13, color: "var(--neutral-400)" }}>
                Ask your HR Admin to upload policy documents.
              </div>
            </div>
          ) : (
            <div className="library-document-list">
              {docs.map((doc) => (
                <div className="library-doc-item" key={doc.id}>
                  <div className="library-doc-icon">
                    {categoryIcon[doc.category] ?? "📄"}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="library-doc-title">{doc.title}</div>
                    <div className="library-doc-meta">
                      {doc.category} · v{doc.version} · {formatBytes(doc.file_size_bytes)} ·{" "}
                      {doc.file_type.toUpperCase()}
                    </div>
                  </div>
                  <div className={`library-doc-badge ${doc.status}`}>
                    {doc.status === "active" ? "✓ Active" : doc.status}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ paddingTop: 12 }}>
          <button className="btn-primary" onClick={onClose} id="btn-library-close">
            Close library
          </button>
        </div>
      </div>
    </div>
  );
}
