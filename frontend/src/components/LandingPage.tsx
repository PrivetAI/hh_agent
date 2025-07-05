'use client'
import { useState } from 'react'
import SEOHead from './Head'
import Footer from './Footer'
import Link from 'next/link'

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
      
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 sm:py-6 flex items-center justify-center">
            <div className="flex items-center space-x-2">
              <div className="text-[#d6001c] font-bold text-2xl sm:text-3xl">hh</div>
              <div className="text-gray-800 font-bold text-xl sm:text-2xl">агент</div>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-16">
          <div className="text-center mb-12 sm:mb-16">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 sm:mb-6 leading-tight px-2">
              Умный поиск работы
              <br />
              <span className="text-[#d6001c]">на новом уровне</span>
            </h1>
            
            <p className="text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto mb-6 sm:mb-8 leading-relaxed px-4">
              AI создает персонализированные сопроводительные письма для каждой вакансии на hh.ru, 
              увеличивая отклик работодателей в 3 раза
            </p>

            <div className="bg-orange-100 border border-orange-200 text-orange-800 px-4 sm:px-6 py-3 rounded-lg text-base sm:text-lg font-medium inline-block mb-8 sm:mb-10 mx-4">
              🎯 10 бесплатных откликов для новых пользователей
            </div>

            <button 
              onClick={handleLogin}
              disabled={loading}
              className="bg-[#d6001c] hover:bg-[#c5001a] text-white px-8 sm:px-10 py-3 sm:py-4 text-lg sm:text-xl font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed shadow-lg transition-colors w-full sm:w-auto max-w-xs sm:max-w-none mx-auto"
              aria-label="Начать использовать HH Agent бесплатно"
            >
              {loading ? (
                <div className="flex items-center justify-center space-x-3">
                  <div className="hh-loader" aria-hidden="true"></div>
                  <span>Подключение...</span>
                </div>
              ) : (
                'Начать бесплатно'
              )}
            </button>
          </div>

          {/* Demo Image */}
          <section className="mb-12 sm:mb-16" aria-labelledby="demo-section">
            <h2 id="demo-section" className="sr-only">Демонстрация работы HH Agent</h2>
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden max-w-4xl mx-auto">
              <img 
                src="/image.png" 
                alt="Демонстрация интерфейса HH Agent - создание персонализированных сопроводительных писем для вакансий на hh.ru"
                className="w-full h-auto"
                width="800"
                height="600"
                loading="lazy"
              />
            </div>
          </section>

          {/* Process Steps */}
          <section className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 sm:gap-8 mb-12 sm:mb-16" aria-labelledby="process-section">
            <h2 id="process-section" className="sr-only">Как работает HH Agent</h2>
            
            <article className="bg-white p-6 sm:p-8 rounded-xl shadow-sm border border-gray-200 text-center">
              <div className="text-3xl sm:text-4xl mb-3 sm:mb-4" aria-hidden="true">🎯</div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2 sm:mb-3">Выбираете вакансии</h3>
              <p className="text-sm sm:text-base text-gray-600">Ищите интересные позиции на hh.ru как обычно</p>
            </article>

            <article className="bg-white p-6 sm:p-8 rounded-xl shadow-sm border border-gray-200 text-center">
              <div className="text-3xl sm:text-4xl mb-3 sm:mb-4" aria-hidden="true">🤖</div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2 sm:mb-3">AI анализирует</h3>
              <p className="text-sm sm:text-base text-gray-600">Система изучает вакансию и ваше резюме за 3 секунды</p>
            </article>

            <article className="bg-white p-6 sm:p-8 rounded-xl shadow-sm border border-gray-200 text-center sm:col-span-2 md:col-span-1">
              <div className="text-3xl sm:text-4xl mb-3 sm:mb-4" aria-hidden="true">📨</div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2 sm:mb-3">Отправляете отклик</h3>
              <p className="text-sm sm:text-base text-gray-600">Уникальное письмо автоматически прикрепляется к отклику</p>
            </article>
          </section>
          {/* Features Grid */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 mb-12 sm:mb-16" aria-labelledby="features-section">
            <h2 id="features-section" className="sr-only">Преимущества HH Agent</h2>
            
            <div className="space-y-4 sm:space-y-6">
              <article className="bg-white p-4 sm:p-6 rounded-xl shadow-sm border border-gray-200">
                <div className="flex items-start space-x-3 sm:space-x-4">
                  <div className="text-2xl sm:text-3xl flex-shrink-0" aria-hidden="true">⚡</div>
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2">Молниеносная скорость</h3>
                    <p className="text-sm sm:text-base text-gray-600">Забудьте о часах написания писем. AI создает качественный текст за 3 секунды</p>
                  </div>
                </div>
              </article>

              <article className="bg-white p-4 sm:p-6 rounded-xl shadow-sm border border-gray-200">
                <div className="flex items-start space-x-3 sm:space-x-4">
                  <div className="text-2xl sm:text-3xl flex-shrink-0" aria-hidden="true">🎨</div>
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2">Идеальная персонализация</h3>
                    <p className="text-sm sm:text-base text-gray-600">Каждое письмо уникально и точно соответствует требованиям конкретной вакансии</p>
                  </div>
                </div>
              </article>
            </div>

            <div className="space-y-4 sm:space-y-6">
              <article className="bg-white p-4 sm:p-6 rounded-xl shadow-sm border border-gray-200">
                <div className="flex items-start space-x-3 sm:space-x-4">
                  <div className="text-2xl sm:text-3xl flex-shrink-0" aria-hidden="true">🔒</div>
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2">Максимальная безопасность</h3>
                    <p className="text-sm sm:text-base text-gray-600">Работаем только через официальный API hh.ru. Все официально и безопасно</p>
                  </div>
                </div>
              </article>

              <article className="bg-white p-4 sm:p-6 rounded-xl shadow-sm border border-gray-200">
                <div className="flex items-start space-x-3 sm:space-x-4">
                  <div className="text-2xl sm:text-3xl flex-shrink-0" aria-hidden="true">✏️</div>
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2">Полный контроль</h3>
                    <p className="text-sm sm:text-base text-gray-600">Редактируйте и дорабатывайте письма перед отправкой по своему усмотрению</p>
                  </div>
                </div>
              </article>
            </div>
          </section>

          <section className="mb-12 sm:mb-16 bg-gradient-to-r from-red-50 to-orange-50 rounded-xl p-6 sm:p-10 shadow-sm border border-red-200" aria-labelledby="personal-message">
            <h2 id="personal-message" className="text-2xl sm:text-3xl font-bold text-gray-900 text-center mb-6">Слово от создателя</h2>
            
            <div className="max-w-3xl mx-auto text-gray-700 space-y-4">
              <p className="text-base sm:text-lg leading-relaxed">
                Привет! Я создал HH Agent, чтобы помочь таким же людям, как и я, найти работу своей мечты.
              </p>
              
              <p className="text-base sm:text-lg leading-relaxed">
                Я искренне рад предоставить вам этот сервис. Честно говоря, я бы хотел сделать его еще дешевле — и работаю над этим каждый день. 
                Чем больше людей будут пользоваться сервисом, тем доступнее я смогу его сделать.
              </p>
              
              <p className="text-base sm:text-lg leading-relaxed">
                <strong>Пользуйтесь, и я обещаю улучшать генерацию каждый день!</strong>
              </p>
                <p className="text-base sm:text-lg leading-relaxed">
                 <strong> Моя цель — не просто создать сервис для генерации, а сделать настоящего ai убийцу рынка поиска работы... </strong>
              </p>
              
              <p className="text-base sm:text-lg leading-relaxed">
                Юзайте, делитесь обратной связью! //google form link
              </p>
            </div>
          </section>


          {/* FAQ */}
          <section className="bg-white rounded-xl p-6 sm:p-10 shadow-sm border border-gray-200" aria-labelledby="faq-section">
            <h2 id="faq-section" className="text-2xl sm:text-3xl font-bold text-gray-900 text-center mb-8 sm:mb-10">Популярные вопросы</h2>
            
            <div className="space-y-4 sm:space-y-6 max-w-4xl mx-auto">
              <article className="border border-gray-200 rounded-lg p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2 sm:mb-3">Как работает AI-генерация писем?</h3>
                <p className="text-sm sm:text-base text-gray-600">Система анализирует описание вакансии, требования и ваше резюме, создавая персонализированное письмо с акцентом на ваши сильные стороны</p>
              </article>
              
              <article className="border border-gray-200 rounded-lg p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2 sm:mb-3">Насколько безопасно пользоваться приложением?</h3>
                <p className="text-sm sm:text-base text-gray-600">Используем только официальный OAuth API HeadHunter. Никаких блокировок и рисков</p>
              </article>
              
              <article className="border border-gray-200 rounded-lg p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2 sm:mb-3">Что входит в бесплатный период?</h3>
                <p className="text-sm sm:text-base text-gray-600">10 полноценных AI-генераций сопроводительных писем. Этого хватит, чтобы оценить качество и эффективность сервиса</p>
              </article>
            </div>
          </section>

          <div className="text-center mt-12 sm:mt-16">
            <button 
              onClick={handleLogin}
              disabled={loading}
              className="bg-[#d6001c] hover:bg-[#c5001a] text-white px-8 sm:px-10 py-3 sm:py-4 text-lg sm:text-xl font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed shadow-lg transition-colors w-full sm:w-auto max-w-xs sm:max-w-none mx-auto"
              aria-label="Начать использовать HH Agent бесплатно"
            >
              {loading ? (
                <div className="flex items-center justify-center space-x-3">
                  <div className="hh-loader" aria-hidden="true"></div>
                  <span>Подключение...</span>
                </div>
              ) : (
                'Начать бесплатно'
              )}
            </button> 
          </div>
        </main>

        <Footer />

        <style jsx>{`
          .hh-loader {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </>
  )
}