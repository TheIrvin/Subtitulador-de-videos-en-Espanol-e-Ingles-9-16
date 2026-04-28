import React, { useEffect, useRef, useState } from "react";
import SubtitleOverlay from "./SubtitleOverlay.jsx";

export default function VideoPreview({ videoUrl, activeBlock, currentTime, onPlaybackChange, onTimeUpdate }) {
  const shellRef = useRef(null);
  const videoRef = useRef(null);
  const animationRef = useRef(null);
  const lastTimeRef = useRef(-1);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);

  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const publishCurrentTime = () => {
    const video = videoRef.current;
    if (!video) return;

    const nextTime = video.currentTime;
    if (Math.abs(nextTime - lastTimeRef.current) >= 0.01) {
      lastTimeRef.current = nextTime;
      onTimeUpdate(nextTime);
    }
  };

  const handleLoadedMetadata = () => {
    const video = videoRef.current;
    setDuration(video?.duration || 0);
    publishCurrentTime();
  };

  const trackFrame = () => {
    publishCurrentTime();
    const video = videoRef.current;
    if (video && !video.paused && !video.ended) {
      animationRef.current = requestAnimationFrame(trackFrame);
    }
  };

  const handlePlay = () => {
    setIsPlaying(true);
    onPlaybackChange(true);
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    animationRef.current = requestAnimationFrame(trackFrame);
  };

  const handlePause = () => {
    setIsPlaying(false);
    onPlaybackChange(false);
    publishCurrentTime();
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  };

  const handleFullscreen = async () => {
    const shell = shellRef.current;
    if (!shell) return;

    if (document.fullscreenElement) {
      await document.exitFullscreen();
      return;
    }

    await shell.requestFullscreen();
  };

  const togglePlay = async () => {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused) {
      await video.play();
    } else {
      video.pause();
    }
  };

  const handleSeek = (event) => {
    const video = videoRef.current;
    if (!video) return;

    const nextTime = Number(event.target.value);
    video.currentTime = nextTime;
    onTimeUpdate(nextTime);
  };

  const handleVolumeChange = (event) => {
    const video = videoRef.current;
    const nextVolume = Number(event.target.value);
    setVolume(nextVolume);
    if (video) {
      video.volume = nextVolume;
      video.muted = nextVolume === 0;
    }
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;

    if (video.muted || video.volume === 0) {
      video.muted = false;
      video.volume = volume || 1;
      setVolume(video.volume);
    } else {
      video.muted = true;
      setVolume(0);
    }
  };

  const formatTime = (value) => {
    const safeValue = Math.max(0, Number(value) || 0);
    const minutes = Math.floor(safeValue / 60);
    const seconds = Math.floor(safeValue % 60).toString().padStart(2, "0");
    return `${minutes}:${seconds}`;
  };

  return (
    <section className="preview-panel">
      <div className="video-shell" ref={shellRef}>
        {videoUrl ? (
          <div className="video-stage">
            <video
              ref={videoRef}
              className="preview-video"
              src={videoUrl}
              onLoadedMetadata={handleLoadedMetadata}
              onPause={handlePause}
              onPlay={handlePlay}
              onSeeked={publishCurrentTime}
              onTimeUpdate={publishCurrentTime}
              onClick={togglePlay}
            />
            <SubtitleOverlay block={activeBlock} currentTime={currentTime} />
            <div className="custom-video-controls">
              <button className="video-icon-button" type="button" onClick={togglePlay} title={isPlaying ? "Pausar" : "Reproducir"}>
                {isPlaying ? "Ⅱ" : "▶"}
              </button>
              <span className="video-time">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
              <input
                className="video-progress"
                max={duration || 0}
                min="0"
                onChange={handleSeek}
                step="0.01"
                type="range"
                value={Math.min(currentTime, duration || currentTime)}
              />
              <button className="video-icon-button" type="button" onClick={toggleMute} title="Volumen">
                {volume === 0 ? "🔇" : "🔊"}
              </button>
              <input
                className="video-volume"
                max="1"
                min="0"
                onChange={handleVolumeChange}
                step="0.01"
                type="range"
                value={volume}
              />
              <button className="video-icon-button" type="button" onClick={handleFullscreen} title="Pantalla completa">
                ⛶
              </button>
            </div>
          </div>
        ) : (
          <div className="empty-preview">Sube un video para iniciar</div>
        )}
      </div>
    </section>
  );
}
