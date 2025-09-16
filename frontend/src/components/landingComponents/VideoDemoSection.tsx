import { useState, useEffect, useRef } from 'react'

export default function VideoDemoSection() {
  const [isVideoLoaded, setIsVideoLoaded] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Для iOS требуется особая обработка
    const loadVideo = () => {
      if (videoRef.current) {
        // Для iOS важно установить эти атрибуты
        videoRef.current.setAttribute('playsinline', 'true')
        videoRef.current.setAttribute('webkit-playsinline', 'true')
        videoRef.current.load()
      }
    }

    if (document.readyState === 'complete') {
      setTimeout(loadVideo, 100)
    } else {
      window.addEventListener('load', loadVideo)
      return () => window.removeEventListener('load', loadVideo)
    }
  }, [])

  useEffect(() => {
    // Слушаем изменения fullscreen
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
    
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
    }
  }, [])

  const handleVideoLoaded = () => {
    setIsVideoLoaded(true)
    // Не запускаем автовоспроизведение на iOS
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
    if (!isIOS && videoRef.current) {
      videoRef.current.play()
        .then(() => setIsPlaying(true))
        .catch(err => {
          console.log('Autoplay prevented:', err)
          setIsPlaying(false)
        })
    }
  }

  const togglePlay = () => {
    if (!videoRef.current) return

    if (isPlaying) {
      videoRef.current.pause()
      setIsPlaying(false)
    } else {
      videoRef.current.play()
        .then(() => setIsPlaying(true))
        .catch(err => console.error('Play failed:', err))
    }
  }

  const toggleFullscreen = () => {
    if (!containerRef.current) return

    if (!isFullscreen) {
      // Запрос fullscreen с поддержкой разных браузеров
      const elem = containerRef.current as any
      if (elem.requestFullscreen) {
        elem.requestFullscreen()
      } else if (elem.webkitRequestFullscreen) { // Safari
        elem.webkitRequestFullscreen()
      } else if (elem.webkitEnterFullscreen) { // iOS Safari
        elem.webkitEnterFullscreen()
      }
    } else {
      // Выход из fullscreen
      const doc = document as any
      if (doc.exitFullscreen) {
        doc.exitFullscreen()
      } else if (doc.webkitExitFullscreen) { // Safari
        doc.webkitExitFullscreen()
      }
    }
  }

  // Обработка окончания видео для loop
  const handleVideoEnd = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = 0
      videoRef.current.play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false))
    }
  }

  return (
    <section className="container mx-auto px-4 pb-8 sm:pb-12" aria-labelledby="demo-section">
      <div className="text-center mb-10">
        <h2 id="demo-section" className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
          Демонстрация работы <br/> HH Agent
        </h2>
      </div>
      
      <div 
        ref={containerRef}
        className="bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden max-w-5xl mx-auto relative group"
      >
        {/* Placeholder пока видео не загружено */}
        {!isVideoLoaded && (
          <div className="absolute inset-0 bg-gray-100 animate-pulse flex items-center justify-center z-10">
            <div className="text-center">
              <svg className="animate-spin h-10 w-10 text-gray-400 mx-auto mb-4" viewBox="0 0 24 24">
                <circle 
                  className="opacity-25" 
                  cx="12" 
                  cy="12" 
                  r="10" 
                  stroke="currentColor" 
                  strokeWidth="4" 
                  fill="none"
                />
                <path 
                  className="opacity-75" 
                  fill="currentColor" 
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <p className="text-gray-500 text-sm">Загрузка демонстрации...</p>
            </div>
          </div>
        )}

        {/* Видео контейнер */}
        <div className="relative">
          <video
            ref={videoRef}
            className="w-full h-auto"
            muted
            playsInline
            webkit-playsinline="true"
            preload="metadata"
            onLoadedData={handleVideoLoaded}
            onEnded={handleVideoEnd}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          >
            <source src="/demo-video.mp4" type="video/mp4" />
            <source src="/demo-video.webm" type="video/webm" />
          </video>

          {/* Кастомные контролы */}
          {isVideoLoaded && (
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-6 pb-8 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <div className="flex items-center gap-4">
                {/* Play/Pause кнопка */}
                <button
                  onClick={togglePlay}
                  className="text-white hover:text-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-white/50 rounded-lg p-2"
                  aria-label={isPlaying ? 'Pause video' : 'Play video'}
                >
                  {isPlaying ? (
                    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                    </svg>
                  ) : (
                    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z"/>
                    </svg>
                  )}
                </button>

                {/* Spacer */}
                <div className="flex-1" />

                {/* Fullscreen кнопка */}
                <button
                  onClick={toggleFullscreen}
                  className="text-white hover:text-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-white/50 rounded-lg p-2"
                  aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
                >
                  {isFullscreen ? (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M8 3v3a2 2 0 01-2 2H3m18 0h-3a2 2 0 01-2-2V3m0 18v-3a2 2 0 012-2h3M3 16h3a2 2 0 012 2v3" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Большая кнопка play по центру когда видео на паузе */}
          {isVideoLoaded && !isPlaying && (
            <button
              onClick={togglePlay}
              className="absolute inset-0 flex items-center justify-center bg-black/30 transition-opacity hover:bg-black/40"
              aria-label="Play video"
            >
              <div className="bg-white/90 rounded-full p-4 hover:bg-white transition-colors">
                <svg className="w-12 h-12 text-gray-900" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
            </button>
          )}
        </div>
      </div>
    </section>
  )
}