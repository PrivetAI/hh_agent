// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // Оптимизация изображений
  images: {
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
  // Сжатие
  compress: true,
    serverRuntimeConfig: {},
  publicRuntimeConfig: {},
  output: 'standalone',
  // Оптимизация для production
  poweredByHeader: false,
  
  // SEO заголовки
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          }
        ]
      },
      {
        source: '/favicon.ico',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ]
      },  
      {
        source: '/(.*\\.(png|jpg|jpeg|gif|webp|svg|ico|woff|woff2|ttf|eot))',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ]
      }
    ]
  },
  
  // Редиректы
  async redirects() {
    return [
      // Добавьте свои редиректы здесь при необходимости
    ]
  },
  
  // Переписывание URL
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://hh_backend:8000/:path*',
      },
    ]
  },
}