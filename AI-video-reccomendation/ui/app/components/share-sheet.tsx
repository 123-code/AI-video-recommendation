"use client";

import { useRef, useState } from "react";
import { X, Link2, MessageCircle, Send, Download, Flag, Copy } from "lucide-react";

interface Props {
  videoId: string;
  onClose: () => void;
  onToast: (msg: string) => void;
}

const SHARE_OPTIONS = [
  { icon: <Send className="w-6 h-6" />, label: "Message", color: "bg-blue-500" },
  { icon: <Copy className="w-6 h-6" />, label: "Copy link", color: "bg-neutral-600" },
  { icon: <MessageCircle className="w-6 h-6" />, label: "WhatsApp", color: "bg-green-500" },
  { icon: <Link2 className="w-6 h-6" />, label: "Embed", color: "bg-purple-500" },
  { icon: <Download className="w-6 h-6" />, label: "Save video", color: "bg-teal-500" },
  { icon: <Flag className="w-6 h-6" />, label: "Report", color: "bg-red-500/70" },
];

export default function ShareSheet({ videoId, onClose, onToast }: Props) {
  const [closing, setClosing] = useState(false);
  const backdropRef = useRef<HTMLDivElement>(null);

  const handleClose = () => {
    setClosing(true);
    setTimeout(onClose, 300);
  };

  const handleOption = (label: string) => {
    if (label === "Copy link") {
      navigator.clipboard?.writeText(`https://tiktok.com/@video/${videoId}`).catch(() => {});
      onToast("Link copied");
    } else {
      onToast(`${label} coming soon`);
    }
    handleClose();
  };

  return (
    <div className="fixed inset-0 z-50" onClick={(e) => { if (e.target === backdropRef.current) handleClose(); }}>
      <div ref={backdropRef} className="absolute inset-0 bg-black/60 fade-in" />
      <div className={`absolute bottom-0 left-0 right-0 bg-[#1e1e1e] rounded-t-xl ${closing ? "slide-down" : "slide-up"}`}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-700">
          <span className="text-[15px] font-semibold">Share to</span>
          <button onClick={handleClose} className="p-1"><X className="w-5 h-5 text-neutral-400" /></button>
        </div>

        <div className="grid grid-cols-4 gap-4 px-6 py-5">
          {SHARE_OPTIONS.map((opt) => (
            <button key={opt.label} onClick={() => handleOption(opt.label)} className="flex flex-col items-center gap-2">
              <div className={`w-12 h-12 ${opt.color} rounded-full flex items-center justify-center text-white`}>
                {opt.icon}
              </div>
              <span className="text-[11px] text-neutral-300">{opt.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
