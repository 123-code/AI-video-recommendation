"use client";

import { useState, useEffect, useRef } from "react";
import { X, Heart, Send } from "lucide-react";
import { Video as VideoAPI, type CommentData, timeAgo } from "../lib/api";

interface Props {
  videoId: string;
  onClose: () => void;
}

export default function CommentSheet({ videoId, onClose }: Props) {
  const [comments, setComments] = useState<CommentData[]>([]);
  const [total, setTotal] = useState(0);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [closing, setClosing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    VideoAPI.getComments(videoId).then((res) => {
      setComments(res.comments);
      setTotal(res.total);
    });
  }, [videoId]);

  const handleClose = () => {
    setClosing(true);
    setTimeout(onClose, 300);
  };

  const handleSend = async () => {
    if (!text.trim() || sending) return;
    setSending(true);
    try {
      const comment = await VideoAPI.comment(videoId, text.trim());
      setComments((prev) => [comment, ...prev]);
      setTotal((t) => t + 1);
      setText("");
    } catch (e) {
      console.error("Comment error:", e);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50" onClick={(e) => { if (e.target === backdropRef.current) handleClose(); }}>
      <div ref={backdropRef} className="absolute inset-0 bg-black/60 fade-in" />
      <div className={`absolute bottom-0 left-0 right-0 bg-[#1e1e1e] rounded-t-xl max-h-[70vh] flex flex-col ${closing ? "slide-down" : "slide-up"}`}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-700">
          <span className="text-[15px] font-semibold">{total} comments</span>
          <button onClick={handleClose} className="p-1">
            <X className="w-5 h-5 text-neutral-400" />
          </button>
        </div>

        {/* Comments list */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-5 scrollbar-hide">
          {comments.length === 0 && (
            <p className="text-neutral-500 text-center text-sm py-8">No comments yet. Be the first!</p>
          )}
          {comments.map((c) => (
            <div key={c.comment_id} className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-neutral-700 flex-shrink-0 overflow-hidden">
                <img
                  src={c.avatar}
                  alt={c.username}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = `data:image/svg+xml,${encodeURIComponent(
                      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect fill="#444" width="32" height="32"/><text x="16" y="21" text-anchor="middle" fill="white" font-size="14">${c.username[0]?.toUpperCase()}</text></svg>`
                    )}`;
                  }}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] text-neutral-400 font-medium">{c.username}</span>
                  <span className="text-[11px] text-neutral-600">{timeAgo(c.timestamp)}</span>
                </div>
                <p className="text-[14px] text-white/90 mt-0.5 leading-snug">{c.text}</p>
                <div className="flex items-center gap-1 mt-1.5">
                  <Heart className="w-3.5 h-3.5 text-neutral-500" />
                  <span className="text-[11px] text-neutral-500">{c.likes > 0 ? c.likes : ""}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <div className="border-t border-neutral-700 px-4 py-3 flex items-center gap-3">
          <input
            ref={inputRef}
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSend(); }}
            placeholder="Add comment..."
            className="flex-1 bg-neutral-800 rounded-full px-4 py-2 text-sm text-white placeholder-neutral-500 outline-none"
          />
          <button
            onClick={handleSend}
            disabled={!text.trim() || sending}
            className="text-[#fe2c55] disabled:text-neutral-600 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
