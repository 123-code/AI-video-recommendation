"use client";

import { useState } from "react";
import { Auth, type UserData } from "../lib/api";

interface Props {
  onAuth: (user: UserData, token: string) => void;
}

export default function AuthScreen({ onAuth }: Props) {
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");
  const [isLogin, setIsLogin] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || username.trim().length < 3) {
      setError("Username must be at least 3 characters");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const fn = isLogin ? Auth.login : Auth.register;
      const { token, user } = await fn(username.trim().toLowerCase());
      onAuth(user, token);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      if (!isLogin && msg.includes("taken")) {
        setError("Username taken — try logging in instead");
      } else if (isLogin && msg.includes("not found")) {
        setError("User not found — try signing up instead");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-black flex flex-col items-center justify-center px-8">
      <div className="mb-12 flex items-center gap-2">
        <svg width="40" height="40" viewBox="0 0 48 48" fill="none">
          <path d="M34.1 10.1a8.6 8.6 0 0 1-5.4-2 8.6 8.6 0 0 1-2.6-5.1h-5.8v22.7a5.1 5.1 0 0 1-5 5.2 5.1 5.1 0 0 1-5.1-5.2 5.1 5.1 0 0 1 5.1-5.1c.5 0 1 .1 1.5.2v-5.9a11 11 0 0 0-1.5-.1A10.9 10.9 0 0 0 4.4 25.7a10.9 10.9 0 0 0 10.9 10.8A10.9 10.9 0 0 0 26.2 25.7V15a14.3 14.3 0 0 0 8.4 2.7V12a8.8 8.8 0 0 1-.5-1.9z" fill="#fe2c55"/>
          <path d="M31.7 10.1a8.6 8.6 0 0 1-5.4-2A8.6 8.6 0 0 1 23.7 3h-5.8v22.7a5.1 5.1 0 0 1-5 5.2 5.1 5.1 0 0 1-5.1-5.2A5.1 5.1 0 0 1 12.9 20.6c.5 0 1 .1 1.5.2v-5.9a11 11 0 0 0-1.5-.1A10.9 10.9 0 0 0 2 25.7a10.9 10.9 0 0 0 10.9 10.8 10.9 10.9 0 0 0 10.9-10.8V15a14.3 14.3 0 0 0 8.4 2.7V12a8.6 8.6 0 0 1-.5-1.9z" fill="#25f4ee"/>
          <path d="M32.9 10.1a8.6 8.6 0 0 1-5.4-2A8.6 8.6 0 0 1 24.9 3h-5.8v22.7a5.1 5.1 0 0 1-5 5.2 5.1 5.1 0 0 1-5.1-5.2 5.1 5.1 0 0 1 5.1-5.1c.5 0 1 .1 1.5.2v-5.9a11 11 0 0 0-1.5-.1A10.9 10.9 0 0 0 3.2 25.7a10.9 10.9 0 0 0 10.9 10.8A10.9 10.9 0 0 0 25 25.7V15a14.3 14.3 0 0 0 8.4 2.7V12a8.6 8.6 0 0 1-.5-1.9z" fill="white"/>
        </svg>
        <span className="text-3xl font-bold tracking-tight">TikTok</span>
      </div>

      <form onSubmit={handleSubmit} className="w-full max-w-xs space-y-4">
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Enter username"
          className="w-full px-4 py-3 bg-[#1e1e1e] rounded-lg text-white placeholder-neutral-500 outline-none focus:ring-2 focus:ring-[#fe2c55] text-base"
          maxLength={20}
          autoFocus
        />
        {error && <p className="text-[#fe2c55] text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-[#fe2c55] text-white font-semibold rounded-lg hover:bg-[#e0264c] transition-colors disabled:opacity-50 text-base"
        >
          {loading ? "..." : isLogin ? "Log in" : "Sign up"}
        </button>
        <button
          type="button"
          onClick={() => { setIsLogin(!isLogin); setError(""); }}
          className="w-full text-center text-neutral-400 text-sm hover:text-white transition-colors"
        >
          {isLogin ? "Don't have an account? Sign up" : "Already have an account? Log in"}
        </button>
      </form>
    </div>
  );
}
