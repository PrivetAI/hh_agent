import { useState } from 'react'

export default function SearchHint() {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className="relative inline-flex items-center">
      {/* Desktop tooltip trigger */}
      <div 
        className="hidden md:block relative"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <svg
          className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        
        {/* Desktop tooltip */}
        {showTooltip && (
          <div className="absolute bottom-full right-0 mb-2 w-80 p-3 bg-gray-800 text-white text-sm rounded-lg shadow-lg z-10">
            <div className="space-y-2">
              <p><strong>AND</strong> - все слова: python AND java</p>
              <p><strong>OR</strong> - любое слово: python OR java</p>
              <p><strong>NOT</strong> - исключить: python NOT junior</p>
              <p><strong>"..."</strong> - точная фраза: "senior developer"</p>
              <p><strong>(...)</strong> - группировка: (python OR java) AND senior</p>
              <p>
                Доступен{' '}
                <a 
                  href="https://hh.ru/article/1175" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-300 underline hover:text-blue-200"
                >
                  язык запросов
                </a>
              </p>
            </div>
            <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"></div>
          </div>
        )}
      </div>

      {/* Mobile hint - always visible */}
      <div className="md:hidden w-full mt-2 p-2 bg-gray-50 text-xs text-gray-600 rounded border">
        <div className="space-y-1">
          <p><strong>AND</strong> - все слова, <strong>OR</strong> - любое слово, <strong>NOT</strong> - исключить</p>
          <p><strong>"..."</strong> - точная фраза, <strong>(...)</strong> - группировка</p>
          <p>
            Доступен{' '}
            <a 
              href="https://hh.ru/article/1175" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 underline"
            >
              язык запросов
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}