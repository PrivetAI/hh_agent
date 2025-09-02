import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-12 sm:mt-16 py-6 sm:py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        {/* Contact and Company Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">О сервисе</h3>
            <p className="text-sm text-gray-600 mb-2">
              HH Agent — умный помощник для поиска работы на hh.ru с AI-генерацией сопроводительных писем
            </p>
            <p className="text-sm text-gray-500">
              © 2025 HH Agent
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Контакты</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <p>ИНН: 231136137506</p>
              <p>Email: <a href="mailto:eliseenko1viktor@gmail.com" className="text-[#d6001c] hover:text-[#c5001a]">eliseenko1viktor@gmail.com</a></p>
            </div>
          </div>
          
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Правовая информация</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/payment-terms" className="text-gray-600 hover:text-[#d6001c] transition-colors">
                  Условия оказания услуг
                </Link>
              </li>
              <li>
                <Link href="/offerta" className="text-gray-600 hover:text-[#d6001c] transition-colors">
                  Публичная оферта
                </Link>
              </li>
              <li>
                <Link href="/privacy-policy" className="text-gray-600 hover:text-[#d6001c] transition-colors">
                  Политика конфиденциальности
                </Link>
              </li>
            </ul>
          </div>
        </div>
        
        {/* Partner Link */}
        <div className="border-t border-gray-200 pt-4 text-center">
          <p className="text-sm text-gray-500">
            Есть вопросы по сервису или нужна автоматизация для бизнеса?{' '}
            <a 
              href="https://t.me/reetry" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-[#d6001c] hover:text-[#c5001a] transition-colors font-medium"
            >
              пиши в Telegram
            </a>
          </p>
        </div>
      </div>
    </footer>
  )
}