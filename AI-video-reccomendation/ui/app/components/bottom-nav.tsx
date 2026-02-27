"use client";

import { Home, Search, Plus, MessageSquare, User } from "lucide-react";

export default function BottomNav() {
  return (
    <div className="absolute bottom-0 left-0 right-0 z-30 bg-black/90 backdrop-blur-sm border-t border-white/5">
      <div className="flex items-center justify-around py-2 pb-3">
        <NavItem icon={<Home className="w-6 h-6" />} label="Home" active />
        <NavItem icon={<Search className="w-6 h-6" />} label="Discover" />
        <div className="px-2">
          <div className="relative w-12 h-8 flex items-center justify-center">
            <div className="absolute inset-0 rounded-lg bg-[#25f4ee] translate-x-[-3px]" />
            <div className="absolute inset-0 rounded-lg bg-[#fe2c55] translate-x-[3px]" />
            <div className="relative bg-white rounded-lg w-full h-full flex items-center justify-center">
              <Plus className="w-5 h-5 text-black" strokeWidth={2.5} />
            </div>
          </div>
        </div>
        <NavItem icon={<MessageSquare className="w-6 h-6" />} label="Inbox" />
        <NavItem icon={<User className="w-6 h-6" />} label="Profile" />
      </div>
    </div>
  );
}

function NavItem({ icon, label, active = false }: { icon: React.ReactNode; label: string; active?: boolean }) {
  return (
    <button className="flex flex-col items-center gap-0.5 min-w-[48px]">
      <div className={active ? "text-white" : "text-white/50"}>{icon}</div>
      <span className={`text-[10px] ${active ? "text-white" : "text-white/50"}`}>{label}</span>
    </button>
  );
}
