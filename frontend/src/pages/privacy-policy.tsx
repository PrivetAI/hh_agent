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
              <p className="text-gray-700">
                Настоящая политика обработки персональных данных составлена в соответствии с требованиями 
                Федерального закона от 27.07.2006. №152-ФЗ «О персональных данных» и определяет порядок 
                обработки персональных данных и меры по обеспечению безопасности персональных данных.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">2. Оператор персональных данных</h2>
              <p className="text-gray-700">
                Оператор: Самозанятый Елисеенко Виктор Александрович<br/>
                ИНН: 231136137506<br/>
                Email: eliseenko1viktor@gmail.com<br/>
                Телефон: +7 918 244-54-06
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">3. Цели обработки персональных данных</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>Предоставление доступа к сервису HH Agent</li>
                <li>Авторизация через API HeadHunter</li>
                <li>Оказание информационно-консультационных услуг</li>
                <li>Обработка платежей за услуги</li>
                <li>Направление уведомлений об услугах</li>
                <li>Исполнение требований законодательства РФ</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">4. Правовые основания обработки</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>Договор на оказание услуг (публичная оферта)</li>
                <li>Согласие на обработку персональных данных</li>
                <li>Федеральный закон "О персональных данных" от 27.07.2006 N 152-ФЗ</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">5. Обрабатываемые персональные данные</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>Фамилия, имя, отчество</li>
                <li>Электронная почта</li>
                <li>Номер телефона</li>
                <li>Данные резюме с HeadHunter</li>
                <li>История откликов на вакансии</li>
                <li>Платежная информация</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">6. Порядок и условия обработки</h2>
              <p className="text-gray-700 mb-3">
                Обработка персональных данных осуществляется с согласия субъекта персональных данных 
                на обработку его персональных данных.
              </p>
              <p className="text-gray-700">
                Оператор обрабатывает персональные данные следующими способами:
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 mt-2">
                <li>Сбор, запись, систематизация</li>
                <li>Накопление, хранение, уточнение</li>
                <li>Извлечение, использование</li>
                <li>Удаление, уничтожение</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">7. Защита персональных данных</h2>
              <p className="text-gray-700">
                Оператор принимает необходимые организационные и технические меры для защиты 
                персональных данных от неправомерного или случайного доступа, уничтожения, 
                изменения, блокирования, копирования, предоставления, распространения.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">8. Права субъекта персональных данных</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2">
                <li>Получить информацию об обработке персональных данных</li>
                <li>Потребовать уточнения персональных данных</li>
                <li>Потребовать удаления персональных данных</li>
                <li>Отозвать согласие на обработку персональных данных</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">9. Сроки обработки</h2>
              <p className="text-gray-700">
                Персональные данные обрабатываются до отзыва согласия субъектом персональных данных. 
                После прекращения договорных отношений персональные данные хранятся в течение 
                срока, установленного законодательством РФ.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3">10. Контакты</h2>
              <p className="text-gray-700">
                По вопросам обработки персональных данных вы можете обратиться:<br/>
                Email: eliseenko1viktor@gmail.com<br/>
                Телефон: +7 918 244-54-06
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