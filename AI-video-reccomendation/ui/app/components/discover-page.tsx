"use client";

import { useState, useEffect } from "react";
import { Search } from "lucide-react";
import { Discover, type VideoData, formatCount, videoUrl } from "../lib/api";

const CATEGORY_CHIPS = [
  "All", "Nature", "Ocean", "Urban", "Fractal", "Generative",
  "Gradient", "Psychedelic", "Abstract", "Cinematic", "Travel",
  "Animals", "Weather", "Space", "Satisfying", "Retro",
];

export default function DiscoverPage() {
  const [query, setQuery] = useState("");
  const [videos, setVideos] = useState<VideoData[]>([]);
  const [activeChip, setActiveChip] = useState("All");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchVideos("");
  }, []);

  const fetchVideos = async (q: string) => {
    setLoading(true);
    try {
      const data = await Discover.search(q);
      setVideos(data.filter((v) => v && v.video_id));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleChip = (chip: string) => {
    setActiveChip(chip);
    const q = chip === "All" ? "" : chip.toLowerCase();
    setQuery(chip === "All" ? "" : chip);
    fetchVideos(q);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveChip("All");
    fetchVideos(query);
  };

  return (
    <div className="h-full bg-black overflow-y-auto pb-20 scrollbar-hide">
      <div className="sticky top-0 z-10 bg-black/95 backdrop-blur-sm px-4 pt-4 pb-2">
        <form onSubmit={handleSearch} className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search videos, categories, creators..."
            className="w-full pl-10 pr-4 py-2.5 bg-[#1e1e1e] rounded-xl text-sm text-white placeholder-neutral-500 outline-none focus:ring-1 focus:ring-neutral-600"
          />
        </form>

        <div className="flex gap-2 mt-3 overflow-x-auto scrollbar-hide pb-2">
          {CATEGORY_CHIPS.map((chip) => (
            <button
              key={chip}
              onClick={() => handleChip(chip)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                activeChip === chip
                  ? "bg-white text-black"
                  : "bg-[#2a2a2a] text-white/70 hover:bg-[#3a3a3a]"
              }`}
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 border-white/20 border-t-[#fe2c55] rounded-full animate-spin" />
        </div>
      )}

      <div className="grid grid-cols-2 gap-1 px-1 mt-1">
        {videos.map((v) => (
          <div key={v.video_id} className="relative aspect-[9/16] bg-neutral-900 rounded-sm overflow-hidden group">
            <video
              src={videoUrl(v.url)}
              className="w-full h-full object-cover"
              muted
              loop
              playsInline
              preload="metadata"
              onMouseEnter={(e) => (e.target as HTMLVideoElement).play().catch(() => {})}
              onMouseLeave={(e) => { const el = e.target as HTMLVideoElement; el.pause(); el.currentTime = 0; }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent pointer-events-none" />
            <div className="absolute bottom-2 left-2 right-2 pointer-events-none">
              <p className="text-[11px] text-white/90 font-medium line-clamp-1">@{v.creator.username}</p>
              <p className="text-[10px] text-white/60 line-clamp-1 mt-0.5">{v.description}</p>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-[10px] text-white/50">&#9829; {formatCount(v.stats.likes)}</span>
                <span className="text-[10px] text-white/50">&#9655; {formatCount(v.stats.views)}</span>
              </div>
            </div>
            <div className="absolute top-2 right-2 px-1.5 py-0.5 bg-black/50 rounded text-[9px] text-white/70 pointer-events-none">
              {v.category}
            </div>
          </div>
        ))}
      </div>

      {!loading && videos.length === 0 && (
        <p className="text-center text-neutral-500 text-sm py-12">No results found</p>
      )}
    </div>
  );
}
