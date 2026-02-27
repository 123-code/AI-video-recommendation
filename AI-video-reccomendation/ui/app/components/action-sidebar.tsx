"use client";

import { useState } from "react";
import { Heart, MessageCircle, Bookmark, Share2 } from "lucide-react";
import { type VideoData, formatCount } from "../lib/api";

interface Props {
  video: VideoData;
  onLike: () => void;
  onComment: () => void;
  onShare: () => void;
  onFollow: () => void;
}

export default function ActionSidebar({ video, onLike, onComment, onShare, onFollow }: Props) {
  const [likeAnim, setLikeAnim] = useState(false);

  const handleLike = () => {
    setLikeAnim(true);
    setTimeout(() => setLikeAnim(false), 400);
    onLike();
  };

  return (
    <div className="absolute right-2 bottom-32 flex flex-col items-center gap-5 z-10">
      {/* Creator avatar with follow button */}
      <div className="relative mb-2">
        <div className="w-12 h-12 rounded-full border-2 border-white overflow-hidden bg-neutral-800">
          <img
            src={video.creator.avatar}
            alt={video.creator.username}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = `data:image/svg+xml,${encodeURIComponent(
                `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect fill="#333" width="40" height="40"/><text x="20" y="25" text-anchor="middle" fill="white" font-size="16">${video.creator.username[0]?.toUpperCase()}</text></svg>`
              )}`;
            }}
          />
        </div>
        {!video.is_following && (
          <button
            onClick={onFollow}
            className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-5 h-5 bg-[#fe2c55] rounded-full flex items-center justify-center shadow-lg"
          >
            <span className="text-white text-xs font-bold leading-none">+</span>
          </button>
        )}
        {video.is_following && (
          <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-5 h-5 bg-neutral-600 rounded-full flex items-center justify-center">
            <span className="text-white text-[9px] font-bold">&#10003;</span>
          </div>
        )}
      </div>

      {/* Like */}
      <button onClick={handleLike} className="flex flex-col items-center gap-1">
        <div className={`w-11 h-11 flex items-center justify-center ${likeAnim ? "like-bounce" : ""}`}>
          <Heart className={`w-7 h-7 ${video.is_liked ? "text-[#fe2c55] fill-[#fe2c55]" : "text-white"}`} strokeWidth={2} />
        </div>
        <span className="text-[11px] text-white/90 font-medium">{formatCount(video.stats.likes)}</span>
      </button>

      {/* Comment */}
      <button onClick={onComment} className="flex flex-col items-center gap-1">
        <div className="w-11 h-11 flex items-center justify-center">
          <MessageCircle className="w-7 h-7 text-white" strokeWidth={2} />
        </div>
        <span className="text-[11px] text-white/90 font-medium">{formatCount(video.stats.comments)}</span>
      </button>

      {/* Bookmark */}
      <button className="flex flex-col items-center gap-1">
        <div className="w-11 h-11 flex items-center justify-center">
          <Bookmark className="w-7 h-7 text-white" strokeWidth={2} />
        </div>
        <span className="text-[11px] text-white/90 font-medium">Save</span>
      </button>

      {/* Share */}
      <button onClick={onShare} className="flex flex-col items-center gap-1">
        <div className="w-11 h-11 flex items-center justify-center">
          <Share2 className="w-7 h-7 text-white" strokeWidth={2} />
        </div>
        <span className="text-[11px] text-white/90 font-medium">{formatCount(video.stats.shares)}</span>
      </button>

      {/* Music disc */}
      <div className="mt-2 w-10 h-10 rounded-full bg-neutral-900 border-2 border-neutral-700 animate-spin-slow flex items-center justify-center overflow-hidden">
        <div className="w-4 h-4 rounded-full bg-neutral-600 border border-neutral-500" />
      </div>
    </div>
  );
}
