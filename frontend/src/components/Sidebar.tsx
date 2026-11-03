"use client";

import { useAuth } from "@/lib/auth-context";
import { ConversationSummary } from "@/lib/api";

interface SidebarProps {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  onOpenLibrary: () => void;
  onOpenAdmin?: () => void;
  onOpenMyTickets?: () => void;
  onGoHome: () => void;
  currentView: "home" | "chat";
}

export function Sidebar({
  conversations,
  activeConversationId,
  onNewConversation,
  onSelectConversation,
  onOpenLibrary,
  onOpenAdmin,
  onOpenMyTickets,
  onGoHome,
  currentView,
}: SidebarProps) {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "HR_ADMIN" || user?.role === "SUPER_ADMIN";

  const initials = user
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : "?";

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-mark">🤖</div>
        <div className="logo-name">
          leave<span>hralone</span>
        </div>
        <div className="logo-tagline">Your people. Your answers.</div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {/* New conversation */}
        <button className="nav-btn primary" onClick={onNewConversation} id="btn-new-conversation">
          <span>+</span>
          <span>New conversation</span>
        </button>

        {/* Ask leavehralone */}
        <button
          className={`nav-btn ${currentView === "chat" && !activeConversationId ? "active" : ""}`}
          onClick={onGoHome}
          id="btn-ask-leavehralone"
        >
          <span>💬</span>
          <span>Ask leavehralone</span>
        </button>

        {/* Knowledge Library */}
        <button className="nav-btn" onClick={onOpenLibrary} id="btn-knowledge-library">
          <span>📚</span>
          <span>Knowledge library</span>
          <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--neutral-400)" }}>↗</span>
        </button>

        {/* My HR Tickets */}
        {onOpenMyTickets && (
          <button className="nav-btn" onClick={onOpenMyTickets} id="btn-my-tickets">
            <span>🎫</span>
            <span>My HR Tickets</span>
            <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--neutral-400)" }}>↗</span>
          </button>
        )}

        {/* HR Admin Command Center */}
        {isAdmin && onOpenAdmin && (
          <button
            className="nav-btn admin-highlight"
            onClick={onOpenAdmin}
            id="btn-admin-command-center"
            style={{
              background: "var(--color-primary-light, #fef9c3)",
              border: "1.5px solid var(--color-primary-dark, #ca8a04)",
              fontWeight: 600,
            }}
          >
            <span>⚡</span>
            <span>HR Command Center</span>
            <span style={{ marginLeft: "auto", fontSize: 10 }}>↗</span>
          </button>
        )}

        {/* Conversation History */}
        {conversations.length > 0 && (
          <>
            <div className="nav-section-label">
              <span>Your conversations</span>
              <span style={{ fontSize: 10 }}>💬</span>
            </div>
            {conversations.slice(0, 8).map((conv) => (
              <button
                key={conv.id}
                className={`conv-item ${activeConversationId === conv.id ? "active" : ""}`}
                onClick={() => onSelectConversation(conv.id)}
                title={conv.title ?? "Untitled"}
              >
                <span className="conv-icon">□</span>
                <span className="conv-text">
                  {conv.title ?? "Untitled conversation"}
                </span>
              </button>
            ))}
          </>
        )}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        {/* Promo card */}
        <div className="sidebar-promo">
          <div className="promo-title">
            <span>🛡️</span> People first. Always.
          </div>
          <div className="promo-subtitle">
            A little clarity for your everyday work life.
          </div>
        </div>

        {/* Help */}
        <button className="nav-btn" id="btn-help-support">
          <span>❓</span>
          <span>Help & support</span>
          <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--neutral-400)" }}>↗</span>
        </button>

        <div style={{ height: 1, background: "var(--color-border)", margin: "4px 0" }} />

        {/* User profile */}
        {user ? (
          <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
            <button className="user-profile-btn" style={{ flex: 1 }} id="btn-user-profile">
              <div className="user-avatar">{initials}</div>
              <div className="user-info">
                <div className="user-name">{user.name}</div>
                <div className="user-role">
                  {user.role === "HR_ADMIN" ? "HR Admin" : "Employee account"} · {user.region}
                </div>
              </div>
              <span style={{ fontSize: 11, color: "var(--neutral-400)" }}>▾</span>
            </button>
            <button
              onClick={logout}
              style={{
                border: "none",
                background: "transparent",
                cursor: "pointer",
                padding: "8px",
                color: "var(--neutral-400)",
                fontSize: 12,
                borderRadius: "var(--radius-sm)",
              }}
              title="Sign out"
              id="btn-sign-out"
            >
              ⏏
            </button>
          </div>
        ) : (
          <div className="user-profile-btn">
            <div className="user-avatar">?</div>
            <div className="user-info">
              <div className="user-name">Guest</div>
              <div className="user-role">Not signed in</div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
