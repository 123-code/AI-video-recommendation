"use client";

import { useState, useEffect } from "react";
import { Heart, MessageCircle, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import VideoPlayer from "./video-player";

interface Video {
  video_id: string;
  metadata: {
    file_path: string;
    genre?: string; // Add genre and make it optional
    title?: string; // Add title and make it optional
  };
  // Add other properties as needed based on your API response
}

export default function TikTokFeed() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [showComments, setShowComments] = useState(false);
  const [videoTime, setVideoTime] = useState<{ [videoId: string]: number }>({});
  const [recommendedVideos, setRecommendedVideos] = useState<Video[]>([]);
  const [interactionRecorded, setInteractionRecorded] = useState(false);
  const [isFetching, setIsFetching] = useState(false); // Track if a fetch is in progress

  useEffect(() => {
    fetchNextVideo(); // Initial fetch for videos
  }, []);

  const fetchNextVideo = () => {
    if (isFetching) return; // Prevent multiple fetches
    setIsFetching(true);

    fetch("http://127.0.0.1:5000/next_video?user_id=user1")
      .then((res) => res.json())
      .then((data) => {
        setRecommendedVideos((prevVideos) => [...prevVideos, data]); // Append new videos
        setIsFetching(false);
      })
      .catch((error) => {
        console.error("Error fetching videos:", error);
        setIsFetching(false);
      });
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    const scrollPosition = container.scrollTop;
    const videoHeight = container.clientHeight;
    const newIndex = Math.round(scrollPosition / videoHeight);

    if (newIndex !== currentVideoIndex) {
      // Send time spent on previous video to server
      if (recommendedVideos.length > 0 && currentVideoIndex < recommendedVideos.length) {
        const videoId = recommendedVideos[currentVideoIndex].video_id;
        const timeWatched = videoTime[videoId] || 0; // Default to 0 if undefined

        if (videoId && timeWatched > 0) {
          fetch(`http://127.0.0.1:5000/update_interaction`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id: "user1",
              video_id: videoId,
              interaction_type: "watch_time",
              value: timeWatched,
            }),
          })
            .then(() => {
               setInteractionRecorded(false);
              // Only fetch new recommendations after interaction is updated
              fetchNextVideo();
            })
            .catch((error) => console.error("Error updating interaction:", error));
        }
      }

      setCurrentVideoIndex(newIndex);
      setInteractionRecorded(false); // Reset interaction flag when scrolling
    }
  };


  const handleTimeUpdate = (videoIndex: number, currentTime: number) => {
    if (recommendedVideos.length > 0 && videoIndex < recommendedVideos.length) {
      const videoId = recommendedVideos[videoIndex].video_id;
      setVideoTime((prevVideoTime) => ({
        ...prevVideoTime,
        [videoId]: currentTime,
      }));
    }
  };

  const handleVideoInteraction = (videoIndex: number) => {
     if (recommendedVideos.length > 0 && videoIndex < recommendedVideos.length) {
      const videoId = recommendedVideos[videoIndex].video_id;
      const timeWatched = videoTime[videoId] || 0;

      // Define a minimum watch time (e.g., 2 seconds)
      const MINIMUM_WATCH_TIME = 2;

      if (timeWatched >= MINIMUM_WATCH_TIME) {
        setInteractionRecorded(true);
      }
    }
  };

  return (
    <div className="h-[100vh] overflow-y-scroll snap-y snap-mandatory" onScroll={handleScroll}>
      {recommendedVideos.map((video, index) => (
        <div key={`recommended-${video.video_id}`} className="h-full w-full snap-start relative">
          <VideoPlayer
            videoSrc={`http://127.0.0.1:5000/videos/${video.metadata.file_path}`}
            videoId={video.video_id}
            onTimeUpdate={(currentTime: number) => {
              handleTimeUpdate(index, currentTime);
              handleVideoInteraction(index); // Check for interaction on every time update
            }}
            playing={index === currentVideoIndex} // Control playing state
          />
          <div className="absolute bottom-4 left-4 right-12">
            <p className="font-bold">username</p>
            <p className="text-sm">{video.metadata.title || "No Title"}</p>
            <p className="text-sm">{video.metadata.genre || "No Genre"}</p>
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
  );
}