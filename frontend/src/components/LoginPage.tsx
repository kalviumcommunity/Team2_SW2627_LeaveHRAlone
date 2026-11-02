"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";

const REGIONS = ["India", "US", "UK", "Singapore", "Germany", "Australia", "Global"];

export function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Login form state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register form state
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regRole, setRegRole] = useState("EMPLOYEE");
  const [regRegion, setRegRegion] = useState("India");
  const [regCountry, setRegCountry] = useState("India");
  const [regDept, setRegDept] = useState("");
  const [regEmpType, setRegEmpType] = useState("Full-Time");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginEmail || !loginPassword) return;
    setIsLoading(true);
    setError(null);
    try {
      await login(loginEmail, loginPassword);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed. Please check your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName || !regEmail || !regPassword) return;
    setIsLoading(true);
    setError(null);
    try {
      await register({
        name: regName,
        email: regEmail,
        password: regPassword,
        role: regRole,
        region: regRegion,
        country: regCountry,
        department: regDept || undefined,
        employment_type: regEmpType,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <div className="logo-mark">🤖</div>
          <div>
            <div
              style={{
                fontSize: 18,
                fontWeight: 800,
                color: "var(--brand-black)",
                letterSpacing: "-0.5px",
              }}
            >
              PolicyPilot<span style={{ color: "var(--brand-yellow-dark)" }}> AI</span>
            </div>
            <div style={{ fontSize: 11, color: "var(--neutral-400)", fontWeight: 600 }}>
              YOUR PEOPLE. YOUR ANSWERS.
            </div>
          </div>
        </div>

        <div className="login-title">
          {mode === "login" ? "Welcome back." : "Create your account."}
        </div>
        <div className="login-subtitle">
          {mode === "login"
            ? "Sign in to access your HR policy assistant."
            : "Set up your PolicyPilot AI account to get started."}
        </div>

        {/* Demo hint */}
        <div className="login-demo-hint">
          💡 <strong>Demo mode:</strong> Register a new account to explore. Use role &quot;HR_ADMIN&quot; to access the admin portal.
        </div>

        {error && <div className="login-error">⚠️ {error}</div>}

        {mode === "login" ? (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label" htmlFor="login-email">Email</label>
              <input
                id="login-email"
                className="form-input"
                type="email"
                placeholder="you@company.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="login-password">Password</label>
              <input
                id="login-password"
                className="form-input"
                type="password"
                placeholder="Your password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                required
              />
            </div>
            <button
              className="login-submit-btn"
              type="submit"
              disabled={isLoading}
              id="btn-login-submit"
            >
              {isLoading ? "Signing in..." : "Sign in →"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegister}>
            <div className="form-group">
              <label className="form-label" htmlFor="reg-name">Full name</label>
              <input
                id="reg-name"
                className="form-input"
                type="text"
                placeholder="Alex Johnson"
                value={regName}
                onChange={(e) => setRegName(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="reg-email">Work email</label>
              <input
                id="reg-email"
                className="form-input"
                type="email"
                placeholder="alex@company.com"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="reg-password">Password</label>
              <input
                id="reg-password"
                className="form-input"
                type="password"
                placeholder="Min 8 characters"
                value={regPassword}
                onChange={(e) => setRegPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label" htmlFor="reg-role">Role</label>
                <select
                  id="reg-role"
                  className="form-select"
                  value={regRole}
                  onChange={(e) => setRegRole(e.target.value)}
                >
                  <option value="EMPLOYEE">Employee</option>
                  <option value="HR_ADMIN">HR Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="reg-region">Region</label>
                <select
                  id="reg-region"
                  className="form-select"
                  value={regRegion}
                  onChange={(e) => {
                    setRegRegion(e.target.value);
                    setRegCountry(e.target.value === "US" ? "United States" : e.target.value);
                  }}
                >
                  {REGIONS.filter((r) => r !== "Global").map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label" htmlFor="reg-dept">Department</label>
                <input
                  id="reg-dept"
                  className="form-input"
                  type="text"
                  placeholder="Engineering"
                  value={regDept}
                  onChange={(e) => setRegDept(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="reg-emp-type">Employment type</label>
                <select
                  id="reg-emp-type"
                  className="form-select"
                  value={regEmpType}
                  onChange={(e) => setRegEmpType(e.target.value)}
                >
                  <option>Full-Time</option>
                  <option>Part-Time</option>
                  <option>Contractor</option>
                  <option>Intern</option>
                </select>
              </div>
            </div>
            <button
              className="login-submit-btn"
              type="submit"
              disabled={isLoading}
              id="btn-register-submit"
            >
              {isLoading ? "Creating account..." : "Create account →"}
            </button>
          </form>
        )}

        <div className="login-toggle">
          {mode === "login" ? (
            <>
              Don&apos;t have an account?{" "}
              <button onClick={() => { setMode("register"); setError(null); }} id="btn-switch-to-register">
                Sign up
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button onClick={() => { setMode("login"); setError(null); }} id="btn-switch-to-login">
                Sign in
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
