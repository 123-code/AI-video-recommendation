"use client";

import { useState, useEffect } from "react";
import { Heart, MessageCircle, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import VideoPlayer from "./video-player"; // Make sure this path is correct

interface Video {
  video_id: string;
  metadata: {
    file_path: string;
    genre?: string; // Add genre and make it optional
    title?: string; // Add title and make it optional
  };
  similarity_score?: number; // Optional, as random videos won't have it.
}

export default function TikTokFeed() {
    const [videos, setVideos] = useState<Video[]>([]);
    const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
    const [showComments, setShowComments] = useState(false);
    const [videoTime, setVideoTime] = useState<{ [videoId: string]: number }>({});
    const [recommendedVideos, setRecommendedVideos] = useState<Video[]>([]);
    const [isFetching, setIsFetching] = useState(false); // Track if a fetch is in progress

  useEffect(() => {
    fetchInitialVideos();
  }, []);

    const fetchInitialVideos = () => {
      setIsFetching(true);
    fetch("http://127.0.0.1:5050/random_videos")  // No user_id needed for random videos
      .then((res) => res.json())
        .then((data) => {
          setVideos(data);
            setIsFetching(false);
        })
        .catch((error) => {
            console.error("Error fetching initial videos:", error);
            setIsFetching(false);
        });
  };


  const fetchNextVideo = () => {
    if (isFetching) return; // Prevent concurrent fetches
    setIsFetching(true);
    fetch("http://127.0.0.1:5050/next_video?user_id=user1")
      .then((res) => res.json())
      .then((data) => {
        // Add the new video to the *recommended* videos list.
        setRecommendedVideos((prevVideos) => [...prevVideos, data]);
        setIsFetching(false);
      })
      .catch((error) => {
        console.error("Error fetching recommended video:", error);
        setIsFetching(false);
      });
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    const scrollPosition = container.scrollTop;
    const videoHeight = container.clientHeight;
    const newIndex = Math.round(scrollPosition / videoHeight);

    // Only update if the index has actually changed
    if (newIndex !== currentVideoIndex) {
       if (currentVideoIndex < displayedVideos.length) {
         const videoId = displayedVideos[currentVideoIndex].video_id;
         const timeWatched = videoTime[videoId] || 0;

            if (videoId && timeWatched > 0) {  // Only send if watched for >0s
                fetch(`http://127.0.0.1:5050/update_interaction`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        user_id: "user1",
                        video_id: videoId,
                        interaction_type: "watch_time",
                        value: timeWatched
                    })
                })
                .then(response => {
                    if (!response.ok) {
                      return response.json().then(err => {throw new Error(err.message || 'Failed to update interaction')})
                    }
                    return response.json(); // Parse the JSON first

                })
                .then(data => {
                    console.log("Interaction update successful:", data);
                    // Clear the watch time after sending, so we don't send it again.
                    setVideoTime(prev => {
                        const updated = { ...prev };
                        delete updated[videoId];
                        return updated;
                    });

                    // Fetch the next video *after* the update is successful.
                    fetchNextVideo();
                })
                .catch((error) => console.error("Error updating interaction:", error));
            }
            else {
              if (newIndex >= videos.length + recommendedVideos.length -1){
                fetchNextVideo();
              }
            }
        }
      setCurrentVideoIndex(newIndex);
    }
  };


  const handleTimeUpdate = (videoIndex: number, currentTime: number) => {
    // Use the combined video list here.
    if (videoIndex < displayedVideos.length) {
      const videoId = displayedVideos[videoIndex].video_id;
      setVideoTime((prevVideoTime) => ({
        ...prevVideoTime,
        [videoId]: currentTime,
      }));
    }
  };



  // Combine initial random videos with recommended videos
  const displayedVideos = [...videos, ...recommendedVideos];

  return (
    <div className="h-[100vh] overflow-y-scroll snap-y snap-mandatory" onScroll={handleScroll}>
      {displayedVideos.map((video, index) => (
        <div key={`video-${video.video_id}-${index}`} className="h-full w-full snap-start relative">
          <VideoPlayer
            videoSrc={`http://127.0.0.1:5050/${video.metadata.file_path}`}
            videoId={video.video_id}
            onTimeUpdate={(currentTime: number) => {
              handleTimeUpdate(index, currentTime);
            }}
            playing={index === currentVideoIndex}  // Play only the current video
          />
          <div className="absolute bottom-4 left-4 right-12">
            <p className="font-bold">username</p>
            <p className="text-sm">{video.metadata.title || "No Title"}</p>
            <p className="text-sm">{video.metadata.genre || "No Genre"}</p>
          </div>
          <div className="absolute bottom-20 right-2 flex flex-col items-center space-y-4">
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full bg-gray-800 text-white"
            >
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
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full bg-gray-800 text-white"
            >
              <Share2 className="h-6 w-6" />
            </Button>
            <span className="text-xs">shares</span>
          </div>
          {showComments && (
            <div
              className="absolute bottom-0 left-0 right-0 h-1/2 bg-gray-900 bg-opacity-90 p-4 overflow-y-auto">
              <h3 className="text-lg font-bold mb-2">Comments</h3>
              <div className="space-y-2">
                <p>
                  <span className="font-bold">commenter1:</span> Great video!
                </p>
                <p>
                  <span className="font-bold">commenter2:</span> Love this
                  content!
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