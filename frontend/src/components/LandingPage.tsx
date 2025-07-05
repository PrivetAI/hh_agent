'use client'
import { useState } from 'react'
import SEOHead from './Head'
import Footer from './Footer'

interface CTASectionProps {
  onLogin: () => Promise<void>
  loading?: boolean
  showFreeTrialBadge?: boolean
}

function CTASection({ onLogin, loading = false, showFreeTrialBadge = true }: CTASectionProps) {
 const [privacyAccepted, setPrivacyAccepted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleClick = async () => {
    if (!privacyAccepted || isLoading) return
    
    setIsLoading(true)
    try {
      await onLogin()
    } finally {
      setIsLoading(false)
    }
  }

  const actualLoading = loading || isLoading

  return (
    <div className="w-full flex flex-col items-center space-y-6">
      {showFreeTrialBadge && (
        <div className="bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-300 text-orange-800 px-6 py-3 rounded-full text-sm sm:text-base font-medium inline-flex items-center gap-2 shadow-sm">
          <span className="text-lg">🎯</span>
          <span>10 бесплатных откликов для новых пользователей</span>
        </div>
      )}

      <div className="flex flex-col items-center gap-4 w-full max-w-sm">
        <label className="flex items-start gap-3 text-xs sm:text-sm text-gray-600 cursor-pointer group">
          <input
            type="checkbox"
            checked={privacyAccepted}
            onChange={(e) => setPrivacyAccepted(e.target.checked)}
            className="mt-0.5 h-4 w-4 text-[#d6001c] border-gray-300 rounded focus:ring-2 focus:ring-[#d6001c] focus:ring-offset-2 transition-all cursor-pointer"
          />
          <span className="select-none leading-relaxed">
            Я принимаю условия{' '}
            <a 
              href="/offerta" 
              className="text-[#d6001c] hover:text-[#a5001a] font-medium underline-offset-2 hover:underline transition-colors" 
              target="_blank" 
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
            >
              пользовательского соглашения
            </a>
            {' '}и{' '}
            <a 
              href="/privacy-policy" 
              className="text-[#d6001c] hover:text-[#a5001a] font-medium underline-offset-2 hover:underline transition-colors" 
              target="_blank" 
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
            >
              политики конфиденциальности
            </a>
          </span>
        </label>

        <button 
          onClick={handleClick}
          disabled={actualLoading || !privacyAccepted}
          className={`
            relative w-full sm:w-auto min-w-[240px] 
            px-8 py-4 
            text-base sm:text-lg font-semibold text-white
            bg-[#d6001c] hover:bg-[#b50018] 
            disabled:bg-gray-300 disabled:text-gray-500
            rounded-xl shadow-lg hover:shadow-xl
            transform transition-all duration-200 
            hover:scale-[1.02] active:scale-[0.98]
            disabled:transform-none disabled:shadow-md
            disabled:cursor-not-allowed
            focus:outline-none focus:ring-4 focus:ring-[#d6001c]/30
          `}
          aria-label="Начать использовать HH Agent бесплатно"
        >
          <span className={`flex items-center justify-center gap-2 ${actualLoading ? 'opacity-0' : ''}`}>
            Начать бесплатно
          </span>
          
          {actualLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span className="text-white font-medium">Подключение...</span>
              </div>
            </div>
          )}
        </button>
      </div>
    </div>
  )
}

// Constants
const FEATURES = [
  {
    icon: '⚡',
    title: 'Молниеносная скорость',
    description: 'Забудьте о часах написания писем. AI создает качественный текст за 3 секунды'
  },
  {
    icon: '🎨',
    title: 'Идеальная персонализация',
    description: 'Каждое письмо уникально и точно соответствует требованиям конкретной вакансии'
  },
  {
    icon: '🔒',
    title: 'Максимальная безопасность',
    description: 'Работаем только через официальный API hh.ru. Все официально и безопасно'
  },
  {
    icon: '✏️',
    title: 'Полный контроль',
    description: 'Редактируйте и дорабатывайте письма перед отправкой по своему усмотрению'
  }
]

const PROCESS_STEPS = [
  {
    icon: '🎯',
    title: 'Выбираете вакансии',
    description: 'Ищите интересные позиции на hh.ru как обычно'
  },
  {
    icon: '🤖',
    title: 'AI анализирует',
    description: 'Система изучает вакансию и ваше резюме за 3 секунды'
  },
  {
    icon: '📨',
    title: 'Отправляете отклик',
    description: 'Уникальное письмо автоматически прикрепляется к отклику'
  }
]

const FAQ_ITEMS = [
  {
    question: 'Как работает AI-генерация писем?',
    answer: 'Система анализирует описание вакансии, требования и ваше резюме, создавая персонализированное письмо с акцентом на ваши сильные стороны'
  },
  {
    question: 'Насколько безопасно пользоваться приложением?',
    answer: 'Используем только официальный OAuth API HeadHunter. Никаких блокировок и рисков'
  },
  {
    question: 'Что входит в бесплатный период?',
    answer: '10 полноценных AI-генераций сопроводительных писем. Этого хватит, чтобы оценить качество и эффективность сервиса'
  }
]

interface LandingPageProps {}

export default function LandingPage({}: LandingPageProps) {
  const [loading, setLoading] = useState(false)
  
  const handleLogin = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/auth/hh`)
      const data = await response.json()
      window.location.href = data.url
    } catch (error) {
      console.error('Login error:', error)
      setLoading(false)
    }
  }

  return (
    <>
      <SEOHead
        title="HH Agent - Умный AI поиск работы на hh.ru"
        description="AI создает персонализированные сопроводительные письма для каждой вакансии на hh.ru, увеличивая отклик работодателей в 3 раза. 10 бесплатных откликов для новых пользователей."
        keywords="поиск работы, hh.ru, сопроводительные письма, AI помощник, автоматизация поиска работы, резюме, вакансии, HeadHunter, искусственный интеллект, персонализированные письма"
        canonicalUrl="https://hhagent.ru"
      />
      
      <div className="min-h-screen bg-gray-50 flex flex-col">
        {/* Header */}
        <header className="bg-white shadow-sm border-b top-0 z-50">
          <div className="container mx-auto px-4 py-4 sm:py-5">
            <div className="flex items-center justify-center">
              <div className="flex items-center space-x-2">
                <span className="text-[#d6001c] font-bold text-2xl sm:text-3xl">hh</span>
                <span className="text-gray-800 font-bold text-xl sm:text-2xl">агент</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-grow">
          {/* Hero Section */}
          <section className="container mx-auto px-4 py-8 sm:py-12 lg:py-16">
            <div className="text-center mb-8 sm:mb-12">
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 sm:mb-6 leading-tight">
                Умный поиск работы
                <br />
                <span className="text-[#d6001c]">на новом уровне</span>
              </h1>
              
              <p className="text-base sm:text-lg lg:text-xl text-gray-600 max-w-3xl mx-auto mb-8 sm:mb-10 leading-relaxed">
                AI создает персонализированные сопроводительные письма для каждой вакансии на hh.ru, 
                увеличивая отклик работодателей в 3 раза
              </p>

              <CTASection onLogin={handleLogin} loading={loading} />
            </div>
          </section>

          {/* Demo Section */}
          <section className="container mx-auto px-4 pb-8 sm:pb-12" aria-labelledby="demo-section">
            <h2 id="demo-section" className="sr-only">Демонстрация работы HH Agent</h2>
            <div className="bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden max-w-5xl mx-auto">
              <img 
                src="/image.png" 
                alt="Демонстрация интерфейса HH Agent - создание персонализированных сопроводительных писем"
                className="w-full h-auto"
                width="1200"
                height="800"
                loading="lazy"
              />
            </div>
          </section>

          {/* Process Steps */}
          <section className="bg-gray-100 py-12 sm:py-16" aria-labelledby="process-section">
            <div className="container mx-auto px-4">
              <h2 id="process-section" className="text-2xl sm:text-3xl font-bold text-center text-gray-900 mb-8 sm:mb-12">
                Как это работает
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 max-w-5xl mx-auto">
                {PROCESS_STEPS.map((step, index) => (
                  <article key={index} className="bg-white p-6 sm:p-8 rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200">
                    <div className="text-3xl sm:text-4xl mb-4 text-center" aria-hidden="true">{step.icon}</div>
                    <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3 text-center">{step.title}</h3>
                    <p className="text-sm sm:text-base text-gray-600 text-center">{step.description}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          {/* Features Grid */}
          <section className="container mx-auto px-4 py-12 sm:py-16" aria-labelledby="features-section">
            <h2 id="features-section" className="text-2xl sm:text-3xl font-bold text-center text-gray-900 mb-8 sm:mb-12">
              Преимущества
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8 max-w-5xl mx-auto">
              {FEATURES.map((feature, index) => (
                <article key={index} className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200">
                  <div className="flex items-start space-x-4">
                    <div className="text-2xl sm:text-3xl flex-shrink-0" aria-hidden="true">{feature.icon}</div>
                    <div>
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                      <p className="text-sm sm:text-base text-gray-600">{feature.description}</p>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>

          {/* FAQ Section */}
          <section className="bg-gray-100 py-12 sm:py-16" aria-labelledby="faq-section">
            <div className="container mx-auto px-4">
              <h2 id="faq-section" className="text-2xl sm:text-3xl font-bold text-center text-gray-900 mb-8 sm:mb-12">
                Популярные вопросы
              </h2>
              
              <div className="space-y-4 sm:space-y-6 max-w-3xl mx-auto">
                {FAQ_ITEMS.map((item, index) => (
                  <article key={index} className="bg-white rounded-lg p-5 sm:p-6 shadow-md">
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2 sm:mb-3">{item.question}</h3>
                    <p className="text-sm sm:text-base text-gray-600">{item.answer}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          {/* Personal Message */}
          <section className="container mx-auto px-4 py-12 sm:py-16" aria-labelledby="personal-message">
            <div className="bg-white rounded-xl p-6 sm:p-10 shadow-lg max-w-4xl mx-auto">
              <h2 id="personal-message" className="text-2xl sm:text-3xl font-bold text-gray-900 text-center mb-6 sm:mb-8">
                Слово от создателя
              </h2>
              
              <div className="text-gray-500 space-y-4 text-sm sm:text-base lg:text-lg leading-relaxed">
                <p>
                  Привет! Я создал HH Agent, чтобы помочь таким же людям, как и я, найти работу своей мечты.
                </p>
                
                <p>
                  Я искренне рад предоставить вам этот сервис. Честно говоря, я бы хотел сделать его еще дешевле — и работаю над этим каждый день. 
                  Чем больше людей будут пользоваться сервисом, тем доступнее я смогу его сделать.
                </p>
                
                <p>
                  <strong>Пользуйтесь, и я обещаю улучшать генерацию каждый день!</strong>
                </p>
                
                <p>
                  <strong>Моя цель — не просто создать сервис для генерации, а сделать настоящего AI убийцу рынка поиска работы...</strong>
                </p>
                
                <p>
                  Юзайте, делитесь обратной связью! 
                  <a href="#" className="text-[#d6001c] hover:text-[#c5001a] transition-colors font-medium ml-1">Поделиться фидбеком</a>
                </p>
              </div>
            </div>
          </section>

          {/* Bottom CTA */}
          <section className="container mx-auto px-4 pb-12 sm:pb-16">
            <div className="text-center">
              <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 mb-6">
                Готовы начать? Авторизуйтесь через HeadHunter
              </h2>
              <CTASection onLogin={handleLogin} loading={loading} showFreeTrialBadge={false} />
            </div>
          </section>
        </main>

        <Footer />
      </div>
    </>
  )
}