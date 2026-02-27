"use client";

import { useState, useEffect, useCallback } from "react";
import { Auth, type UserData } from "./lib/api";
import TikTokFeed from "./components/tiktok-feed";
import AuthScreen from "./components/auth-screen";
import DiscoverPage from "./components/discover-page";
import ProfilePage from "./components/profile-page";
import BottomNav from "./components/bottom-nav";

export type ActiveView = "home" | "discover" | "profile";

export default function Home() {
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<ActiveView>("home");
  const [toast, setToast] = useState<string | null>(null);

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

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2000);
  }, []);

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-black">
        <div className="w-10 h-10 border-2 border-white/20 border-t-[#fe2c55] rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return <AuthScreen onAuth={handleAuth} />;

  return (
    <div className="h-screen w-screen bg-black relative overflow-hidden">
      <div className={activeView === "home" ? "block h-full" : "hidden"}>
        <TikTokFeed user={user} onToast={showToast} />
      </div>
      <div className={activeView === "discover" ? "block h-full" : "hidden"}>
        <DiscoverPage />
      </div>
      <div className={activeView === "profile" ? "block h-full" : "hidden"}>
        <ProfilePage user={user} onLogout={() => {
          localStorage.removeItem("tiktok_token");
          localStorage.removeItem("tiktok_user_id");
          setUser(null);
        }} />
      </div>

      <BottomNav active={activeView} onChange={setActiveView} />

      {toast && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-[100] bg-neutral-800 text-white text-sm px-4 py-2 rounded-full shadow-lg fade-in">
          {toast}
        </div>
      )}
    </div>
  );
}
