"use client";

import { useState, useEffect } from "react";
import { Heart, MessageCircle, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import VideoPlayer from "./video-player"; 

interface Video {
  video_id: string;
  metadata: {
    file_path: string;
    genre?: string; 
    title?: string;
  };
  similarity_score?: number; 
}

export default function TikTokFeed() {
    const [videos, setVideos] = useState<Video[]>([]);
    const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
    const [showComments, setShowComments] = useState(false);
    const [videoTime, setVideoTime] = useState<{ [videoId: string]: number }>({});
    const [recommendedVideos, setRecommendedVideos] = useState<Video[]>([]);
    const [isFetching, setIsFetching] = useState(false); 

  useEffect(() => {
    fetchInitialVideos();
  }, []);

    const fetchInitialVideos = () => {
      setIsFetching(true);
    fetch("http://127.0.0.1:5050/random_videos")  
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
    if (isFetching) return; 
    setIsFetching(true);
    fetch("http://127.0.0.1:5050/next_video?user_id=user1")
      .then((res) => res.json())
      .then((data) => {
      
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

  
    if (newIndex !== currentVideoIndex) {
       if (currentVideoIndex < displayedVideos.length) {
         const videoId = displayedVideos[currentVideoIndex].video_id;
         const timeWatched = videoTime[videoId] || 0;

            if (videoId && timeWatched > 0) { 
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
                    return response.json();

                })
                .then(data => {
                    console.log("Interaction update successful:", data);
                
                    setVideoTime(prev => {
                        const updated = { ...prev };
                        delete updated[videoId];
                        return updated;
                    });

              
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

    if (videoIndex < displayedVideos.length) {
      const videoId = displayedVideos[videoIndex].video_id;
      setVideoTime((prevVideoTime) => ({
        ...prevVideoTime,
        [videoId]: currentTime,
      }));
    }
  };




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
            playing={index === currentVideoIndex}  
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