// tiktok-feed.tsx
"use client"
import { useState, useEffect } from "react"
import { Heart, MessageCircle, Share2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import VideoPlayer from './video-player';

export default function TikTokFeed() {
  const [videos, setVideos] = useState([]);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0)
  const [showComments, setShowComments] = useState(false)

  useEffect(() => {
    fetch('http://127.0.0.1:5000/random_videos')
      .then(response => response.json())
      .then(data => setVideos(data));
  }, []);
 
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget
    const scrollPosition = container.scrollTop
    const videoHeight = container.clientHeight
    const newIndex = Math.round(scrollPosition / videoHeight)
    if (newIndex !== currentVideoIndex) {
      setCurrentVideoIndex(newIndex)
    }
  }

  return (
    <div className="h-[100vh] overflow-y-scroll snap-y snap-mandatory" onScroll={handleScroll}>
      {videos.map((video, index) => (
        <div key={index} className="h-full w-full snap-start relative">
          <VideoPlayer videoSrc={video.file_path} />
          <div className="absolute bottom-4 left-4 right-12">
            <p className="font-bold">username</p>
            <p className="text-sm">description</p>
          </div>
          <div className="absolute bottom-20 right-2 flex flex-col items-center space-y-4">
            <Button variant="ghost" size="icon" className="rounded-full bg-gray-800 text-white">
              <Heart className="h-6 w-6" />
            </Button>
            <span className="text-xs">likes</span>
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full bg-gray-800 text-white"
              onClick={() => setShowComments(!showComments)}
            >
              <MessageCircle className="h-6 w-6" />
            </Button>
            <span className="text-xs">comments</span>
            <Button variant="ghost" size="icon" className="rounded-full bg-gray-800 text-white">
              <Share2 className="h-6 w-6" />
            </Button>
            <span className="text-xs">shares</span>
          </div>
          {showComments && (
            <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gray-900 bg-opacity-90 p-4 overflow-y-auto">
              <h3 className="text-lg font-bold mb-2">Comments</h3>
              <div className="space-y-2">
                <p>
                  <span className="font-bold">commenter1:</span> Great video!
                </p>
                <p>
                  <span className="font-bold">commenter2:</span> Love this content!
                </p>
                <p>
                  <span className="font-bold">commenter3:</span> Keep it up!
                </p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
