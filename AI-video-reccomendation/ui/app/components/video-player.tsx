import React, { useRef, useEffect } from 'react';

interface VideoPlayerProps {
  videoSrc: string;
  onTimeUpdate?: (currentTime: number) => void;
  playing: boolean;
  videoId?: string;
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
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.catch(() => {});
      }
    } else {
      video.pause();
    }

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [videoSrc, onTimeUpdate, playing]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <video
        ref={videoRef}
        src={videoSrc}
        controls={false}
        loop
        muted
        playsInline
        preload="auto"
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
    </div>
  );
};

export default VideoPlayer;