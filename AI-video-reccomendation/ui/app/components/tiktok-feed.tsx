"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Feed, Video as VideoAPI, type VideoData, type UserData } from "../lib/api";
import VideoPlayer from "./video-player";
import ActionSidebar from "./action-sidebar";
import VideoOverlay from "./video-overlay";
import CommentSheet from "./comment-sheet";
import TopBar from "./top-bar";
import BottomNav from "./bottom-nav";

interface Props {
  user: UserData;
}

export default function TikTokFeed({ user: _user }: Props) {
  const [videos, setVideos] = useState<VideoData[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<"foryou" | "following">("foryou");
  const [commentVideoId, setCommentVideoId] = useState<string | null>(null);
  const [isFetching, setIsFetching] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const lastFetchRef = useRef(0);
  void _user;

  const fetchVideos = useCallback(async (tab: "foryou" | "following", append = false) => {
    if (isFetching) return;
    setIsFetching(true);
    try {
      const data = tab === "following" ? await Feed.following(5) : await Feed.forYou(5);
      const valid = data.filter((v) => v && v.video_id);
      if (append) {
        setVideos((prev) => {
          const existingIds = new Set(prev.map((v) => v.video_id));
          const newVids = valid.filter((v) => !existingIds.has(v.video_id));
          return [...prev, ...newVids];
        });
      } else {
        setVideos(valid);
        setCurrentIndex(0);
        if (containerRef.current) containerRef.current.scrollTop = 0;
      }
    } catch (e) {
      console.error("Feed fetch error:", e);
    } finally {
      setIsFetching(false);
    }
  }, [isFetching]);

  useEffect(() => {
    fetchVideos(activeTab);
  }, [activeTab]);

  useEffect(() => {
    if (videos.length > 0 && currentIndex >= videos.length - 2 && !isFetching) {
      const now = Date.now();
      if (now - lastFetchRef.current > 1000) {
        lastFetchRef.current = now;
        fetchVideos(activeTab, true);
      }
    }
  }, [currentIndex, videos.length, isFetching, activeTab]);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    const h = container.clientHeight;
    const newIdx = Math.round(container.scrollTop / h);
    if (newIdx !== currentIndex && newIdx >= 0 && newIdx < videos.length) {
      const prev = videos[currentIndex];
      if (prev) {
        VideoAPI.view(prev.video_id, 0).catch(() => {});
      }
      setCurrentIndex(newIdx);
    }
  }, [currentIndex, videos]);

  const handleLike = useCallback(async (videoId: string) => {
    try {
      const res = await VideoAPI.like(videoId);
      setVideos((prev) =>
        prev.map((v) =>
          v.video_id === videoId
            ? { ...v, is_liked: res.is_liked, stats: { ...v.stats, likes: res.likes } }
            : v
        )
      );
    } catch (e) {
      console.error("Like error:", e);
    }
  }, []);

  const handleTabChange = useCallback((tab: "foryou" | "following") => {
    if (tab !== activeTab) {
      setActiveTab(tab);
    }
  }, [activeTab]);

  return (
    <div className="h-screen w-screen bg-black relative">
      <TopBar activeTab={activeTab} onTabChange={handleTabChange} />

      <div
        ref={containerRef}
        className="snap-container scrollbar-hide"
        onScroll={handleScroll}
      >
        {videos.map((video, index) => (
          <div key={`${video.video_id}-${index}`} className="snap-item">
            <VideoPlayer
              video={video}
              active={index === currentIndex}
              onDoubleTap={() => {
                if (!video.is_liked) handleLike(video.video_id);
              }}
            />
            <VideoOverlay video={video} />
            <ActionSidebar
              video={video}
              onLike={() => handleLike(video.video_id)}
              onComment={() => setCommentVideoId(video.video_id)}
              onShare={() => VideoAPI.share(video.video_id).catch(() => {})}
            />
          </div>
        ))}

        {videos.length === 0 && !isFetching && (
          <div className="snap-item flex items-center justify-center">
            <p className="text-neutral-500 text-lg">No videos yet</p>
          </div>
        )}

        {isFetching && videos.length === 0 && (
          <div className="snap-item flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-white/20 border-t-[#fe2c55] rounded-full animate-spin" />
          </div>
        )}
      </div>

      <BottomNav />

      {commentVideoId && (
        <CommentSheet
          videoId={commentVideoId}
          onClose={() => setCommentVideoId(null)}
        />
      )}
    </div>
  );
}
