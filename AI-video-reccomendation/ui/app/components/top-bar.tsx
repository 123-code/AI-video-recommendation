"use client";

interface Props {
  activeTab: "foryou" | "following";
  onTabChange: (tab: "foryou" | "following") => void;
}

export default function TopBar({ activeTab, onTabChange }: Props) {
  return (
    <div className="absolute top-0 left-0 right-0 z-30 pointer-events-none">
      <div className="video-gradient-top pt-2 pb-6">
        <div className="flex items-center justify-center gap-6 pointer-events-auto pt-3">
          <button
            onClick={() => onTabChange("following")}
            className={`text-[16px] font-semibold transition-colors relative pb-1 ${
              activeTab === "following" ? "text-white" : "text-white/50"
            }`}
          >
            Following
            {activeTab === "following" && (
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-[3px] bg-white rounded-full" />
            )}
          </button>
          <span className="text-white/20">|</span>
          <button
            onClick={() => onTabChange("foryou")}
            className={`text-[16px] font-semibold transition-colors relative pb-1 ${
              activeTab === "foryou" ? "text-white" : "text-white/50"
            }`}
          >
            For You
            {activeTab === "foryou" && (
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-[3px] bg-white rounded-full" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
