export const apiUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ============================================================
// Types
// ============================================================
export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  region: string;
  country: string;
  department?: string;
  employment_type: string;
}

export interface AuthToken {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface ChatSource {
  document_title: string;
  section: string;
  page_number: number;
  version: string;
  region: string;
  category: string;
  similarity_score: number;
}

export interface ChatResponse {
  answer: string;
  confidence: "high" | "medium" | "low" | "none";
  sources: ChatSource[];
  requires_hr: boolean;
  conversation_id: string;
  query: string;
  region: string;
  refusal: boolean;
  processing_time_ms?: number;
}

export interface ConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface LibraryDocument {
  id: string;
  title: string;
  category: string;
  region: string;
  version: string;
  effective_date: string;
  status: string;
  file_type: string;
  file_size_bytes: number;
}

// ============================================================
// Auth helpers
// ============================================================
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function storeAuth(auth: AuthToken) {
  localStorage.setItem("access_token", auth.access_token);
  localStorage.setItem("refresh_token", auth.refresh_token);
  localStorage.setItem("user", JSON.stringify(auth.user));
}

export function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

// ============================================================
// Core fetch wrapper
// ============================================================
async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  auth = true
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (auth) {
    const token = getStoredToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const resp = await fetch(`${apiUrl}${path}`, { ...options, headers });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }

  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

// ============================================================
// API methods
// ============================================================
export const api = {
  // Auth
  login: (email: string, password: string) =>
    apiFetch<AuthToken>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, false),

  register: (data: {
    name: string;
    email: string;
    password: string;
    role: string;
    region: string;
    country: string;
    department?: string;
    employment_type: string;
  }) =>
    apiFetch<AuthToken>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }, false),

  getMe: () => apiFetch<User>("/api/auth/me"),

  logout: () =>
    apiFetch<{ message: string }>("/api/auth/logout", { method: "POST" }),

  // Chat
  chat: (data: {
    query: string;
    region?: string;
    conversation_id?: string;
    top_k?: number;
  }) =>
    apiFetch<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Chat without auth (anonymous)
  chatAnonymous: (data: {
    query: string;
    region?: string;
    top_k?: number;
  }) =>
    apiFetch<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify(data),
    }, false),

  // Conversations
  getConversations: () =>
    apiFetch<ConversationSummary[]>("/api/conversations"),

  deleteConversation: (id: string) =>
    apiFetch<void>(`/api/conversations/${id}`, { method: "DELETE" }),

  // Knowledge Library
  getLibrary: (region?: string) => {
    const params = region ? `?region=${encodeURIComponent(region)}` : "";
    return apiFetch<LibraryDocument[]>(`/api/documents/library${params}`, {}, false);
  },

  // Feedback
  submitFeedback: (data: {
    message_id: string;
    rating: boolean;
    reason?: string;
    comment?: string;
  }) =>
    apiFetch<{ id: string; rating: boolean }>("/api/feedback", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Tickets
  createTicket: (data: {
    question: string;
    conversation_id?: string;
    priority?: string;
    confidence?: string;
    retrieved_sources?: any[];
  }) =>
    apiFetch<{ id: string; status: string; question: string }>("/api/tickets", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMyTickets: () =>
    apiFetch<any[]>("/api/tickets/my-tickets"),

  getAdminTickets: (status?: string, priority?: string) => {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (priority) params.append("priority", priority);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<any[]>(`/api/admin/tickets${qs}`);
  },

  updateAdminTicket: (id: string, data: { status?: string; resolution_notes?: string; priority?: string }) =>
    apiFetch<any>(`/api/admin/tickets/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  replyTicket: (id: string, reply: string, status: string = "resolved") =>
    apiFetch<any>(`/api/admin/tickets/${id}/reply`, {
      method: "POST",
      body: JSON.stringify({ reply, status }),
    }),

  convertTicketToFaq: (id: string) =>
    apiFetch<any>(`/api/admin/tickets/${id}/faq-draft`, {
      method: "POST",
    }),

  // Analytics
  getAnalyticsOverview: () =>
    apiFetch<{
      total_questions: number;
      resolved_by_ai: number;
      resolved_percentage: number;
      escalated_questions: number;
      escalated_percentage: number;
      low_confidence_questions: number;
      active_policies: number;
      total_users: number;
    }>("/api/admin/analytics/overview"),

  getAnalyticsTopics: () =>
    apiFetch<Array<{ topic: string; count: number; percentage: number }>>("/api/admin/analytics/topics"),

  getAnalyticsQuestions: () =>
    apiFetch<Array<{ question: string; count: number; resolved: boolean; requires_hr: boolean; region: string }>>("/api/admin/analytics/questions"),

  getUnansweredQuestions: () =>
    apiFetch<Array<{ id: string; question: string; region: string; confidence: string; created_at: string; escalated: boolean }>>("/api/admin/analytics/unanswered"),

  getAnalyticsFeedback: () =>
    apiFetch<{
      total_feedback: number;
      positive_count: number;
      negative_count: number;
      positive_percentage: number;
      reasons_breakdown: Record<string, number>;
    }>("/api/admin/analytics/feedback"),

  // Admin Documents
  getAdminDocuments: (region?: string) => {
    const params = region ? `?region=${encodeURIComponent(region)}` : "";
    return apiFetch<any[]>(`/api/admin/documents${params}`);
  },

  uploadDocument: async (formData: FormData): Promise<any> => {
    const token = getStoredToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${apiUrl}/api/admin/documents`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Failed to upload document");
    }
    return res.json();
  },

  downloadDocumentUrl: (id: string) => `${apiUrl}/api/admin/documents/${id}/download`,

  activateDocument: (id: string) =>
    apiFetch<any>(`/api/admin/documents/${id}/activate`, { method: "POST" }),

  deactivateDocument: (id: string) =>
    apiFetch<any>(`/api/admin/documents/${id}/deactivate`, { method: "POST" }),

  deleteDocument: (id: string) =>
    apiFetch<any>(`/api/admin/documents/${id}`, { method: "DELETE" }),

  updateDocument: (id: string, data: Record<string, any>) =>
    apiFetch<any>(`/api/admin/documents/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  retryDocument: (id: string) =>
    apiFetch<any>(`/api/admin/documents/${id}/retry`, { method: "POST" }),

  reindexDocument: (id: string) =>
    apiFetch<any>(`/api/admin/documents/${id}/reindex`, { method: "POST" }),

  reindexAllDocuments: () =>
    apiFetch<any>("/api/admin/documents/reindex-all", { method: "POST" }),

  getDocumentChunks: (id: string) =>
    apiFetch<any[]>(`/api/admin/documents/${id}/chunks`),

  // User Management
  getUsers: (query?: string, role?: string, region?: string) => {
    const params = new URLSearchParams();
    if (query) params.append("query", query);
    if (role) params.append("role", role);
    if (region) params.append("region", region);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<User[]>(`/api/admin/users${qs}`);
  },

  createUser: (data: any) =>
    apiFetch<User>("/api/admin/users", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateUser: (id: string, data: any) =>
    apiFetch<User>(`/api/admin/users/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteUser: (id: string) =>
    apiFetch<any>(`/api/admin/users/${id}`, { method: "DELETE" }),

  bulkImportUsers: async (file: File): Promise<any> => {
    const token = getStoredToken();
    const formData = new FormData();
    formData.append("file", file);

    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${apiUrl}/api/admin/users/bulk-import`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Bulk import failed" }));
      throw new Error(err.detail || "Failed to bulk import users");
    }
    return res.json();
  },

  inviteUser: (data: { email: string; name?: string; region?: string; role?: string }) =>
    apiFetch<{ invite_token: string; invite_url: string; message: string }>("/api/admin/users/invite", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Health
  health: () =>
    apiFetch<{ status: string }>("/api/health", {}, false),
};

