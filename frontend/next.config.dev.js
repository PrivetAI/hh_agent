/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: false, // Отключаем для dev
  
  // Настройки для разработки
  typescript: {
    ignoreBuildErrors: true, // Для быстрой разработки
  },
  eslint: {
    ignoreDuringBuilds: true, // Для быстрой разработки
  },
  
  // Оптимизация изображений
  images: {
    formats: ['image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
    unoptimized: true, // Для dev среды
  },
  
  // Отключаем сжатие для dev
  compress: false,
  
  
  // Убираем production оптимизации
  poweredByHeader: true,
  
  // Переписывание URL для проксирования API запросов
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/:path*',
      },
    ]
  },
  
  // Настройки для hot reload
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // Настройки для dev режима
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      }
    }
    return config
  },
  
  // Экспериментальные функции для dev
  experimental: {
    // Включаем для лучшего dev опыта
    serverComponentsExternalPackages: [],
  },
}

module.exports = nextConfig