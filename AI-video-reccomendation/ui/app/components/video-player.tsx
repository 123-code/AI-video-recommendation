// video-player.tsx
import React from 'react';

interface VideoPlayerProps {
  videoSrc: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoSrc }) => {
  return (
    <div>
      <video src={videoSrc} controls={true} autoPlay loop muted playsInline />
    </div>
  );
};

export default VideoPlayer;
