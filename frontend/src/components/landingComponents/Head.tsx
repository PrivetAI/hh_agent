// components/SEOHead.tsx
import Head from 'next/head'

interface SEOHeadProps {
  title?: string
  description?: string
  keywords?: string
  ogImage?: string
  ogUrl?: string
  canonicalUrl?: string
  noindex?: boolean
}

export default function SEOHead({
  title = 'HH Agent - AI поиск работы на hh.ru | Умные сопроводительные письма',
  description = 'Умный AI-помощник для поиска работы на hh.ru. Создает уникальные сопроводительные письма, увеличивая отклик работодателей в 3 раза. Бесплатно!',
  keywords = 'hh.ru, поиск работы, AI помощник, сопроводительные письма, отклики, резюме, вакансии, HeadHunter, автоматизация откликов',
  ogImage = '/og-image.png',
  ogUrl = 'https://hhagent.ru',
  canonicalUrl,
  noindex = false
}: SEOHeadProps) {
  const fullTitle = title.includes('HH Agent') ? title : `${title} | HH Agent`

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
      
      {/* Open Graph */}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:url" content={ogUrl} />
      <meta property="og:type" content="website" />
      <meta property="og:site_name" content="HH Agent" />
      <meta property="og:locale" content="ru_RU" />
      
      {/* Twitter Card */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />
      
      {/* Favicon */}
      <link rel="icon" href="/favicon.ico" />
      <link rel="apple-touch-icon" sizes="180x180" href="/favicon-32x32.png" />
      <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
      <link rel="manifest" href="/manifest.json" />
      
      {/* Дополнительные мета-теги для поисковиков */}
      <meta name="theme-color" content="#d6001c" />
      <meta name="msapplication-TileColor" content="#d6001c" />
      <meta name="application-name" content="HH Agent" />
      
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