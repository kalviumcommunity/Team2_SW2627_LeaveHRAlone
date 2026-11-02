"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, ChatResponse, ChatSource, ConversationSummary } from "@/lib/api";
import { Sidebar } from "@/components/Sidebar";
import { ChatInput } from "@/components/ChatInput";
import { MessageBubble } from "@/components/MessageBubble";
import { KnowledgeLibraryModal } from "@/components/KnowledgeLibraryModal";
import { SourcePreviewDrawer } from "@/components/SourcePreviewDrawer";
import { AdminDashboard } from "@/components/AdminDashboard";
import { MyTicketsModal } from "@/components/MyTicketsModal";
import { LoginPage } from "@/components/LoginPage";
import Image from "next/image";

type View = "home" | "chat";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence?: string;
  sources?: ChatResponse["sources"];
  requiresHr?: boolean;
}

const REGION_SUGGESTED_QUESTIONS: Record<string, string[]> = {
  India: [
    "How many days of annual leave do I get?",
    "What does our group health insurance cover?",
    "Can I carry forward unused annual leave?",
    "What is the maternity leave entitlement?",
  ],
  US: [
    "How many days of PTO do I get?",
    "Does our health insurance cover dependents?",
    "What is our remote working policy?",
    "What are our 401(k) retirement benefits?",
  ],
  Global: [
    "What is our workplace code of conduct?",
    "What is our anti-harassment policy?",
    "How do I report a policy violation?",
    "What are the remote work guidelines?",
  ],
};

const DEFAULT_SUGGESTED_QUESTIONS = [
  "How many days of annual leave do I get?",
  "What does our health insurance cover?",
  "What is our remote working policy?",
  "How do I apply for parental leave?",
];

const CATEGORY_CARDS = [
  {
    key: "leave",
    title: "Leave & time off",
    subtitle: "Make room for life.",
    image: "/leave-card.jpg",
    emoji: "🏖️",
    query: "What are the leave and time off policies?",
    imageClass: "leave",
  },
  {
    key: "benefits",
    title: "Benefits & wellbeing",
    subtitle: "Good things, just for you.",
    image: "/benefits-card.jpg",
    emoji: "❤️",
    query: "What benefits and health insurance does the company offer?",
    imageClass: "benefits",
  },
  {
    key: "workplace",
    title: "Workplace policies",
    subtitle: "The how, what and why.",
    image: "/workplace-card.jpg",
    emoji: "📋",
    query: "What are the workplace conduct and handbook policies?",
    imageClass: "workplace",
  },
];

export default function Home() {
  const { user, isLoading: authLoading } = useAuth();
  const [view, setView] = useState<View>("home");
  const [region, setRegion] = useState("India");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isQueryLoading, setIsQueryLoading] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [showLibrary, setShowLibrary] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [showMyTickets, setShowMyTickets] = useState(false);
  const [selectedSource, setSelectedSource] = useState<ChatSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Suggested questions based on selected region
  const activeSuggestedQuestions =
    REGION_SUGGESTED_QUESTIONS[region] || DEFAULT_SUGGESTED_QUESTIONS;

  // Set region from user profile
  useEffect(() => {
    if (user?.region) setRegion(user.region);
  }, [user]);

  // Load conversations when user logs in
  useEffect(() => {
    if (user) {
      api.getConversations()
        .then(setConversations)
        .catch(() => {});
    } else {
      setConversations([]);
    }
  }, [user]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(
    async (query: string) => {
      if (isQueryLoading) return;

      // Switch to chat view if not already
      setView("chat");

      // Append user message
      const userMsgId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        { id: userMsgId, role: "user", content: query },
      ]);

      // Append loading assistant message
      const assistantMsgId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        { id: assistantMsgId, role: "assistant", content: "", isLoading: true } as Message & { isLoading: boolean },
      ]);

      setIsQueryLoading(true);

      try {
        const chatFn = user ? api.chat : api.chatAnonymous;
        const resp = await chatFn({
          query,
          region,
          conversation_id: activeConversationId ?? undefined,
          top_k: 5,
        });

        setActiveConversationId(resp.conversation_id);

        // Replace loading message
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  id: assistantMsgId,
                  role: "assistant",
                  content: resp.answer,
                  confidence: resp.confidence,
                  sources: resp.sources,
                  requiresHr: resp.requires_hr,
                }
              : m
          )
        );

        // Refresh conversation list
        if (user) {
          api.getConversations().then(setConversations).catch(() => {});
        }
      } catch (err: unknown) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  id: assistantMsgId,
                  role: "assistant",
                  content: `Sorry, I encountered an error: ${err instanceof Error ? err.message : "Please try again."}`,
                  confidence: "none",
                  sources: [],
                  requiresHr: false,
                }
              : m
          )
        );
      } finally {
        setIsQueryLoading(false);
      }
    },
    [isQueryLoading, user, region, activeConversationId]
  );

  const handleNewConversation = useCallback(() => {
    setMessages([]);
    setActiveConversationId(null);
    setView("home");
  }, []);

  const handleSelectConversation = useCallback((id: string) => {
    // For now, just switch to chat view and clear messages
    // (full conversation loading would require a messages endpoint)
    setActiveConversationId(id);
    setView("chat");
    const conv = conversations.find((c) => c.id === id);
    if (conv) {
      setMessages([
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Continuing conversation: "${conv.title}". Ask your next HR question.`,
          confidence: "none",
          sources: [],
        },
      ]);
    }
  }, [conversations]);

  const handleCategoryClick = useCallback(
    (query: string) => {
      handleSend(query);
    },
    [handleSend]
  );

  // Show auth loading
  if (authLoading) {
    return (
      <div
        style={{
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--neutral-50)",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🤖</div>
          <div style={{ fontSize: 14, color: "var(--neutral-400)" }}>
            Loading PolicyPilot AI...
          </div>
        </div>
      </div>
    );
  }

  // Show login if not authenticated
  if (!user) {
    return <LoginPage />;
  }

  return (
    <>
      <div className="app-shell">
        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onNewConversation={handleNewConversation}
          onSelectConversation={handleSelectConversation}
          onOpenLibrary={() => setShowLibrary(true)}
          onOpenAdmin={() => setShowAdmin(true)}
          onOpenMyTickets={() => setShowMyTickets(true)}
          onGoHome={() => {
            setView("home");
            setMessages([]);
            setActiveConversationId(null);
          }}
          currentView={view}
        />

        {/* Main content */}
        <div className="main-content">
          {/* Topbar */}
          <div className="topbar">
            <div className="topbar-left">
              <span>💬</span>
              <span>
                {view === "home"
                  ? "Your HR, a conversation away."
                  : "HR conversation"}
              </span>
            </div>
            <div className="topbar-right">
              <div className="region-selector">
                <span>🌐</span>
                <select
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  id="topbar-region-selector"
                >
                  {["India", "US", "UK", "Singapore", "Germany", "Australia", "Global"].map(
                    (r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    )
                  )}
                </select>
                <span style={{ fontSize: 10 }}>▾</span>
              </div>
              <div className="save-indicator">
                <span>🔒</span>
                <span>Saved in browser</span>
              </div>
            </div>
          </div>

          {/* HOME VIEW */}
          {view === "home" && (
            <div className="home-container">
              <div className="home-eyebrow">
                <span>✨</span>
                <span>A little help from your work buddy</span>
              </div>
              <h1 className="home-heading">
                Hey there.
                <br />
                Let&apos;s talk{" "}
                <span className="highlight">people stuff.</span>
              </h1>
              <p className="home-subtext">
                Time off, benefits, the fine print. Ask what&apos;s on your
                mind.
                <br />
                Let&apos;s make your work life a little simpler.
              </p>

              {/* Category Cards */}
              <div className="category-grid">
                {CATEGORY_CARDS.map((card) => (
                  <div
                    key={card.key}
                    className="category-card"
                    onClick={() => handleCategoryClick(card.query)}
                    role="button"
                    tabIndex={0}
                    id={`category-card-${card.key}`}
                    onKeyDown={(e) =>
                      e.key === "Enter" && handleCategoryClick(card.query)
                    }
                  >
                    <div className={`category-card-image ${card.imageClass}`}>
                      <Image
                        src={card.image}
                        alt={card.title}
                        width={400}
                        height={200}
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "cover",
                        }}
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    </div>
                    <div className="category-card-body">
                      <div>
                        <div className="category-card-title">{card.title}</div>
                        <div className="category-card-subtitle">
                          {card.subtitle}
                        </div>
                      </div>
                      <div className="card-arrow">↗</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Suggested Questions */}
              <div className="section-header">
                <div className="section-title">A good place to start</div>
                <div className="section-badge">BIG QUESTIONS. SMALL EFFORT.</div>
              </div>
              <div className="suggested-grid">
                {activeSuggestedQuestions.map((q, i) => (
                  <button
                    key={i}
                    className="suggested-btn"
                    onClick={() => handleSend(q)}
                    id={`suggested-question-${i}`}
                  >
                    <span>{q}</span>
                    <span className="suggested-arrow">↗</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* CHAT VIEW */}
          {view === "chat" && (
            <div className="chat-page">
              <div className="chat-messages">
                <div className="chat-messages-inner">
                  {/* Chat Welcome Header */}
                  <div className="chat-welcome">
                    <div className="chat-bot-avatar">🤖</div>
                    <div>
                      <div className="chat-welcome-title">
                        Let&apos;s figure it out.
                      </div>
                      <div className="chat-welcome-sub">
                        {region} · HR conversation
                      </div>
                    </div>
                  </div>

                  {/* Messages */}
                  {messages.map((msg) => (
                    <div className="message-group" key={msg.id}>
                      <MessageBubble
                        id={msg.id}
                        role={msg.role}
                        content={msg.content}
                        confidence={msg.confidence}
                        sources={msg.sources}
                        requiresHr={msg.requiresHr}
                        conversationId={activeConversationId}
                        onSelectSource={(src) => setSelectedSource(src)}
                        isLoading={
                          msg.role === "assistant" &&
                          msg.content === "" &&
                          isQueryLoading
                        }
                      />
                    </div>
                  ))}

                  <div ref={messagesEndRef} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chat Input - fixed at bottom */}
      <ChatInput
        onSend={handleSend}
        isLoading={isQueryLoading}
        region={region}
        onRegionChange={setRegion}
        placeholder={
          view === "home"
            ? "Ask PolicyPilot anything about your work life..."
            : "Ask a follow-up question..."
        }
      />

      {/* Knowledge Library Modal */}
      <KnowledgeLibraryModal
        isOpen={showLibrary}
        onClose={() => setShowLibrary(false)}
        region={region}
      />

      {/* Side-by-side Source Preview Drawer */}
      <SourcePreviewDrawer
        isOpen={!!selectedSource}
        onClose={() => setSelectedSource(null)}
        source={selectedSource}
      />

      {/* HR Admin Command Center */}
      {showAdmin && <AdminDashboard onClose={() => setShowAdmin(false)} />}

      {/* My HR Tickets Modal */}
      {showMyTickets && (
        <MyTicketsModal onClose={() => setShowMyTickets(false)} />
      )}
    </>
  );
}
