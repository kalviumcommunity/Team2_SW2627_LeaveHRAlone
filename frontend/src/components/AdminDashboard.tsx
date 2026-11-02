"use client";

import { useEffect, useState, useRef } from "react";
import { api, User } from "@/lib/api";

interface AdminDashboardProps {
  onClose: () => void;
}

export function AdminDashboard({ onClose }: AdminDashboardProps) {
  const [tab, setTab] = useState<"analytics" | "documents" | "tickets" | "users">("analytics");
  const [overview, setOverview] = useState<any>(null);
  const [topics, setTopics] = useState<any[]>([]);
  const [questions, setQuestions] = useState<any[]>([]);
  const [unanswered, setUnanswered] = useState<any[]>([]);
  const [feedback, setFeedback] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [resolutionNote, setResolutionNote] = useState<Record<string, string>>({});

  // Modals state
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [chunksModalOpen, setChunksModalOpen] = useState(false);
  const [selectedDocChunks, setSelectedDocChunks] = useState<any[]>([]);
  const [selectedDocTitle, setSelectedDocTitle] = useState("");
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [csvModalOpen, setCsvModalOpen] = useState(false);
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [inviteUrl, setInviteUrl] = useState("");

  // Upload Form State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadCategory, setUploadCategory] = useState("Leave & Time Off");
  const [uploadRegion, setUploadRegion] = useState("India");
  const [uploadEmpType, setUploadEmpType] = useState("All");
  const [uploadVersion, setUploadVersion] = useState("1.0");
  const [uploadEffectiveDate, setUploadEffectiveDate] = useState(new Date().toISOString().split("T")[0]);
  const [uploadExpirationDate, setUploadExpirationDate] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  // Edit Document State
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingDoc, setEditingDoc] = useState<any>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editCategory, setEditCategory] = useState("Leave & Time Off");
  const [editRegion, setEditRegion] = useState("India");
  const [editEmpType, setEditEmpType] = useState("All");
  const [editVersion, setEditVersion] = useState("1.0");
  const [editEffectiveDate, setEditEffectiveDate] = useState("");
  const [editExpirationDate, setEditExpirationDate] = useState("");
  const [editStatus, setEditStatus] = useState("active");
  const [isUpdatingDoc, setIsUpdatingDoc] = useState(false);
  const [editError, setEditError] = useState("");

  // New User Form State
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [userPassword, setUserPassword] = useState("Welcome2026!");
  const [userRole, setUserRole] = useState("employee");
  const [userRegion, setUserRegion] = useState("India");
  const [userCountry, setUserCountry] = useState("India");
  const [userDept, setUserDept] = useState("Engineering");
  const [userEmpType, setUserEmpType] = useState("Full-Time");

  // CSV Import State
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvResult, setCsvResult] = useState<any>(null);
  const [isImporting, setIsImporting] = useState(false);

  // Polling ref
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  const loadData = async () => {
    try {
      const [ov, top, q, unans, fb, docs, tix, u] = await Promise.allSettled([
        api.getAnalyticsOverview(),
        api.getAnalyticsTopics(),
        api.getAnalyticsQuestions(),
        api.getUnansweredQuestions(),
        api.getAnalyticsFeedback(),
        api.getAdminDocuments(),
        api.getAdminTickets(),
        api.getUsers(),
      ]);

      if (ov.status === "fulfilled") setOverview(ov.value);
      if (top.status === "fulfilled") setTopics(top.value);
      if (q.status === "fulfilled") setQuestions(q.value);
      if (unans.status === "fulfilled") setUnanswered(unans.value);
      if (fb.status === "fulfilled") setFeedback(fb.value);
      if (docs.status === "fulfilled") setDocuments(docs.value);
      if (tix.status === "fulfilled") setTickets(tix.value);
      if (u.status === "fulfilled") setUsers(u.value);
    } catch (err) {
      console.error("Failed to load admin data", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setIsLoading(true);
    loadData();
  }, []);

  // Auto-poll if any document is queued or processing
  useEffect(() => {
    const hasActiveProcessing = documents.some(
      (d) => d.processing_status === "queued" || d.processing_status === "processing"
    );

    if (hasActiveProcessing) {
      pollTimerRef.current = setInterval(async () => {
        const updated = await api.getAdminDocuments().catch(() => null);
        if (updated) setDocuments(updated);
      }, 3000);
    } else if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [documents]);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError("Please select a document file (.pdf, .docx, .txt).");
      return;
    }
    setUploadError("");
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("title", uploadTitle || uploadFile.name.replace(/\.[^/.]+$/, ""));
      formData.append("category", uploadCategory);
      formData.append("region", uploadRegion);
      formData.append("employee_type", uploadEmpType);
      formData.append("version", uploadVersion);
      formData.append("effective_date", uploadEffectiveDate);
      if (uploadExpirationDate) {
        formData.append("expiration_date", uploadExpirationDate);
      }

      await api.uploadDocument(formData);
      setUploadModalOpen(false);
      setUploadFile(null);
      setUploadTitle("");
      setUploadExpirationDate("");
      const updated = await api.getAdminDocuments();
      setDocuments(updated);
    } catch (err: any) {
      setUploadError(err.message || "Upload failed. Please check file format and size.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleToggleDocument = async (docId: string, currentStatus: string) => {
    try {
      if (currentStatus === "active") {
        await api.deactivateDocument(docId);
      } else {
        await api.activateDocument(docId);
      }
      const updated = await api.getAdminDocuments();
      setDocuments(updated);
    } catch {
      alert("Failed to toggle document status");
    }
  };

  const handleOpenEditModal = (doc: any) => {
    setEditingDoc(doc);
    setEditTitle(doc.title || "");
    setEditCategory(doc.category || "Leave & Time Off");
    setEditRegion(doc.region || "India");
    setEditEmpType(doc.employee_type || "All");
    setEditVersion(doc.version || "1.0");
    setEditEffectiveDate(doc.effective_date || "");
    setEditExpirationDate(doc.expiration_date || "");
    setEditStatus(doc.status || "active");
    setEditError("");
    setEditModalOpen(true);
  };

  const handleUpdateDocumentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDoc) return;
    setIsUpdatingDoc(true);
    setEditError("");
    try {
      await api.updateDocument(editingDoc.id, {
        title: editTitle,
        category: editCategory,
        region: editRegion,
        employee_type: editEmpType,
        version: editVersion,
        effective_date: editEffectiveDate,
        expiration_date: editExpirationDate || null,
        status: editStatus,
      });
      setEditModalOpen(false);
      const updated = await api.getAdminDocuments();
      setDocuments(updated);
    } catch (err: any) {
      setEditError(err.message || "Failed to update document metadata");
    } finally {
      setIsUpdatingDoc(false);
    }
  };

  const handleDeleteDocument = async (docId: string, title: string) => {
    if (!confirm(`Are you sure you want to permanently delete '${title}'? This deletes vectors and extracted chunks.`)) return;
    try {
      await api.deleteDocument(docId);
      setDocuments(documents.filter((d) => d.id !== docId));
    } catch {
      alert("Failed to delete document.");
    }
  };

  const handleReindexDocument = async (docId: string) => {
    try {
      await api.reindexDocument(docId);
      const updated = await api.getAdminDocuments();
      setDocuments(updated);
    } catch {
      alert("Failed to trigger reindexing.");
    }
  };

  const handleRetryDocument = async (docId: string) => {
    try {
      await api.retryDocument(docId);
      const updated = await api.getAdminDocuments();
      setDocuments(updated);
    } catch {
      alert("Failed to retry document processing.");
    }
  };

  const handleViewChunks = async (doc: any) => {
    setSelectedDocTitle(doc.title);
    try {
      const chunks = await api.getDocumentChunks(doc.id);
      setSelectedDocChunks(chunks);
      setChunksModalOpen(true);
    } catch {
      alert("Failed to load document chunks.");
    }
  };

  const handleResolveTicket = async (ticketId: string, customStatus = "resolved") => {
    const note = resolutionNote[ticketId] || "Resolved by HR Admin";
    try {
      await api.replyTicket(ticketId, note, customStatus);
      const updated = await api.getAdminTickets();
      setTickets(updated);
    } catch {
      alert("Failed to submit ticket reply.");
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createUser({
        name: userName,
        email: userEmail,
        password: userPassword,
        role: userRole,
        region: userRegion,
        country: userCountry,
        department: userDept,
        employment_type: userEmpType,
      });
      setUserModalOpen(false);
      setUserName("");
      setUserEmail("");
      const updated = await api.getUsers();
      setUsers(updated);
    } catch (err: any) {
      alert(err.message || "Failed to create user");
    }
  };

  const handleDeleteUser = async (userId: string, email: string) => {
    if (!confirm(`Permanently delete user ${email}?`)) return;
    try {
      await api.deleteUser(userId);
      setUsers(users.filter((u) => u.id !== userId));
    } catch (err: any) {
      alert(err.message || "Failed to delete user");
    }
  };

  const handleBulkImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) return;
    setIsImporting(true);
    try {
      const res = await api.bulkImportUsers(csvFile);
      setCsvResult(res);
      const updated = await api.getUsers();
      setUsers(updated);
    } catch (err: any) {
      alert(err.message || "Bulk import failed.");
    } finally {
      setIsImporting(false);
    }
  };

  const handleGenerateInvite = async () => {
    const email = prompt("Enter employee email address for onboarding invite:");
    if (!email) return;
    try {
      const res = await api.inviteUser({ email, region: "India", role: "employee" });
      setInviteUrl(window.location.origin + res.invite_url);
      setInviteModalOpen(true);
    } catch (err: any) {
      alert(err.message || "Failed to create invite");
    }
  };

  return (
    <div className="admin-overlay" onClick={onClose}>
      <div
        className="admin-container"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="HR Admin Command Center"
        style={{ maxWidth: 1100 }}
      >
        {/* Header */}
        <div className="admin-header">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div className="admin-badge-icon">⚡</div>
            <div>
              <div className="admin-eyebrow">HR ADMIN COMMAND CENTER</div>
              <h1 className="admin-title">PolicyPilot AI Governance & Live RAG Engine</h1>
            </div>
          </div>
          <button className="admin-close-btn" onClick={onClose} id="btn-close-admin-dash">
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="admin-nav-tabs">
          <button
            className={`admin-tab-btn ${tab === "analytics" ? "active" : ""}`}
            onClick={() => setTab("analytics")}
          >
            📊 Analytics & Insights
          </button>
          <button
            className={`admin-tab-btn ${tab === "documents" ? "active" : ""}`}
            onClick={() => setTab("documents")}
          >
            📚 Policy Documents ({documents.length})
          </button>
          <button
            className={`admin-tab-btn ${tab === "tickets" ? "active" : ""}`}
            onClick={() => setTab("tickets")}
          >
            🎫 HR Escalations ({tickets.filter((t) => t.status === "open").length} open)
          </button>
          <button
            className={`admin-tab-btn ${tab === "users" ? "active" : ""}`}
            onClick={() => setTab("users")}
          >
            👥 User Management ({users.length})
          </button>
        </div>

        {isLoading ? (
          <div className="admin-loading">
            <div className="admin-spinner" />
            <span>Connecting to live PostgreSQL and vector database...</span>
          </div>
        ) : (
          <div className="admin-content">
            {/* TAB 1: ANALYTICS */}
            {tab === "analytics" && (
              <div>
                <div className="admin-kpi-grid">
                  <div className="admin-kpi-card">
                    <div className="kpi-label">Total Employee Inquiries</div>
                    <div className="kpi-value">{overview?.total_questions ?? 0}</div>
                    <div className="kpi-sub">Across all regional jurisdictions</div>
                  </div>
                  <div className="kpi-card-highlight">
                    <div className="kpi-label">AI Resolution Rate</div>
                    <div className="kpi-value">{overview?.resolved_percentage ?? 0}%</div>
                    <div className="kpi-sub">Grounded in company policies</div>
                  </div>
                  <div className="admin-kpi-card">
                    <div className="kpi-label">HR Escalated Tickets</div>
                    <div className="kpi-value">{overview?.escalated_questions ?? 0}</div>
                    <div className="kpi-sub">{overview?.escalated_percentage ?? 0}% escalation rate</div>
                  </div>
                  <div className="admin-kpi-card">
                    <div className="kpi-label">Active Policies</div>
                    <div className="kpi-value">{overview?.active_policies ?? documents.length}</div>
                    <div className="kpi-sub">Indexed in Qdrant Vector Store</div>
                  </div>
                </div>

                {/* Unanswered Gaps Panel */}
                <div className="admin-panel" style={{ marginTop: 20 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                    <div>
                      <h3 className="panel-title">⚠️ Knowledge Gaps & Unanswered Queries</h3>
                      <p style={{ fontSize: 12, color: "var(--neutral-400)" }}>
                        Low confidence questions from employees that lack policy coverage.
                      </p>
                    </div>
                    <button
                      className="ticket-resolve-btn"
                      onClick={() => {
                        setTab("documents");
                        setUploadModalOpen(true);
                      }}
                      style={{ background: "#2563eb", padding: "6px 12px" }}
                    >
                      + Upload Document to Fill Gap
                    </button>
                  </div>

                  <div className="attention-table">
                    {unanswered.length === 0 ? (
                      <div style={{ padding: 12, color: "var(--neutral-400)", textAlign: "center" }}>
                        ✓ No unresolved policy gaps found. All queries are supported.
                      </div>
                    ) : (
                      unanswered.map((u, idx) => (
                        <div key={idx} className="attention-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <div>
                            <div className="attention-q">{u.question}</div>
                            <div className="attention-meta">
                              Region: {u.region} • Date: {new Date(u.created_at).toLocaleDateString()}
                            </div>
                          </div>
                          <button
                            className="admin-toggle-btn"
                            onClick={() => {
                              setUploadTitle(u.question.substring(0, 40) + " Policy");
                              setUploadRegion(u.region || "Global");
                              setTab("documents");
                              setUploadModalOpen(true);
                            }}
                          >
                            Bridge Gap ↗
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Topics & Feedback Grids */}
                <div className="admin-charts-grid" style={{ marginTop: 20 }}>
                  <div className="admin-panel">
                    <h3 className="panel-title">Most Asked Policy Domains</h3>
                    <div className="topic-bars-list">
                      {topics.map((t, idx) => (
                        <div key={idx} className="topic-bar-row">
                          <div className="topic-bar-info">
                            <span className="topic-name">{t.topic}</span>
                            <span className="topic-pct">{t.percentage}% ({t.count})</span>
                          </div>
                          <div className="topic-bar-track">
                            <div className="topic-bar-fill" style={{ width: `${Math.max(t.percentage, 8)}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="admin-panel">
                    <h3 className="panel-title">Employee Feedback Ratings</h3>
                    <div className="feedback-score-row">
                      <div className="feedback-score-big">{feedback?.positive_percentage ?? 100}%</div>
                      <div style={{ fontSize: 13, color: "var(--neutral-400)" }}>
                        Positive rating across {feedback?.total_feedback ?? 0} reviews.
                      </div>
                    </div>
                    <div style={{ marginTop: 14, fontSize: 12, fontWeight: 600 }}>Driver Breakdown:</div>
                    <div className="reasons-list">
                      {feedback?.reasons_breakdown &&
                        Object.entries(feedback.reasons_breakdown).map(([r, c]) => (
                          <div key={r} className="reason-item">
                            <span>{r}</span>
                            <span className="reason-count">{c as number}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: DOCUMENTS */}
            {tab === "documents" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 700 }}>Active Company Policies</h3>
                    <p style={{ fontSize: 12, color: "var(--neutral-400)" }}>
                      Real enterprise policies parsed, tokenized, and indexed into Qdrant for semantic search.
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      className="ticket-resolve-btn"
                      onClick={() => setUploadModalOpen(true)}
                      style={{ background: "#16a34a" }}
                    >
                      + Upload Real Policy
                    </button>
                    <button
                      className="admin-toggle-btn"
                      onClick={() => api.reindexAllDocuments().then(() => alert("Reindexing triggered."))}
                    >
                      🔄 Reindex All
                    </button>
                  </div>
                </div>

                <div className="docs-table-wrapper">
                  <table className="docs-table">
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Category</th>
                        <th>Region / Scope</th>
                        <th>Version</th>
                        <th>Effective / Expiry</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {documents.length === 0 ? (
                        <tr>
                          <td colSpan={7} style={{ textAlign: "center", padding: 24, color: "var(--neutral-400)" }}>
                            No policy documents uploaded yet. Click <strong>+ Upload Real Policy</strong> to ingest your first PDF, DOCX, or TXT file.
                          </td>
                        </tr>
                      ) : (
                        documents.map((doc) => {
                          const isExpired = doc.expiration_date && new Date(doc.expiration_date) < new Date();
                          return (
                            <tr key={doc.id}>
                              <td>
                                <div style={{ fontWeight: 600 }}>{doc.title}</div>
                                <div style={{ fontSize: 11, color: "var(--neutral-400)" }}>{doc.file_type.toUpperCase()} • {(doc.file_size_bytes / 1024).toFixed(1)} KB</div>
                              </td>
                              <td>{doc.category}</td>
                              <td>
                                <span className="region-tag">{doc.region}</span>
                                {doc.employee_type !== "All" && (
                                  <span style={{ fontSize: 10, background: "#e0f2fe", color: "#0369a1", padding: "2px 4px", borderRadius: 4, marginLeft: 4 }}>
                                    {doc.employee_type}
                                  </span>
                                )}
                              </td>
                              <td>v{doc.version}</td>
                              <td>
                                <div>{doc.effective_date}</div>
                                {doc.expiration_date && (
                                  <div style={{ fontSize: 10, color: isExpired ? "#dc2626" : "var(--neutral-400)" }}>
                                    {isExpired ? "⚠️ Expired: " : "Exp: "}
                                    {doc.expiration_date}
                                  </div>
                                )}
                              </td>
                              <td>
                                <span
                                  className={`status-pill ${
                                    doc.processing_status === "ready"
                                      ? doc.status === "active"
                                        ? "active"
                                        : "inactive"
                                      : doc.processing_status === "failed"
                                      ? "escalated"
                                      : "in_progress"
                                  }`}
                                >
                                  {doc.processing_status === "processing" ? "⏳ Processing..." : doc.processing_status === "failed" ? "❌ Failed" : doc.status}
                                </span>
                              </td>
                              <td>
                                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                                  <a
                                    href={api.downloadDocumentUrl(doc.id)}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="admin-toggle-btn"
                                    style={{ textDecoration: "none" }}
                                  >
                                    ⬇️ File
                                  </a>
                                  <button className="admin-toggle-btn" onClick={() => handleOpenEditModal(doc)}>
                                    ✏️ Edit
                                  </button>
                                  <button className="admin-toggle-btn" onClick={() => handleViewChunks(doc)}>
                                    🔍 Chunks
                                  </button>
                                  {doc.processing_status === "failed" ? (
                                    <button className="admin-toggle-btn" style={{ color: "#dc2626" }} onClick={() => handleRetryDocument(doc.id)}>
                                      🔄 Retry
                                    </button>
                                  ) : (
                                    <button className="admin-toggle-btn" onClick={() => handleReindexDocument(doc.id)}>
                                      🔄 Reindex
                                    </button>
                                  )}
                                  <button className="admin-toggle-btn" onClick={() => handleToggleDocument(doc.id, doc.status)}>
                                    {doc.status === "active" ? "Deactivate" : "Activate"}
                                  </button>
                                  <button
                                    className="admin-toggle-btn"
                                    style={{ color: "#dc2626" }}
                                    onClick={() => handleDeleteDocument(doc.id, doc.title)}
                                  >
                                    🗑️
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: TICKETS */}
            {tab === "tickets" && (
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>
                  Escalated Policy Queries & HR Resolutions
                </h3>
                {tickets.length === 0 ? (
                  <div className="empty-tickets">
                    <span>🎉</span>
                    <div>No pending employee escalations. All inquiries resolved by PolicyPilot AI.</div>
                  </div>
                ) : (
                  <div className="tickets-grid">
                    {tickets.map((t) => (
                      <div key={t.id} className="ticket-card">
                        <div className="ticket-card-header">
                          <span className={`ticket-priority-pill ${t.priority}`}>
                            {t.priority.toUpperCase()} PRIORITY
                          </span>
                          <span className={`status-pill ${t.status}`}>
                            {t.status.toUpperCase()}
                          </span>
                        </div>
                        <div className="ticket-question">{t.question}</div>
                        <div className="ticket-meta">
                          Created: {new Date(t.created_at).toLocaleString()}
                        </div>

                        {t.status === "open" ? (
                          <div className="ticket-action-box">
                            <input
                              type="text"
                              placeholder="Write HR resolution note for employee..."
                              value={resolutionNote[t.id] ?? ""}
                              onChange={(e) =>
                                setResolutionNote({
                                  ...resolutionNote,
                                  [t.id]: e.target.value,
                                })
                              }
                              className="ticket-note-input"
                            />
                            <button
                              className="ticket-resolve-btn"
                              onClick={() => handleResolveTicket(t.id)}
                            >
                              Send Reply & Resolve
                            </button>
                          </div>
                        ) : (
                          <div className="ticket-resolved-note">
                            <strong>HR Resolution:</strong> {t.resolution_notes || "Resolved by HR Admin."}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: USERS */}
            {tab === "users" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 700 }}>Employee Roster & Roles</h3>
                    <p style={{ fontSize: 12, color: "var(--neutral-400)" }}>
                      Manage enterprise employees, roles, departments, and regional policy jurisdictions.
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      className="ticket-resolve-btn"
                      style={{ background: "#2563eb" }}
                      onClick={() => setUserModalOpen(true)}
                    >
                      + Add Employee
                    </button>
                    <button
                      className="admin-toggle-btn"
                      onClick={() => setCsvModalOpen(true)}
                    >
                      📁 Bulk CSV Import
                    </button>
                    <button
                      className="admin-toggle-btn"
                      onClick={handleGenerateInvite}
                    >
                      ✉️ Invite Link
                    </button>
                  </div>
                </div>

                <div className="docs-table-wrapper">
                  <table className="docs-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Region</th>
                        <th>Department</th>
                        <th>Employment</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u) => (
                        <tr key={u.id}>
                          <td style={{ fontWeight: 600 }}>{u.name}</td>
                          <td>{u.email}</td>
                          <td>
                            <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>
                              {u.role}
                            </span>
                          </td>
                          <td>
                            <span className="region-tag">{u.region}</span>
                          </td>
                          <td>{u.department || "General"}</td>
                          <td>{u.employment_type}</td>
                          <td>
                            <button
                              className="admin-toggle-btn"
                              style={{ color: "#dc2626" }}
                              onClick={() => handleDeleteUser(u.id, u.email)}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Upload Modal */}
        {uploadModalOpen && (
          <div className="admin-overlay" style={{ zIndex: 1100 }}>
            <div className="admin-container" style={{ maxWidth: 550, padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700 }}>Upload Real Policy Document</h3>
                <button className="admin-close-btn" onClick={() => setUploadModalOpen(false)}>✕</button>
              </div>

              {uploadError && (
                <div style={{ background: "#fee2e2", color: "#991b1b", padding: "8px 12px", borderRadius: 6, fontSize: 12, marginBottom: 12 }}>
                  {uploadError}
                </div>
              )}

              <form onSubmit={handleUploadSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600 }}>Policy Document File (PDF, DOCX, TXT):</label>
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc,.txt"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    required
                    style={{ width: "100%", marginTop: 4 }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600 }}>Policy Title:</label>
                  <input
                    type="text"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    placeholder="e.g. Employee Leave & Holiday Policy 2026"
                    className="ticket-note-input"
                    style={{ width: "100%", marginTop: 4 }}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Category:</label>
                    <select
                      value={uploadCategory}
                      onChange={(e) => setUploadCategory(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    >
                      <option value="Leave & Time Off">Leave & Time Off</option>
                      <option value="Benefits & Insurance">Benefits & Insurance</option>
                      <option value="Remote Work">Remote Work</option>
                      <option value="Workplace Policies">Workplace Policies</option>
                      <option value="Payroll & Compensation">Payroll & Compensation</option>
                      <option value="General">General</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Region:</label>
                    <select
                      value={uploadRegion}
                      onChange={(e) => setUploadRegion(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    >
                      <option value="India">India</option>
                      <option value="US">US</option>
                      <option value="Global">Global</option>
                      <option value="UK">UK</option>
                      <option value="Singapore">Singapore</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Employee Type:</label>
                    <select
                      value={uploadEmpType}
                      onChange={(e) => setUploadEmpType(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    >
                      <option value="All">All Employees</option>
                      <option value="Full-Time">Full-Time</option>
                      <option value="Contractor">Contractor</option>
                      <option value="Intern">Intern</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Version:</label>
                    <input
                      type="text"
                      value={uploadVersion}
                      onChange={(e) => setUploadVersion(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Effective Date:</label>
                    <input
                      type="date"
                      value={uploadEffectiveDate}
                      onChange={(e) => setUploadEffectiveDate(e.target.value)}
                      className="ticket-note-input"
                      required
                      style={{ width: "100%", marginTop: 4 }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Expiration Date (Optional):</label>
                    <input
                      type="date"
                      value={uploadExpirationDate}
                      onChange={(e) => setUploadExpirationDate(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    />
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 12 }}>
                  <button type="button" className="admin-toggle-btn" onClick={() => setUploadModalOpen(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="ticket-resolve-btn" disabled={isUploading} style={{ background: "#16a34a" }}>
                    {isUploading ? "Uploading & Ingesting..." : "Upload & Ingest Policy"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edit Document Modal */}
        {editModalOpen && editingDoc && (
          <div className="admin-overlay" style={{ zIndex: 1200 }}>
            <div className="admin-container" style={{ maxWidth: 560, padding: 24, maxHeight: "90vh", overflowY: "auto" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
                <div>
                  <h3 style={{ fontSize: 18, fontWeight: 700 }}>✏️ Edit Policy Document</h3>
                  <p style={{ fontSize: 12, color: "var(--neutral-400)" }}>
                    Update metadata for <strong>{editingDoc.title}</strong>. Changes will synchronize with Qdrant vector search filters.
                  </p>
                </div>
                <button className="admin-close-btn" onClick={() => setEditModalOpen(false)}>✕</button>
              </div>

              {editError && (
                <div style={{ background: "#fef2f2", color: "#b91c1c", padding: "8px 12px", borderRadius: 6, fontSize: 13, marginBottom: 12 }}>
                  {editError}
                </div>
              )}

              <form onSubmit={handleUpdateDocumentSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600 }}>Policy Title:</label>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    required
                    className="ticket-note-input"
                    style={{ width: "100%", marginTop: 4 }}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Category:</label>
                    <select
                      value={editCategory}
                      onChange={(e) => setEditCategory(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    >
                      <option value="Leave & Time Off">Leave & Time Off</option>
                      <option value="Benefits & Insurance">Benefits & Insurance</option>
                      <option value="Remote Work">Remote Work</option>
                      <option value="Workplace Policies">Workplace Policies</option>
                      <option value="Payroll & Compensation">Payroll & Compensation</option>
                      <option value="General">General</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Region:</label>
                    <select
                      value={editRegion}
                      onChange={(e) => setEditRegion(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    >
                      <option value="India">India</option>
                      <option value="US">US</option>
                      <option value="Global">Global</option>
                      <option value="UK">UK</option>
                      <option value="Singapore">Singapore</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Employee Type:</label>
                    <select
                      value={editEmpType}
                      onChange={(e) => setEditEmpType(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    >
                      <option value="All">All Employees</option>
                      <option value="Full-Time">Full-Time</option>
                      <option value="Contractor">Contractor</option>
                      <option value="Intern">Intern</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Version:</label>
                    <input
                      type="text"
                      value={editVersion}
                      onChange={(e) => setEditVersion(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Effective Date:</label>
                    <input
                      type="date"
                      value={editEffectiveDate}
                      onChange={(e) => setEditEffectiveDate(e.target.value)}
                      className="ticket-note-input"
                      required
                      style={{ width: "100%", marginTop: 4 }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Expiration Date (Optional):</label>
                    <input
                      type="date"
                      value={editExpirationDate}
                      onChange={(e) => setEditExpirationDate(e.target.value)}
                      className="ticket-note-input"
                      style={{ width: "100%", marginTop: 4 }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600 }}>Status:</label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value)}
                    className="ticket-note-input"
                    style={{ width: "100%", marginTop: 4 }}
                  >
                    <option value="active">Active (retrievable by employees)</option>
                    <option value="inactive">Inactive (archived / draft)</option>
                  </select>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 12 }}>
                  <button type="button" className="admin-toggle-btn" onClick={() => setEditModalOpen(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="ticket-resolve-btn" disabled={isUpdatingDoc} style={{ background: "#2563eb" }}>
                    {isUpdatingDoc ? "Saving Changes..." : "Save Policy Changes"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Chunks Inspection Modal */}
        {chunksModalOpen && (
          <div className="admin-overlay" style={{ zIndex: 1200 }}>
            <div className="admin-container" style={{ maxWidth: 800, padding: 24, maxHeight: "85vh", overflowY: "auto" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                <div>
                  <h3 style={{ fontSize: 18, fontWeight: 700 }}>Indexed Chunks: {selectedDocTitle}</h3>
                  <p style={{ fontSize: 12, color: "var(--neutral-400)" }}>{selectedDocChunks.length} chunks extracted and vectorized in Qdrant.</p>
                </div>
                <button className="admin-close-btn" onClick={() => setChunksModalOpen(false)}>✕</button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {selectedDocChunks.map((ch, idx) => (
                  <div key={idx} style={{ border: "1px solid var(--neutral-200)", borderRadius: 8, padding: 12, background: "#fafaf9" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--neutral-500)", marginBottom: 6 }}>
                      <span>Chunk #{ch.chunk_index + 1} • Page {ch.page_number} • Section: <strong>{ch.section}</strong></span>
                      <span>{ch.token_count} tokens</span>
                    </div>
                    <div style={{ fontSize: 13, whiteSpace: "pre-wrap", lineHeight: 1.5, color: "var(--neutral-800)" }}>
                      {ch.chunk_text}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* User Creation Modal */}
        {userModalOpen && (
          <div className="admin-overlay" style={{ zIndex: 1100 }}>
            <div className="admin-container" style={{ maxWidth: 500, padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700 }}>Add Employee to PolicyPilot</h3>
                <button className="admin-close-btn" onClick={() => setUserModalOpen(false)}>✕</button>
              </div>

              <form onSubmit={handleCreateUser} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600 }}>Full Name:</label>
                  <input
                    type="text"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                    required
                    className="ticket-note-input"
                    style={{ width: "100%", marginTop: 4 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600 }}>Work Email:</label>
                  <input
                    type="email"
                    value={userEmail}
                    onChange={(e) => setUserEmail(e.target.value)}
                    required
                    className="ticket-note-input"
                    style={{ width: "100%", marginTop: 4 }}
                  />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Role:</label>
                    <select value={userRole} onChange={(e) => setUserRole(e.target.value)} className="ticket-note-input" style={{ width: "100%", marginTop: 4 }}>
                      <option value="employee">Employee</option>
                      <option value="hr_admin">HR Admin</option>
                      <option value="super_admin">Super Admin</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Region:</label>
                    <select value={userRegion} onChange={(e) => setUserRegion(e.target.value)} className="ticket-note-input" style={{ width: "100%", marginTop: 4 }}>
                      <option value="India">India</option>
                      <option value="US">US</option>
                      <option value="Global">Global</option>
                      <option value="UK">UK</option>
                    </select>
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Department:</label>
                    <input type="text" value={userDept} onChange={(e) => setUserDept(e.target.value)} className="ticket-note-input" style={{ width: "100%", marginTop: 4 }} />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600 }}>Employment Type:</label>
                    <select value={userEmpType} onChange={(e) => setUserEmpType(e.target.value)} className="ticket-note-input" style={{ width: "100%", marginTop: 4 }}>
                      <option value="Full-Time">Full-Time</option>
                      <option value="Contractor">Contractor</option>
                      <option value="Intern">Intern</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 12 }}>
                  <button type="button" className="admin-toggle-btn" onClick={() => setUserModalOpen(false)}>Cancel</button>
                  <button type="submit" className="ticket-resolve-btn" style={{ background: "#2563eb" }}>Create Employee</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* CSV Modal */}
        {csvModalOpen && (
          <div className="admin-overlay" style={{ zIndex: 1100 }}>
            <div className="admin-container" style={{ maxWidth: 500, padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700 }}>Bulk Employee Import (CSV)</h3>
                <button className="admin-close-btn" onClick={() => setCsvModalOpen(false)}>✕</button>
              </div>

              <p style={{ fontSize: 12, color: "var(--neutral-500)", marginBottom: 12 }}>
                Upload a CSV with columns: <code>name, email, role, region, country, department, employment_type</code>
              </p>

              {csvResult && (
                <div style={{ background: "#f0fdf4", color: "#166534", padding: 12, borderRadius: 6, fontSize: 12, marginBottom: 12 }}>
                  {csvResult.message}
                </div>
              )}

              <form onSubmit={handleBulkImport}>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                  required
                  style={{ width: "100%", marginBottom: 16 }}
                />

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
                  <button type="button" className="admin-toggle-btn" onClick={() => setCsvModalOpen(false)}>Close</button>
                  <button type="submit" className="ticket-resolve-btn" disabled={isImporting}>
                    {isImporting ? "Importing..." : "Process CSV"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Invite URL Modal */}
        {inviteModalOpen && (
          <div className="admin-overlay" style={{ zIndex: 1200 }}>
            <div className="admin-container" style={{ maxWidth: 500, padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700 }}>Employee Onboarding Link</h3>
                <button className="admin-close-btn" onClick={() => setInviteModalOpen(false)}>✕</button>
              </div>

              <p style={{ fontSize: 12, color: "var(--neutral-500)", marginBottom: 8 }}>
                Share this secure registration link with the employee:
              </p>

              <input
                type="text"
                readOnly
                value={inviteUrl}
                className="ticket-note-input"
                style={{ width: "100%", marginBottom: 12 }}
                onClick={(e) => (e.target as HTMLInputElement).select()}
              />

              <button
                className="ticket-resolve-btn"
                style={{ width: "100%" }}
                onClick={() => {
                  navigator.clipboard.writeText(inviteUrl);
                  alert("Invite link copied to clipboard!");
                }}
              >
                Copy Link 📋
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
