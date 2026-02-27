"use client";

import { useState, useEffect } from "react";
import { Settings, Grid3X3, Heart, LogOut } from "lucide-react";
import { Auth, Discover, type UserData, type VideoData, formatCount, videoUrl } from "../lib/api";

interface Props {
  user: UserData;
  onLogout: () => void;
}

export default function ProfilePage({ user: initialUser, onLogout }: Props) {
  const [user, setUser] = useState(initialUser);
  const [videos, setVideos] = useState<VideoData[]>([]);
  const [activeTab, setActiveTab] = useState<"videos" | "liked">("videos");

  useEffect(() => {
    Auth.me().then(setUser).catch(() => {});
    Discover.search("").then((v) => setVideos(v.filter((x) => x && x.video_id))).catch(() => {});
  }, []);

  return (
    <div className="h-full bg-black overflow-y-auto pb-20 scrollbar-hide">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <span className="text-lg font-bold">{user.username}</span>
        <div className="flex items-center gap-3">
          <button className="p-1"><Settings className="w-5 h-5 text-white" /></button>
          <button onClick={onLogout} className="p-1"><LogOut className="w-5 h-5 text-white/60" /></button>
        </div>
      </div>

      {/* Avatar & Stats */}
      <div className="flex flex-col items-center pt-4 pb-2">
        <div className="w-24 h-24 rounded-full bg-neutral-800 overflow-hidden border-2 border-neutral-700">
          <img
            src={user.avatar}
            alt={user.username}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = `data:image/svg+xml,${encodeURIComponent(
                `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96"><rect fill="#333" width="96" height="96"/><text x="48" y="58" text-anchor="middle" fill="white" font-size="36">${user.username[0]?.toUpperCase()}</text></svg>`
              )}`;
            }}
          />
        </div>
        <h2 className="text-base font-semibold mt-3">@{user.username}</h2>
        {user.bio && <p className="text-xs text-neutral-400 mt-1">{user.bio}</p>}
      </div>

      {/* Stats row */}
      <div className="flex justify-center gap-8 py-4">
        <StatItem value={formatCount(user.following_count)} label="Following" />
        <StatItem value={formatCount(user.follower_count)} label="Followers" />
        <StatItem value={formatCount(user.total_likes)} label="Likes" />
      </div>

      {/* Edit profile button */}
      <div className="flex justify-center gap-2 pb-4 px-6">
        <button className="flex-1 py-2 bg-[#2a2a2a] rounded-md text-sm font-medium hover:bg-[#3a3a3a] transition-colors">
          Edit profile
        </button>
        <button className="flex-1 py-2 bg-[#2a2a2a] rounded-md text-sm font-medium hover:bg-[#3a3a3a] transition-colors">
          Share profile
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-neutral-800">
        <button
          onClick={() => setActiveTab("videos")}
          className={`flex-1 flex justify-center py-3 ${activeTab === "videos" ? "border-b-2 border-white" : ""}`}
        >
          <Grid3X3 className={`w-5 h-5 ${activeTab === "videos" ? "text-white" : "text-neutral-500"}`} />
        </button>
        <button
          onClick={() => setActiveTab("liked")}
          className={`flex-1 flex justify-center py-3 ${activeTab === "liked" ? "border-b-2 border-white" : ""}`}
        >
          <Heart className={`w-5 h-5 ${activeTab === "liked" ? "text-white" : "text-neutral-500"}`} />
        </button>
      </div>

      {/* Video grid */}
      <div className="grid grid-cols-3 gap-0.5">
        {videos.slice(0, activeTab === "liked" ? 9 : 18).map((v) => (
          <div key={v.video_id} className="relative aspect-[9/16] bg-neutral-900 overflow-hidden">
            <video
              src={videoUrl(v.url)}
              className="w-full h-full object-cover"
              muted
              preload="metadata"
              playsInline
            />
            <div className="absolute bottom-1 left-1 flex items-center gap-0.5">
              <span className="text-[10px] text-white font-medium drop-shadow">&#9655; {formatCount(v.stats.views)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <p className="text-lg font-bold">{value}</p>
      <p className="text-[11px] text-neutral-400">{label}</p>
    </div>
  );
}
