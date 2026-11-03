"use client";

import { useState } from "react";
import { api, ChatSource } from "@/lib/api";

interface MessageBubbleProps {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence?: string;
  sources?: ChatSource[];
  requiresHr?: boolean;
  isLoading?: boolean;
  conversationId?: string | null;
  onSelectSource?: (src: ChatSource) => void;
}

function ConfidenceBadge({ confidence }: { confidence: string }) {
  const labels: Record<string, string> = {
    high: "✓ High confidence",
    medium: "~ Medium confidence",
    low: "! Low confidence",
    none: "• Unknown",
  };
  return (
    <span className={`confidence-badge ${confidence}`}>
      {labels[confidence] ?? confidence}
    </span>
  );
}

function formatInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /(\*{1,2})(.*?)\1/g;
  let lastIndex = 0;
  let match;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    const delim = match[1];
    const inner = match[2];
    if (delim === '**') {
      parts.push(<strong key={match.index}>{inner}</strong>);
    } else {
      parts.push(<em key={match.index}>{inner}</em>);
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }
  return parts.length > 0 ? parts : [text];
}

function renderFormattedMessage(content: string) {
  const lines = content.split("\n");
  const blocks: Array<{ type: "paragraph" | "quote"; lines: string[] }> = [];
  let currentBlock: { type: "paragraph" | "quote"; lines: string[] } | null = null;
  for (const line of lines) {
    const trimmed = line.trim();
    const isQuote = trimmed.startsWith(">");
    const cleanedLine = isQuote ? trimmed.replace(/^>\s?/, "") : line;
    if (!currentBlock) {
      currentBlock = { type: isQuote ? "quote" : "paragraph", lines: [cleanedLine] };
    } else if ((isQuote && currentBlock.type === "quote") || (!isQuote && currentBlock.type === "paragraph")) {
      currentBlock.lines.push(cleanedLine);
    } else {
      blocks.push(currentBlock);
      currentBlock = { type: isQuote ? "quote" : "paragraph", lines: [cleanedLine] };
    }
  }
  if (currentBlock) blocks.push(currentBlock);
  return blocks.map((block, idx) => {
    if (block.type === "quote") {
      return (
        <div
          key={idx}
          className="policy-excerpt-highlight"
          style={{
            margin: "12px 0",
            padding: "12px 16px",
            backgroundColor: "#FFFBEB",
            borderLeft: "4px solid #F5C518",
            borderRadius: "0 8px 8px 0",
            borderTop: "1px solid #FEF3C7",
            borderRight: "1px solid #FEF3C7",
            borderBottom: "1px solid #FEF3C7",
            fontSize: "13.5px",
            lineHeight: "1.6",
            color: "#292524",
          }}
        >
          {block.lines.map((l, li) => (
            <div key={li} style={{ marginBottom: li < block.lines.length - 1 ? 4 : 0 }}>
              {formatInline(l)}
            </div>
          ))}
        </div>
      );
    }
    return (
      <div key={idx} className="message-answer-section">
        {block.lines.map((l, li) => (
          <p key={li} style={{ marginBottom: 6 }}>
            {formatInline(l) || "\u00A0"}
          </p>
        ))}
      </div>
    );
  });
}

export function MessageBubble({
  id,
  role,
  content,
  confidence,
  sources = [],
  requiresHr = false,
  isLoading = false,
  conversationId,
  onSelectSource,
}: MessageBubbleProps) {
  const [feedbackSent, setFeedbackSent] = useState<"positive" | "negative" | null>(null);
  const [showNegativeModal, setShowNegativeModal] = useState(false);
  const [selectedReason, setSelectedReason] = useState("Incorrect information");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [ticketStatus, setTicketStatus] = useState<"idle" | "creating" | "created" | "error">("idle");
  const [copied, setCopied] = useState(false);

  if (role === "user") {
    return (
      <div className="message-user">
        <div className="message-user-bubble">{content}</div>
      </div>
    );
  }

  const handlePositiveFeedback = async () => {
    try {
      await api.submitFeedback({
        message_id: id,
        rating: true,
      });
      setFeedbackSent("positive");
    } catch {
      // Optimistic set
      setFeedbackSent("positive");
    }
  };

  const handleNegativeFeedbackSubmit = async () => {
    try {
      await api.submitFeedback({
        message_id: id,
        rating: false,
        reason: selectedReason,
        comment: feedbackComment,
      });
      setFeedbackSent("negative");
      setShowNegativeModal(false);
    } catch {
      setFeedbackSent("negative");
      setShowNegativeModal(false);
    }
  };

  const handleEscalateToHr = async () => {
    setTicketStatus("creating");
    try {
      await api.createTicket({
        question: content.slice(0, 150),
        conversation_id: conversationId || undefined,
        confidence: confidence || "low",
        priority: "medium",
        retrieved_sources: sources,
      });
      setTicketStatus("created");
    } catch {
      setTicketStatus("error");
    }
  };

  const handleCopy = () => {
    navigator.clipboard?.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="message-assistant">
      {/* Bot Avatar */}
      <div className="message-bot-avatar-sm">🤖</div>

      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Header */}
        <div className="message-bot-meta">
          <span className="message-bot-name">leavehralone</span>
          <span className="message-bot-label">HR assistant</span>
          {confidence && !isLoading && (
            <ConfidenceBadge confidence={confidence} />
          )}
        </div>

        {/* Content or Typing Animation */}
        {isLoading ? (
          <div className="typing-dots">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        ) : (
          <div className="message-bot-content">
            {renderFormattedMessage(content)}
          </div>
        )}

        {/* Escalation Alert & Action Button */}
        {(requiresHr || confidence === "low") && !isLoading && (
          <div className="hr-alert">
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ fontSize: 18 }}>⚠️</span>
              <div>
                <div style={{ fontWeight: 600 }}>Need verified HR clarification?</div>
                <div style={{ fontSize: 12, opacity: 0.85 }}>
                  This policy query has lower retrieval certainty. You can escalate it directly to the HR team.
                </div>
              </div>
            </div>
            {ticketStatus === "created" ? (
              <span className="ticket-badge success">✓ HR Ticket Created</span>
            ) : (
              <button
                className="ask-hr-btn"
                onClick={handleEscalateToHr}
                disabled={ticketStatus === "creating"}
                id={`btn-ask-hr-${id}`}
              >
                {ticketStatus === "creating" ? "Creating ticket..." : "Ask HR ↗"}
              </button>
            )}
          </div>
        )}

        {/* Sources with Clickable Chips */}
        {!isLoading && (
          <div className="sources-section">
            <div className="sources-header">
              <span>📎</span>
              <span>
                {sources.length > 0
                  ? `${sources.length} Policy Source${sources.length !== 1 ? "s" : ""} (Click to inspect)`
                  : "No policy sources connected"}
              </span>
            </div>
            {sources.length > 0 ? (
              <div className="sources-chips-container">
                {sources.map((src, i) => (
                  <button
                    className="source-chip clickable"
                    key={i}
                    onClick={() => onSelectSource && onSelectSource(src)}
                    id={`source-chip-${id}-${i}`}
                    type="button"
                    title="Click to view full chunk excerpt in drawer"
                  >
                    <div className="source-icon">📄</div>
                    <div style={{ textAlign: "left" }}>
                      <div className="source-text">{src.document_title}</div>
                      <div style={{ fontSize: 10.5, color: "var(--neutral-400)" }}>
                        {src.section} · p.{src.page_number} · v{src.version}
                      </div>
                    </div>
                    <div className="source-meta">
                      {Math.round(src.similarity_score * 100)}% match ↗
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="no-sources">
                <span>📭</span>
                <span>No policy sources connected for this region</span>
              </div>
            )}
          </div>
        )}

        {/* Message Actions & Feedback */}
        {!isLoading && (
          <div className="message-actions">
            <button
              className="message-action-btn"
              onClick={handleCopy}
              id={`btn-copy-${id}`}
            >
              {copied ? "✓ Copied!" : "📋 Copy"}
            </button>

            {feedbackSent === "positive" ? (
              <span className="feedback-done">✓ Helpful</span>
            ) : feedbackSent === "negative" ? (
              <span className="feedback-done">✓ Feedback noted</span>
            ) : (
              <>
                <button
                  className="message-action-btn"
                  onClick={handlePositiveFeedback}
                  id={`btn-helpful-${id}`}
                >
                  👍 Helpful
                </button>
                <button
                  className="message-action-btn"
                  onClick={() => setShowNegativeModal(true)}
                  id={`btn-not-helpful-${id}`}
                >
                  👎 Not helpful
                </button>
              </>
            )}
          </div>
        )}

        {/* Negative Feedback Modal / Dropdown */}
        {showNegativeModal && (
          <div className="feedback-reason-box">
            <div className="feedback-reason-title">Help us improve leavehralone</div>
            <select
              value={selectedReason}
              onChange={(e) => setSelectedReason(e.target.value)}
              className="feedback-select"
            >
              <option value="Incorrect information">Incorrect information</option>
              <option value="Outdated policy">Outdated policy version</option>
              <option value="Not relevant">Not relevant to my question</option>
              <option value="Missing information">Missing critical details</option>
              <option value="Other">Other</option>
            </select>
            <input
              type="text"
              placeholder="Optional comment..."
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
              className="feedback-comment-input"
            />
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <button
                className="feedback-submit-btn"
                onClick={handleNegativeFeedbackSubmit}
              >
                Submit Feedback
              </button>
              <button
                className="feedback-cancel-btn"
                onClick={() => setShowNegativeModal(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}