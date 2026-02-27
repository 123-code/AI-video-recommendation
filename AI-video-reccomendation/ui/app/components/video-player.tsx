"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { Heart, Volume2, VolumeX } from "lucide-react";
import { type VideoData, videoUrl } from "../lib/api";

interface Props {
  video: VideoData;
  active: boolean;
  muted: boolean;
  onDoubleTap: () => void;
  onMuteToggle: () => void;
}

export default function VideoPlayer({ video, active, muted, onDoubleTap, onMuteToggle }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [paused, setPaused] = useState(false);
  const [showHeart, setShowHeart] = useState(false);
  const [heartPos, setHeartPos] = useState({ x: 0, y: 0 });
  const lastTapRef = useRef(0);
  const heartTimeoutRef = useRef<NodeJS.Timeout>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const el = videoRef.current;
    if (!el) return;
    if (active && !paused) {
      el.play().catch(() => {});
    } else {
      el.pause();
    }
  }, [active, paused]);

  useEffect(() => {
    const el = videoRef.current;
    if (el) el.muted = muted;
  }, [muted]);

  useEffect(() => {
    setPaused(false);
    setProgress(0);
  }, [video.video_id]);

  useEffect(() => {
    const el = videoRef.current;
    if (!el) return;
    const onTime = () => {
      if (el.duration) setProgress(el.currentTime / el.duration);
    };
    el.addEventListener("timeupdate", onTime);
    return () => el.removeEventListener("timeupdate", onTime);
  }, []);

  const handleTap = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    const target = e.target as HTMLElement;
    if (target.closest("button")) return;

    const now = Date.now();
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    let clientX: number, clientY: number;
    if ("touches" in e) {
      clientX = e.changedTouches?.[0]?.clientX ?? rect.width / 2;
      clientY = e.changedTouches?.[0]?.clientY ?? rect.height / 2;
    } else {
      clientX = e.clientX;
      clientY = e.clientY;
    }

    if (now - lastTapRef.current < 300) {
      setHeartPos({ x: clientX - rect.left, y: clientY - rect.top });
      setShowHeart(true);
      if (heartTimeoutRef.current) clearTimeout(heartTimeoutRef.current);
      heartTimeoutRef.current = setTimeout(() => setShowHeart(false), 1000);
      onDoubleTap();
      lastTapRef.current = 0;
    } else {
      lastTapRef.current = now;
      setTimeout(() => {
        if (lastTapRef.current === now) setPaused((p) => !p);
      }, 300);
    }
  }, [onDoubleTap]);

  return (
    <div className="absolute inset-0 bg-black" onClick={handleTap}>
      <video
        ref={videoRef}
        src={videoUrl(video.url)}
        className="w-full h-full object-cover"
        loop
        muted={muted}
        playsInline
        preload="auto"
      />

      {/* Pause icon */}
      {paused && active && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-16 h-16 bg-black/40 rounded-full flex items-center justify-center backdrop-blur-sm">
            <svg className="w-8 h-8 text-white ml-1" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        </div>
      )}

      {/* Double-tap heart */}
      {showHeart && (
        <div className="absolute pointer-events-none heart-animation" style={{ left: heartPos.x - 40, top: heartPos.y - 40 }}>
          <Heart className="w-20 h-20 text-[#fe2c55] fill-[#fe2c55] drop-shadow-lg" />
        </div>
      )}

      {/* Sound toggle */}
      <button
        onClick={(e) => { e.stopPropagation(); onMuteToggle(); }}
        className="absolute top-14 right-3 z-20 w-8 h-8 bg-black/40 rounded-full flex items-center justify-center backdrop-blur-sm"
      >
        {muted ? <VolumeX className="w-4 h-4 text-white/80" /> : <Volume2 className="w-4 h-4 text-white/80" />}
      </button>

      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-white/10">
        <div className="h-full bg-white/60 transition-[width] duration-200" style={{ width: `${progress * 100}%` }} />
      </div>
    </div>
  );
}
