// video-player.tsx
import React, { useRef, useEffect } from 'react';

interface VideoPlayerProps {
  videoSrc: string;
  onTimeUpdate?: (currentTime: number) => void;
  playing: boolean; // Added prop
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoSrc, onTimeUpdate, playing }) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;

    if (!video) return;

    const handleTimeUpdate = () => {
      if (onTimeUpdate) {
        onTimeUpdate(video.currentTime);
      }
    };

    video.addEventListener("timeupdate", handleTimeUpdate);

    // Play/Pause based on 'playing' prop
    if (playing) {
      video.play().catch(error => {
        console.error("Autoplay failed:", error);
      });
    } else {
      video.pause();
    }

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [videoSrc, onTimeUpdate, playing]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <video
        ref={videoRef}
        src={videoSrc}
        controls={true}
        autoPlay={playing} // Conditionally autoplay
        loop
        muted
        playsInline
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
    </div>
  );
};

export default VideoPlayer;