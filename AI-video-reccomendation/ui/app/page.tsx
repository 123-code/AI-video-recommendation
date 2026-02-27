"use client";

import { useState, useEffect, useCallback } from "react";
import { Auth, type UserData } from "./lib/api";
import TikTokFeed from "./components/tiktok-feed";
import AuthScreen from "./components/auth-screen";

export default function Home() {
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("tiktok_token");
    if (token) {
      Auth.me()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem("tiktok_token");
          localStorage.removeItem("tiktok_user_id");
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const handleAuth = useCallback((userData: UserData, token: string) => {
    localStorage.setItem("tiktok_token", token);
    localStorage.setItem("tiktok_user_id", userData.user_id);
    setUser(userData);
  }, []);

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-black">
        <div className="w-10 h-10 border-2 border-white/20 border-t-[#fe2c55] rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <AuthScreen onAuth={handleAuth} />;
  }

  return <TikTokFeed user={user} />;
}
