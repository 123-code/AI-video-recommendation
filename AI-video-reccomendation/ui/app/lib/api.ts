const API_BASE = "http://127.0.0.1:5050";

function getHeaders(): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("tiktok_token");
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const userId = localStorage.getItem("tiktok_user_id");
    if (userId) headers["X-User-Id"] = userId;
  }
  return headers;
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...options?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

export interface VideoCreator {
  user_id: string;
  username: string;
  display_name: string;
  avatar: string;
  is_verified: boolean;
}

export interface VideoData {
  video_id: string;
  filename: string;
  url: string;
  creator: VideoCreator;
  description: string;
  music: { name: string; artist: string };
  category: string;
  tags: string[];
  stats: { views: number; likes: number; comments: number; shares: number };
  duration: number;
  created_at: number;
  is_liked?: boolean;
  is_following?: boolean;
  is_generated?: boolean;
}

export interface UserData {
  user_id: string;
  username: string;
  display_name: string;
  avatar: string;
  bio: string;
  follower_count: number;
  following_count: number;
  is_verified: boolean;
  total_likes: number;
  is_following?: boolean;
}

export interface CommentData {
  comment_id: string;
  user_id: string;
  username: string;
  avatar: string;
  text: string;
  likes: number;
  timestamp: number;
}

export const Auth = {
  register: (username: string) =>
    api<{ token: string; user: UserData }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username }),
    }),
  login: (username: string) =>
    api<{ token: string; user: UserData }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username }),
    }),
  me: () => api<UserData>("/api/auth/me"),
};

export const Feed = {
  forYou: (count = 5) => api<VideoData[]>(`/api/feed/foryou?count=${count}`),
  following: (count = 5) => api<VideoData[]>(`/api/feed/following?count=${count}`),
};

export const Video = {
  like: (videoId: string) =>
    api<{ is_liked: boolean; likes: number; likes_formatted: string }>(
      `/api/video/${videoId}/like`,
      { method: "POST" }
    ),
  comment: (videoId: string, text: string) =>
    api<CommentData>(`/api/video/${videoId}/comment`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  getComments: (videoId: string, page = 0) =>
    api<{ comments: CommentData[]; total: number; has_more: boolean }>(
      `/api/video/${videoId}/comments?page=${page}`
    ),
  share: (videoId: string) =>
    api<{ shares: number }>(`/api/video/${videoId}/share`, { method: "POST" }),
  view: (videoId: string, watchTime = 0) =>
    api<{ views: number }>(`/api/video/${videoId}/view`, {
      method: "POST",
      body: JSON.stringify({ watch_time: watchTime }),
    }),
};

export const User = {
  get: (userId: string) => api<UserData>(`/api/user/${userId}`),
  follow: (userId: string) =>
    api<{ is_following: boolean; follower_count: number }>(
      `/api/user/${userId}/follow`,
      { method: "POST" }
    ),
};

export const Discover = {
  search: (q = "") => api<VideoData[]>(`/api/discover?q=${encodeURIComponent(q)}`),
};

export function formatCount(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return String(n);
}

export function timeAgo(ts: number): string {
  const seconds = Math.floor(Date.now() / 1000 - ts);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d`;
  const weeks = Math.floor(days / 7);
  return `${weeks}w`;
}

export function videoUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export const Generation = {
  status: () => api<Record<string, unknown>>("/api/generation/status"),
  profile: (userId: string) => api<Record<string, unknown>>(`/api/generation/profile/${userId}`),
  trigger: () => api<Record<string, unknown>>("/api/generation/trigger", { method: "POST" }),
  preview: () => api<VideoData[]>("/api/generation/preview"),
};
