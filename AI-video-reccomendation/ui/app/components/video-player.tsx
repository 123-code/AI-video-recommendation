// video-player.tsx
import React from 'react';

interface VideoPlayerProps {
  videoSrc: string;
  onTimeUpdate?: (currentTime: number) => void;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoSrc, onTimeUpdate }) => {
  const [currentTime, setCurrentTime] = React.useState(0);

  const handleTimeUpdate = (e: React.SyntheticEvent<HTMLVideoElement>) => {
    const video = e.currentTarget;
    setCurrentTime(video.currentTime);
    if (onTimeUpdate) {
      onTimeUpdate(video.currentTime);
    }
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <video
        src={videoSrc}
        controls={true}
        autoPlay
        loop
        muted
        playsInline
        onTimeUpdate={handleTimeUpdate}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
    </div>
  );
};

export default VideoPlayer;
