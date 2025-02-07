// app/page.tsx
import TikTokFeed from "./components/tiktok-feed"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-white text-black">
      <div className="w-full max-w-md">
        <TikTokFeed />
      </div>
    </main>
  )
}
