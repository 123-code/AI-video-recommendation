"use client"

import { useState, type React } from "react"
import { Heart, MessageCircle, Share2 } from "lucide-react"
import { Button } from "@/components/ui/button"

const mockVideos = [
  {
    id: 1,
    videoUrl: "/placeholder.svg?height=640&width=360",
    user: "@user1",
    description: "This is a cool video #trending",
    likes: 1234,
    comments: 56,
    shares: 78,
  },
  {
    id: 2,
    videoUrl: "/placeholder.svg?height=640&width=360",
    user: "@user2",
    description: "Another awesome video #fyp",
    likes: 5678,
    comments: 90,
    shares: 12,
  },
  // Add more mock videos as needed
]

export default function TikTokFeed() {
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0)
  const [showComments, setShowComments] = useState(false)

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
      {mockVideos.map((video, index) => (
        <div key={video.id} className="h-full w-full snap-start relative">
          <video
            src={video.videoUrl}
            className="h-full w-full object-cover"
            loop
            muted
            playsInline
            autoPlay={index === currentVideoIndex}
          />
          <div className="absolute bottom-4 left-4 right-12">
            <p className="font-bold">{video.user}</p>
            <p className="text-sm">{video.description}</p>
          </div>
          <div className="absolute bottom-20 right-2 flex flex-col items-center space-y-4">
            <Button variant="ghost" size="icon" className="rounded-full bg-gray-800 text-white">
              <Heart className="h-6 w-6" />
            </Button>
            <span className="text-xs">{video.likes}</span>
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full bg-gray-800 text-white"
              onClick={() => setShowComments(!showComments)}
            >
              <MessageCircle className="h-6 w-6" />
            </Button>
            <span className="text-xs">{video.comments}</span>
            <Button variant="ghost" size="icon" className="rounded-full bg-gray-800 text-white">
              <Share2 className="h-6 w-6" />
            </Button>
            <span className="text-xs">{video.shares}</span>
          </div>
          {showComments && (
            <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gray-900 bg-opacity-90 p-4 overflow-y-auto">
              <h3 className="text-lg font-bold mb-2">Comments</h3>
              <div className="space-y-2">
                <p>
                  <span className="font-bold">@commenter1:</span> Great video!
                </p>
                <p>
                  <span className="font-bold">@commenter2:</span> Love this content!
                </p>
                <p>
                  <span className="font-bold">@commenter3:</span> Keep it up!
                </p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

