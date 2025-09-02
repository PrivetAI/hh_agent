import { useState, useEffect, useRef } from 'react'

export default function VideoDemoSection() {
  const [isVideoLoaded, setIsVideoLoaded] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    // Загружаем видео после того как DOM готов и основной контент загружен
    const loadVideo = () => {
      if (videoRef.current) {
        videoRef.current.load()
      }
    }

    // Используем setTimeout чтобы отложить загрузку до следующего тика event loop
    // это позволит сначала отрендерить весь остальной контент
    if (document.readyState === 'complete') {
      setTimeout(loadVideo, 100)
    } else {
      window.addEventListener('load', loadVideo)
      return () => window.removeEventListener('load', loadVideo)
    }
  }, [])

  const handleVideoLoaded = () => {
    setIsVideoLoaded(true)
    // Автовоспроизведение после загрузки
    if (videoRef.current) {
      videoRef.current.play().catch(err => {
        console.log('Autoplay prevented:', err)
      })
    }
  }

  return (
    <section className="container mx-auto px-4 pb-8 sm:pb-12" aria-labelledby="demo-section">
      <div className="text-center mb-10">
        <h2 id="demo-section" className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
          Демонстрация работы <br/> HH Agent
        </h2>
      </div>
      
      <div className="bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden max-w-5xl mx-auto relative">
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

        {/* Видео */}
        <video
          ref={videoRef}
          className="w-full h-auto"
          autoPlay
          muted
          loop
          playsInline
          preload="none"
          onLoadedData={handleVideoLoaded}
        >
          {/* Добавьте несколько форматов для лучшей совместимости */}
          <source src="/demo-video.mp4" type="video/mp4" />
          
        </video>
      </div>
    </section>
  )
}