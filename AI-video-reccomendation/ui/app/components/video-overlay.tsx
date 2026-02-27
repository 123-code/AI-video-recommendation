"use client";

import { Music } from "lucide-react";
import { type VideoData } from "../lib/api";

interface Props {
  video: VideoData;
}

export default function VideoOverlay({ video }: Props) {
  return (
    <div className="absolute bottom-0 left-0 right-16 pointer-events-none pb-20">
      <div className="video-gradient-bottom px-4 pt-24 pb-4 space-y-2">
        {video.is_generated && (
          <div className="inline-flex items-center gap-1 px-2 py-0.5 bg-gradient-to-r from-purple-500/80 to-pink-500/80 rounded-full text-[10px] font-medium backdrop-blur-sm mb-1">
            <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61z"/></svg>
            Made for you
          </div>
        )}
        <div className="flex items-center gap-1">
          <span className="font-bold text-[15px]">@{video.creator.username}</span>
          {video.creator.is_verified && (
            <svg className="w-4 h-4 text-[#20d5ec]" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          )}
        </div>

        <p className="text-[13px] leading-snug line-clamp-2 text-white/90">
          {video.description}
        </p>

        <div className="flex items-center gap-2 overflow-hidden">
          <Music className="w-3.5 h-3.5 flex-shrink-0" />
          <div className="overflow-hidden whitespace-nowrap">
            <span className="inline-block animate-marquee text-[13px] text-white/80">
              {video.music.name} — {video.music.artist}
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
              {video.music.name} — {video.music.artist}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
