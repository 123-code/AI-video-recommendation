
import React, { useRef, useEffect } from 'react';

interface VideoPlayerProps {
  videoSrc: string;
  onTimeUpdate?: (currentTime: number) => void;
  playing: boolean; 
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
        autoPlay={playing}
        loop
        muted
        playsInline
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
    </div>
  );
};

export default VideoPlayer;