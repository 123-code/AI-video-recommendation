import React from 'react';

interface VideoPlayerProps {
  videoSrc: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoSrc }) => {
  return (
    <div>
      <video 
        src={videoSrc} 
        controls={true} 
        autoPlay 
        loop 
        muted 
        playsInline 
        style={{
          width: '100%', 
          height: '100vh', 
          objectFit: 'cover', 
        }} 
      />
    </div>
  );
};

export default VideoPlayer;
