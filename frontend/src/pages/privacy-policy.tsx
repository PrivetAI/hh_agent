import SEOHead from '../components/Head'
import Link from 'next/link'

export default function PrivacyPolicy() {
  return (
    <>
      <SEOHead 
        title="Политика обработки персональных данных - HH Agent"
        description="Политика обработки персональных данных сервиса HH Agent"
        noindex={true}
      />
      
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-3xl font-bold mb-8">Политика обработки персональных данных</h1>
          
          <div className="bg-white rounded-lg shadow-sm p-8 space-y-6">
            <section>
              <h2 className="text-xl font-semibold mb-3">1. Общие положения</h2>
              <p className="text-gray-700 mb-3">
                1.1. Настоящая Политика обработки персональных данных (далее – «Политика») разработана в соответствии с Федеральным законом от 27.07.2006 № 152‑ФЗ «О персональных данных» (далее – «Закон 152‑ФЗ») и иными нормативными актами Российской Федерации.
              </p>
              <p className="text-gray-700">
                1.2. Цель Политики – обеспечить прозрачность, законность и безопасность обработки персональных данных пользователей сервиса AI‑генерации сопроводительных писем (далее – «Сервис»).
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">2. Основные терминологические понятия</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li><strong>Персональные данные</strong> – любая информация, относящаяся к прямо или косвенно определённому или определяемому Субъекту.</li>
                <li><strong>Оператор</strong> – физическое лицо, организующее и осуществляющее обработку персональных данных.</li>
                <li><strong>Обработка</strong> – любое действие с персональными данными: сбор, запись, систематизация, накопление, хранение, уточнение, извлечение, использование, передача, удаление и уничтожение.</li>
                <li><strong>Провайдер ИИ</strong> – внешний сервис, принимающий текст резюме для генерации сопроводительных писем.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">3. Оператор персональных данных</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>ФИО: Елисеенко Виктор Александрович</li>
                <li>Статус: Самозанятый</li>
                <li>ИНН: 231136137506</li>
                <li>Электронная почта: eliseenko1viktor@gmail.com</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">4. Принципы и правовые основания обработки</h2>
              <p className="text-gray-700 mb-3">
                4.1. Принципы обработки: законность, ограничение целей, минимизация объёма, точность, хранение не дольше необходимого.
              </p>
              <p className="text-gray-700 mb-2">4.2. Правовые основания:</p>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>договор на оказание услуг (публичная оферта);</li>
                <li>добровольное, информированное согласие Субъекта;</li>
                <li>нормы Закона 152‑ФЗ.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">5. Цели обработки персональных данных</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>Приём и хранение текста резюме пользователя.</li>
                <li>Генерация сопроводительных писем на основе предоставленного текста резюме.</li>
                <li>Направление готовых писем пользователю через интерфейс Сервиса.</li>
                <li>Информационные уведомления о статусе обработки запроса.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">6. Категории обрабатываемых данных</h2>
              <p className="text-gray-700 mb-3">
                6.1. Оператор обрабатывает исключительно полный текст резюме, предоставляемый пользователем.
              </p>
              <p className="text-gray-700 mb-2">6.2. Оператор не запрашивает и не хранит:</p>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>ФИО;</li>
                <li>адрес электронной почты;</li>
                <li>номера телефонов;</li>
                <li>платежную информацию (оплата услуг осуществляется через сторонний сервис Robokassa, который самостоятельно обрабатывает данные).</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">7. Передача персональных данных третьим лицам</h2>
              <p className="text-gray-700 mb-3">
                7.1. Для генерации сопроводительных писем Оператор передаёт только текст резюме внешним провайдерам ИИ.
              </p>
              <p className="text-gray-700 mb-3">
                7.2. Оператор не заключает отдельных соглашений об обработке персональных данных с провайдерами ИИ: передача текста осуществляется в рамках условий публично доступных пользовательских соглашений провайдеров.
              </p>
              <p className="text-gray-700">
                7.3. Объём передаваемых данных ограничен текстом резюме и не содержит платежных сведений.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">8. Сроки хранения и удаления данных</h2>
              <p className="text-gray-700 mb-3">
                8.1. Текст резюме хранится до завершения услуги и не дольше 30 календарных дней, если иное не оговорено пользователем.
              </p>
              <p className="text-gray-700">
                8.2. По запросу пользователя данные удаляются досрочно.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">9. Права субъектов персональных данных</h2>
              <p className="text-gray-700 mb-2">9.1. Субъект имеет право:</p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mb-3">
                <li>получить подтверждение факта обработки своего резюме;</li>
                <li>запросить копию или удаление текста резюме;</li>
                <li>отозвать согласие на обработку текста резюме.</li>
              </ul>
              <p className="text-gray-700">
                9.2. Запросы направляются на электронную почту Оператора. Ответ предоставляется в течение 30 календарных дней.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">10. Организационные и технические меры безопасности</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>Защищённые каналы передачи (HTTPS);</li>
                <li>Ограничение доступа сотрудников;</li>
                <li>Резервное копирование и шифрование данных;</li>
                <li>Регулярный мониторинг и обновление систем безопасности.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">11. Ответственность</h2>
              <p className="text-gray-700">
                Оператор несёт ответственность за соблюдение законодательства РФ о персональных данных.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">12. Изменения Политики</h2>
              <p className="text-gray-700">
                Изменения публикуются на сайте Сервиса и вступают в силу с момента публикации.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">13. Контактная информация</h2>
              <p className="text-gray-700">
                Электронная почта: eliseenko1viktor@gmail.com
              </p>
              <p className="text-gray-700 mt-4 italic">
                Дата последнего обновления: 13 июля 2025 г.
              </p>
            </section>
          </div>

          <div className="mt-8 text-center">
            <Link href="/" className="text-[#d6001c] hover:text-[#c5001a]">
              ← Вернуться на главную
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}