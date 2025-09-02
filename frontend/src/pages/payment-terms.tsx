import SEOHead from '../components/landingComponents/Head'
import Link from 'next/link'

export default function PaymentTerms() {
  return (
    <>
      <SEOHead
        title="Условия оплаты и доставки - HH Agent"
        description="Правила оказания услуг, условия оплаты и возврата средств сервиса HH Agent"
        noindex={true}
      />

      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="mt-2 mb-4 space-x-4">
            <Link href="/" className="text-[#d6001c] hover:text-[#c5001a]">
              ← Вернуться на главную
            </Link>
          </div>
          <h1 className="text-3xl font-bold mb-8">Условия оказания услуг</h1>

          <div className="bg-white rounded-lg shadow-sm p-8 space-y-8">
            <section>
              <h2 className="text-2xl font-semibold mb-4">Описание услуги</h2>
              <div className="space-y-4 text-gray-700">
                <p>
                  <strong>HH Agent</strong> — это информационно-консультационный сервис для автоматизации
                  поиска работы на платформе HeadHunter (hh.ru).
                </p>

                <div>
                  <h3 className="text-lg font-semibold mb-2">Основные функции:</h3>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Поиск и фильтрация вакансий через API hh.ru</li>
                    <li>Автоматическая генерация персонализированных сопроводительных писем</li>
                    <li>Отправка откликов на вакансии</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">Тарифы и цены:</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="mb-3">Стоимость услуг рассчитывается в токенах. 1 токен = 1 отклик на вакансию.</p>
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2">Пакет</th>
                          <th className="text-left py-2">Количество токенов</th>
                          <th className="text-left py-2">Цена</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b">
                          <td className="py-2">Мини</td>
                          <td className="py-2">50 токенов</td>
                          <td className="py-2">199 ₽</td>
                        </tr>
                        <tr className="border-b">
                          <td className="py-2">Стандарт</td>
                          <td className="py-2">100 токенов</td>
                          <td className="py-2">299 ₽</td>
                        </tr>
                        <tr className="border-b">
                          <td className="py-2">Профи</td>
                          <td className="py-2">200 токенов</td>
                          <td className="py-2">499 ₽</td>
                        </tr>
                        <tr>
                          <td className="py-2">Премиум</td>
                          <td className="py-2">500 токенов</td>
                          <td className="py-2">999 ₽</td>
                        </tr>
                      </tbody>
                    </table>
                    <p className="mt-3 text-sm text-gray-600">
                      * Новым пользователям предоставляется 10 бесплатных токенов при регистрации
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold mb-4">Порядок оказания услуг</h2>
              <ol className="list-decimal list-inside space-y-3 text-gray-700">
                <li>
                  <strong>Регистрация:</strong> Авторизация через аккаунт HeadHunter с использованием OAuth 2.0
                </li>
                <li>
                  <strong>Выбор резюме:</strong> Выбор активного резюме для генерации откликов
                </li>
                <li>
                  <strong>Поиск вакансий:</strong> Использование фильтров для поиска подходящих вакансий
                </li>
                <li>
                  <strong>Генерация писем:</strong> AI создает персонализированное письмо за 3-5 секунд
                </li>
                <li>
                  <strong>Отправка отклика:</strong> Отправка резюме с сопроводительным письмом работодателю
                </li>
              </ol>
            </section>

            <section>
              <h2 className="text-2xl font-semibold mb-4">Сроки оказания услуг</h2>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>Генерация сопроводительного письма: до 10 сек</li>
                <li>Отправка отклика: мгновенно после подтверждения</li>
                <li>Доступ к сервису: круглосуточно 24/7</li>
                <li>Техническая поддержка: в рабочие дни с 9:00 до 18:00 МСК</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold mb-4">Условия оплаты</h2>
              <div className="space-y-3 text-gray-700">
                <p><strong>Способы оплаты:</strong></p>
                <ul className="list-disc list-inside ml-4 space-y-2">
                  <li>Система быстрых платежей (СБП)</li>
                  <li>Банковские карты (Visa, Mastercard, МИР)</li>
                </ul>

                <p><strong>Порядок оплаты:</strong></p>
                <ol className="list-decimal list-inside ml-4 space-y-2">
                  <li>Выберите пакет токенов в личном кабинете</li>
                  <li>Нажмите кнопку "Оплатить"</li>
                  <li>Вы будете перенаправлены на защищенную страницу оплаты</li>
                  <li>После успешной оплаты токены автоматически зачисляются на баланс</li>
                </ol>

                <p className="mt-3">
                  <strong>Безопасность платежей:</strong> Все платежи обрабатываются через защищенное
                  соединение. Мы не храним данные банковских карт.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold mb-4">Правила возврата</h2>
              <div className="space-y-3 text-gray-700">
                <p>
                  В соответствии с Законом РФ "О защите прав потребителей", вы имеете право на возврат
                  средств за неиспользованные услуги.
                </p>

                <p><strong>Условия возврата:</strong></p>
                <ul className="list-disc list-inside ml-4 space-y-2">
                  <li>Возврат возможен за неиспользованные токены</li>
                  <li>Заявка на возврат подается в течение 14 дней с момента покупки</li>
                  <li>Использованные токены возврату не подлежат</li>
                </ul>

                <p><strong>Процедура возврата:</strong></p>
                <ol className="list-decimal list-inside ml-4 space-y-2">
                  <li>Направьте заявление на email: eliseenko1viktor@gmail.com</li>
                  <li>Укажите номер заказа и причину возврата</li>
                  <li>Возврат осуществляется в течение 10 рабочих дней</li>
                  <li>Средства возвращаются тем же способом, которым была произведена оплата</li>
                </ol>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold mb-4">Ограничения сервиса</h2>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>Лимит HeadHunter: не более 200 откликов в сутки на один аккаунт</li>
                <li>Токены не имеют срока действия, но могут быть отозваны администратором</li>
                <li>Передача токенов между аккаунтами невозможна</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold mb-4">Контактная информация</h2>
              <div className="bg-gray-50 p-4 rounded-lg text-gray-700">
                <p><strong>Исполнитель:</strong> Самозанятый Елисеенко Виктор Александрович</p>
                <p><strong>ИНН:</strong> 231136137506</p>
                <p><strong>Email:</strong> eliseenko1viktor@gmail.com</p>
                <p><strong>Телефон:</strong> +7 918 244-54-06</p>
                <p><strong>График работы поддержки:</strong> Пн-Пт с 9:00 до 18:00 МСК</p>
              </div>
            </section>
          </div>

          <div className="mt-8 text-center space-x-4">
            <Link href="/" className="text-[#d6001c] hover:text-[#c5001a]">
              ← Вернуться на главную
            </Link>
            <Link href="/offerta" className="text-[#d6001c] hover:text-[#c5001a]">
              Публичная оферта
            </Link>
            <Link href="/privacy-policy" className="text-[#d6001c] hover:text-[#c5001a]">
              Политика конфиденциальности
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}