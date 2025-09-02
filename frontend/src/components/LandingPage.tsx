'use client'
import { useState, useEffect } from 'react'
import SEOHead from './landingComponents/Head'
import Footer from './landingComponents/Footer'
import ApiService from '../services/apiService'
import VideoDemoSection from './landingComponents/VideoDemoSection'

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
            <a href="/offerta" className="text-[#d6001c] hover:text-[#a5001a] font-medium underline-offset-2 hover:underline transition-colors" target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
              пользовательского соглашения
            </a>
            {' '}и{' '}
            <a href="/privacy-policy" className="text-[#d6001c] hover:text-[#a5001a] font-medium underline-offset-2 hover:underline transition-colors" target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
              политики конфиденциальности
            </a>
          </span>
        </label>

        <button
          onClick={handleClick}
          disabled={actualLoading || !privacyAccepted}
          className={`relative w-full sm:w-auto min-w-[240px] px-8 py-4 text-base sm:text-lg font-semibold text-white bg-[#d6001c] hover:bg-[#b50018] disabled:bg-gray-300 disabled:text-gray-500 rounded-xl shadow-lg hover:shadow-xl transform transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:transform-none disabled:shadow-md disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-[#d6001c]/30`}
          aria-label="Начать использовать HH Agent бесплатно"
        >
          <span className={`flex items-center justify-center gap-2 ${actualLoading ? 'opacity-0' : ''}`}>
            Авторизоваться через HeadHunter
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

function SavingsCalculator() {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-lg p-8 max-w-4xl mx-auto">
      <h3 className="text-2xl sm:text-3xl font-bold text-center text-gray-900 mb-8">
        💰 Экономия времени
      </h3>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="text-center p-6 rounded-xl bg-gray-50 border border-gray-200">
          <h4 className="text-lg font-semibold text-gray-700 mb-4">Обычный способ</h4>
          <div className="text-3xl font-bold text-gray-900 mb-2">
            8+ часов
          </div>
          <p className="text-gray-600">100 откликов × 5 мин</p>
        </div>
        
        <div className="text-center p-6 rounded-xl bg-gradient-to-br from-[#d6001c]/5 to-[#d6001c]/10 border border-[#d6001c]/20">
          <h4 className="text-lg font-semibold text-[#d6001c] mb-4">С HH Agent</h4>
          <div className="text-3xl font-bold text-[#d6001c] mb-2">
            200₽ + 5 мин
          </div>
          <p className="text-gray-600">100 откликов автоматически</p>
        </div>
      </div>

      <div className="text-center mt-8 p-6 bg-gradient-to-r from-[#d6001c] to-[#b50018] text-white rounded-xl">
        <div className="text-lg mb-2">Экономия:</div>
        <div className="text-3xl font-bold">
          8+ часов времени
        </div>
        <div className="text-sm mt-2 opacity-90">
          Время для подготовки к собеседованиям
        </div>
      </div>
    </div>
  )
}

function FAQAccordion({ items }: { items: { question: string; answer: string }[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  const toggleAccordion = (index: number) => {
    setOpenIndex(openIndex === index ? null : index)
  }

  return (
    <div className="space-y-3 max-w-4xl mx-auto">
      {items.map((item, index) => (
        <div key={index} className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
          <button onClick={() => toggleAccordion(index)} className="w-full px-6 py-5 text-left flex items-center justify-between hover:bg-gray-50" aria-expanded={openIndex === index} aria-controls={`faq-answer-${index}`}>
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 pr-4">{item.question}</h3>
            <div className="flex-shrink-0">
              <svg className={`w-5 h-5 text-gray-500 transform transition-transform duration-200 ${openIndex === index ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </button>
          <div id={`faq-answer-${index}`} className={`overflow-hidden transition-all duration-300 ease-in-out ${openIndex === index ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
            <div className="px-6 pb-5 pt-0">
              <div className="border-t border-gray-100 pt-4">
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed">{item.answer}</p>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

const PAIN_POINTS = [
  { icon: '😫', title: '60+ минут на каждые 10 откликов', description: 'Время, которое можно потратить на подготовку к собеседованиям' },
  { icon: '📝', title: 'Шаблонные письма = мало приглашений', description: 'HR-менеджеры сразу видят копипаст и игнорируют такие заявки' },
  { icon: '💸', title: 'Упущенные возможности', description: 'Идеальные вакансии проходят мимо из-за слабых откликов' },
  { icon: '✨', title: 'AI пишет лучше человека', description: 'Анализирует резюме и вакансию, создавая уникальное письмо, которое выделяет вас.' }
]

const PROCESS_STEPS = [
  { icon: '🎯', step: 'Шаг 1', title: 'Выбираете вакансии', description: 'Ищите интересные позиции на hh.ru как обычно. Никаких изменений в привычном процессе' },
  { icon: '🤖', step: 'Шаг 2', title: 'AI анализирует', description: 'Система изучает требования вакансии и ваше резюме, создавая идеальное сопроводительное письмо' },
  { icon: '📨', step: 'Шаг 3', title: 'Отправляете отклик', description: 'Редактируете письмо по желанию и отправляете. Получаете в 3 раза больше ответов от работодателей' }
]


const FAQ_ITEMS = [
  { question: 'Как работает AI-генерация писем?', answer: 'AI анализирует каждую вакансию индивидуально и создает уникальное письмо, подчеркивающие именно те навыки и опыт, которые ищет работодатель. Результат: увеличение откликов в 3 раза по сравнению с шаблонными письмами.' },
  { question: 'Насколько безопасно пользоваться приложением?', answer: 'Мы работаем исключительно через официальный API hh.ru. Ваши данные обрабатываются в соответствии с политикой конфиденциальности HeadHunter. Мы не храним ваши пароли и персональную информацию. Никаких блокировок, рисков для аккаунта или нарушений правил hh.ru.' },
  // { question: 'Как используются мои данные?', answer: 'Мы не передаем и не храним Ваши контакты, ФИО и другую личную информацию. Более того, при генерации откликов мы анонимизируем ваши резюме, скрыв названия компаний, периоды работы в соответствии с законом 152-ФЗ РФ. После генерации отклика они восстанавливаются на нашей стороне.' },
  { question: 'Что входит в бесплатный период?', answer: '10 полноценных AI-генераций сопроводительных писем с возможностью редактирования и отправки. Этого достаточно, чтобы оценить качество сервиса и увидеть реальные результаты в виде откликов от работодателей.' },
  { question: 'Можно ли редактировать сгенерированные письма?', answer: 'Конечно! После генерации вы получаете полностью редактируемый текст. Можете изменить любую часть письма, добавить личные детали или скорректировать тон обращения под свой стиль коммуникации.' },
  { question: 'Какого качества получаются письма?', answer: 'AI создает письма профессионального качества, адаптированные под конкретную вакансию и вашу специализацию. Письма содержат релевантные примеры из вашего опыта, показывают понимание требований работодателя и мотивацию к работе в компании.' },
  { question: 'Работает ли сервис со всеми типами вакансий?', answer: 'Да, HH Agent эффективно работает с вакансиями любой специализации - от IT и маркетинга до продаж и управления. AI адаптирует стиль и содержание письма под специфику каждой индустрии и уровень позиции.' },
  { question: 'Будут ли письма похожими друг на друга?', answer: 'Каждое письмо создается индивидуально на основе конкретной вакансии и вашего резюме. AI использует разные подходы, стили изложения и акценты, поэтому даже при отклике на похожие позиции письма будут уникальными.' }
]

function StatsCounter() {
  const [stats, setStats] = useState({
    totalResponses: 0,
    todayResponses: 0,
    isLoading: true,
    error: null as string | null
  })

  useEffect(() => {
    const loadStats = async () => {
      try {
        const apiService = ApiService.getInstance()
        const data = await apiService.getCoverLetterStats()
        
        // Анимация счетчиков
        const animateValue = (setter: (value: number) => void, end: number, duration: number) => {
          const start = 0
          const increment = end / (duration / 10)
          let current = start
          const timer = setInterval(() => {
            current += increment
            if (current >= end) {
              setter(end)
              clearInterval(timer)
            } else {
              setter(Math.floor(current))
            }
          }, 10)
          return timer
        }

        const timer1 = animateValue(
          (value) => setStats(prev => ({ ...prev, totalResponses: value })), 
          data.total_generated, 
          2000
        )
        const timer2 = animateValue(
          (value) => setStats(prev => ({ ...prev, todayResponses: value })), 
          data.last_24h_generated, 
          1500
        )

        setStats(prev => ({ ...prev, isLoading: false }))

        return () => {
          clearInterval(timer1)
          clearInterval(timer2)
        }
      } catch (error) {
        console.error('Failed to load stats:', error)
        setStats(prev => ({ 
          ...prev, 
          isLoading: false, 
          error: 'Не удалось загрузить статистику',
          totalResponses: 0, // fallback values
          todayResponses: 0
        }))
      }
    }

    loadStats()
  }, [])

  if (stats.isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, index) => (
          <div key={index} className="bg-white rounded-xl p-6 text-center border border-gray-200 shadow-sm">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-16 mx-auto"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-white rounded-xl p-6 text-center border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
        <div className="text-2xl sm:text-3xl font-bold text-[#d6001c] mb-2">
          {stats.totalResponses.toLocaleString()}
        </div>
        <div className="text-xs sm:text-sm text-gray-600">откликов создано через HH Agent</div>
      </div>
      <div className="bg-white rounded-xl p-6 text-center border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
        <div className="text-2xl sm:text-3xl font-bold text-[#d6001c] mb-2">
          {stats.todayResponses}
        </div>
        <div className="text-xs sm:text-sm text-gray-600">откликов создано сегодня</div>
      </div>
      <div className="bg-white rounded-xl p-6 text-center border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
        <div className="text-2xl sm:text-3xl font-bold text-[#d6001c] mb-2">3x</div>
        <div className="text-xs sm:text-sm text-gray-600">больше приглашений от работодателей</div>
      </div>
      <div className="bg-white rounded-xl p-6 text-center border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
        <div className="text-2xl sm:text-3xl font-bold text-[#d6001c] mb-2">0₽</div>
        <div className="text-xs sm:text-sm text-gray-600">никаких подписок, начни бесплатно</div>
      </div>
    </div>
  )
}

export default function LandingPage() {
  const [loading, setLoading] = useState(false)

  const handleLogin = async () => {
    setLoading(true)
    try {
      const apiService = ApiService.getInstance()
      const data = await apiService.getAuthUrl()
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

        <main className="flex-grow">
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

              <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-6 sm:p-8 mb-8 sm:mb-10 max-w-4xl mx-auto border border-gray-200">
                <StatsCounter />
              </div>

              <CTASection onLogin={handleLogin} loading={loading} />
            </div>
          </section>

          <VideoDemoSection/>

          {/* Pain Points Section */}
          <section className="bg-gradient-to-br from-gray-100 to-gray-50 py-12 sm:py-16">
            <div className="container mx-auto px-4">
              <div className="max-w-6xl mx-auto text-center">
                <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
                  Устали тратить часы на написание писем?
                </h2>
                <p className="text-lg text-gray-600 mb-10">
                  Каждый день сотни специалистов теряют время на создание сопроводительных писем, получая минимум откликов от работодателей
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {PAIN_POINTS.map((point, index) => (
                    <div key={index} className="bg-white rounded-xl p-6 shadow-lg h-full flex flex-col">
                      <div className="text-4xl mb-4">{point.icon}</div>
                      <h3 className="font-bold text-gray-900 mb-2">{point.title}</h3>
                      <p className="text-sm text-gray-600 flex-grow">{point.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Process Steps */}
          <section className="bg-white py-12 sm:py-16">
            <div className="container mx-auto px-4">
              <div className="text-center mb-10">
                <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
                  Как работает AI-магия
                </h2>
                <p className="text-lg text-gray-600">
                  Простой процесс из 3 шагов превращает поиск работы в эффективную систему
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 max-w-5xl mx-auto">
                {PROCESS_STEPS.map((step, index) => (
                  <article key={index} className="relative bg-gradient-to-br from-white to-gray-50 p-6 sm:p-8 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200">
                    <div className="text-3xl sm:text-4xl mb-3">{step.icon}</div>
                    <div className="text-sm font-semibold text-[#d6001c] mb-2">{step.step}</div>
                    <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-3">{step.title}</h3>
                    <p className="text-sm sm:text-base text-gray-600">{step.description}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          {/* Savings Calculator */}
          <section className="container mx-auto px-4 py-12 sm:py-16">
            <SavingsCalculator />
          </section>

          {/* FAQ Section */}
          <section className="bg-gray-100 py-12 sm:py-16" aria-labelledby="faq-section">
            <div className="container mx-auto px-4">
              <h2 id="faq-section" className="text-2xl sm:text-3xl font-bold text-center text-gray-900 mb-8 sm:mb-12">
                Часто задаваемые вопросы
              </h2>
              <FAQAccordion items={FAQ_ITEMS} />
            </div>
          </section>

          {/* Personal Message */}
          <section className="container mx-auto px-4 py-12 sm:py-16" aria-labelledby="personal-message">
            <div className="bg-white rounded-xl p-6 sm:p-10 shadow-lg max-w-4xl mx-auto">
              <h2 id="personal-message" className="text-2xl sm:text-3xl font-bold text-gray-900 text-center mb-6 sm:mb-8">
                Слово от создателя
              </h2>
              <div className="text-gray-500 space-y-4 text-sm sm:text-base lg:text-lg leading-relaxed">
                <p>Привет! Я создал HH Agent, чтобы помочь таким же людям, как и я, найти работу своей мечты.</p>
                <p>Я искренне рад предоставить вам этот сервис. Чем больше людей будут пользоваться сервисом, тем лучше я смогу его сделать.</p>
                <p><strong>Пользуйтесь, и я обещаю улучшать генерацию каждый день!</strong></p>
                <p><strong>Моя цель — не просто создать сервис для генерации, а сделать настоящего AI убийцу рынка поиска работы </strong> <span style={{textDecoration:'line-through', fontSize:'12px'}}>и профессии hr</span></p>
                <p>Юзайте, <a href="#" className="text-[#d6001c] hover:text-[#c5001a] transition-colors font-medium ml-1">делитесь обратной связью!</a></p>
              </div>
            </div>
          </section>

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