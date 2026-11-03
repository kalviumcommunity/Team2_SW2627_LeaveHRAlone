"use client";

import { useEffect } from "react";
import { ChatSource } from "@/lib/api";

interface SourcePreviewDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  source: (ChatSource & { chunk_text?: string }) | null;
}

export function SourcePreviewDrawer({
  isOpen,
  onClose,
  source,
}: SourcePreviewDrawerProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !source) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div
        className="drawer-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Source Document Preview"
      >
        {/* Drawer Header */}
        <div className="drawer-header">
          <div>
            <div className="drawer-eyebrow">POLICY CITATION PREVIEW</div>
            <h2 className="drawer-title">{source.document_title}</h2>
          </div>
          <button
            className="drawer-close-btn"
            onClick={onClose}
            aria-label="Close source preview"
            id="btn-close-source-drawer"
          >
            ✕
          </button>
        </div>

        {/* Metadata Badges */}
        <div className="drawer-badges">
          <span className="drawer-badge region">🌐 {source.region}</span>
          <span className="drawer-badge section">📑 Section: {source.section}</span>
          <span className="drawer-badge page">📄 Page {source.page_number}</span>
          <span className="drawer-badge version">🏷️ Version {source.version}</span>
          <span className="drawer-badge score">
            🎯 {Math.round(source.similarity_score * 100)}% Match
          </span>
        </div>

        {/* Body & Chunk Highlight */}
        <div className="drawer-body">
          <div className="drawer-section-label">Cited Policy Text</div>
          <div className="drawer-chunk-highlight">
            <p>
              {source.chunk_text ||
                `Section ${source.section} details the company guidelines for ${source.category} under the ${source.document_title} for the ${source.region} region. Please refer to this policy for official leave, insurance coverage, and compliance criteria.`}
            </p>
          </div>

          <div className="drawer-note">
            <span style={{ fontSize: 16 }}>🛡️</span>
            <span>
              All leavehralone answers are strictly grounded in active, approved HR documentation for your geographical jurisdiction.
            </span>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="drawer-footer">
          <button
            className="drawer-action-btn"
            onClick={() => {
              if (source.chunk_text) {
                navigator.clipboard?.writeText(source.chunk_text);
              }
            }}
          >
            📋 Copy Excerpt
          </button>
          <button className="drawer-action-btn primary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
