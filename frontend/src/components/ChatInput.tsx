"use client";

import { useRef, useState, useEffect } from "react";

interface ChatInputProps {
  onSend: (query: string) => void;
  isLoading: boolean;
  region: string;
  onRegionChange: (r: string) => void;
  placeholder?: string;
}

const REGIONS = ["India", "US", "UK", "Singapore", "Germany", "Australia", "Global"];

export function ChatInput({
  onSend,
  isLoading,
  region,
  onRegionChange,
  placeholder = "Ask leavehralone anything about your work life...",
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [value]);

  const handleSend = () => {
    const q = value.trim();
    if (!q || isLoading) return;
    onSend(q);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-container">
      <div className="chat-input-wrapper">
        <div className="chat-input-area">
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            placeholder={placeholder}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isLoading}
            id="chat-textarea-input"
          />
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!value.trim() || isLoading}
            id="btn-send-message"
            title="Send message (Enter)"
          >
            {isLoading ? (
              <div className="spinner" />
            ) : (
              <span>↑</span>
            )}
          </button>
        </div>
        <div className="chat-input-footer">
          <div className="chat-region-indicator">
            <span>📍</span>
            <span>Your region:</span>
            <select
              value={region}
              onChange={(e) => onRegionChange(e.target.value)}
              style={{
                background: "transparent",
                border: "none",
                outline: "none",
                fontSize: "11.5px",
                fontWeight: 600,
                color: "var(--brand-yellow-dark)",
                cursor: "pointer",
                fontFamily: "inherit",
              }}
              id="select-region"
            >
              {REGIONS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
      <div className="chat-footer-text" style={{ marginTop: 8, fontSize: 11, color: "var(--neutral-400)" }}>
        leavehralone · Answers are grounded in your company&apos;s active HR policies
      </div>
    </div>
  );
}
