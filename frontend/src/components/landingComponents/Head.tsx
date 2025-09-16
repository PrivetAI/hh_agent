import Head from 'next/head'

interface SEOHeadProps {
  title?: string
  description?: string
  keywords?: string
  ogImage?: string
  ogImageWidth?: number
  ogImageHeight?: number
  ogImageType?: string
  ogImageAlt?: string
  ogImageSecureUrl?: string
  ogUrl?: string
  canonicalUrl?: string
  noindex?: boolean
}

export default function SEOHead({
  title = 'HH Agent - AI поиск работы на hh.ru | Автоматизированные сопроводительные письма',
  description = 'Умный AI-помощник для поиска работы на hh.ru. Создает уникальные сопроводительные письма, увеличивая отклик работодателей в 3 раза. Бесплатно!',
  keywords = 'hh.ru, поиск работы, AI помощник, сопроводительные письма, отклики, резюме, вакансии, HeadHunter, автоматизация откликов headhunter, сопроводительное письмо headhunter',
  ogImage = '/og-image.png',
  ogImageWidth = 1200,
  ogImageHeight = 630,
  ogImageType = 'image/png',
  ogImageAlt = 'HH Agent — AI-помощник для поиска работы на hh.ru',
  ogImageSecureUrl,
  ogUrl = 'https://hhagent.ru',
  canonicalUrl,
  noindex = false
}: SEOHeadProps) {
  const fullTitle = title.includes('HH Agent') ? title : `${title} | HH Agent`

  // Собираем абсолютный URL для изображения (Telegram требует доступ по HTTPS)
  const siteUrl = ogUrl.replace(/\/+$|\s+/g, '')
  const makeAbsolute = (p: string) => {
    if (!p) return p
    if (/^https?:\/\//i.test(p)) return p
    const path = p.startsWith('/') ? p : `/${p}`
    return `${siteUrl}${path}`
  }

  const absoluteOgImage = makeAbsolute(ogImage)
  const absoluteSecureOgImage = ogImageSecureUrl ? makeAbsolute(ogImageSecureUrl) : absoluteOgImage

  return (
    <Head>
      {/* Основные мета-теги */}
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <meta name="author" content="HH Agent" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />

      {/* Robots */}
      {noindex && <meta name="robots" content="noindex, nofollow" />}

      {/* Canonical URL */}
      {canonicalUrl && <link rel="canonical" href={canonicalUrl} />}

      {/* Open Graph (включая расширенные теги для корректной миниатюры в Telegram/мессенджерах) */}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      {absoluteOgImage && <meta property="og:image" content={absoluteOgImage} />}
      {absoluteSecureOgImage && <meta property="og:image:secure_url" content={absoluteSecureOgImage} />}
      <meta property="og:image:width" content={String(ogImageWidth)} />
      <meta property="og:image:height" content={String(ogImageHeight)} />
      <meta property="og:image:type" content={ogImageType} />
      <meta property="og:image:alt" content={ogImageAlt} />
      <meta property="og:url" content={ogUrl} />
      <meta property="og:type" content="website" />
      <meta property="og:site_name" content="HH Agent" />
      <meta property="og:locale" content="ru_RU" />

      {/* Twitter Card */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      {absoluteOgImage && <meta name="twitter:image" content={absoluteOgImage} />}
      <meta name="twitter:image:alt" content={ogImageAlt} />

      {/* Favicon */}
      <link rel="icon" href="/favicon.ico" />
      <link rel="apple-touch-icon" sizes="180x180" href="/favicon-32x32.png" />
      <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
      <link rel="manifest" href="/manifest.json" />

      {/* Дополнительные мета-теги для поисковиков */}
      <meta name="theme-color" content="#d6001c" />
      <meta name="msapplication-TileColor" content="#d6001c" />
      <meta name="application-name" content="HH Agent" />

      {/* Поддержка старых клиентов/мессенджеров */}
      {absoluteOgImage && <link rel="image_src" href={absoluteOgImage} />}

      {/* Структурированные данные */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": "HH Agent",
            "description": description,
            "url": ogUrl,
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Web",
            "offers": {
              "@type": "Offer",
              "price": "0",
              "priceCurrency": "RUB",
              "description": "10 бесплатных откликов для новых пользователей"
            },
            "author": {
              "@type": "Organization",
              "name": "HH Agent"
            }
          })
        }}
      />
    </Head>
  )
}
