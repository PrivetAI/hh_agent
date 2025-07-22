import { useEffect, useState } from 'react'
import { LoadingButton } from './ui/LoadingButton'
import { Vacancy } from '../types'
interface TableProps {
  vacancies: Vacancy[]
  onVacancyUpdate: (id: string, updates: Partial<Vacancy>) => void
  onGenerateAll: () => void
  onSendSelected: () => void
  onGenerateAndSend: () => void
  loading?: string
  generatingId?: string
}

export default function VacanciesTable({
  vacancies,
  onVacancyUpdate,
  onGenerateAll,
  onSendSelected,
  onGenerateAndSend,
  loading,
  generatingId
}: TableProps) {
  const [isMobile, setIsMobile] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [modalVacancy, setModalVacancy] = useState<Vacancy | null>(null)
  
  const filteredVacancies = isGenerating ? vacancies.filter(v => v.selected) : vacancies
  
  const selectedCount = vacancies.filter(v => v.selected && !v.aiLetter).length
  const toSentCount = vacancies.filter(v => v.selected && v.aiLetter).length
  const selectedNotSended = vacancies.filter(v => v.selected).length
  const allSelected = filteredVacancies.length > 0 && filteredVacancies.every(v => v.selected !== false)

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    if (loading === 'generate' || loading === 'generate-and-send' || generatingId) {
      setIsGenerating(true)
    }
  }, [loading, generatingId])

  const toggleAll = () => {
    const newValue = !allSelected
    filteredVacancies.forEach(v => onVacancyUpdate(v.id, { selected: newValue }))
  }

  const toggleVacancy = (vacancyId: string) => {
    const vacancy = filteredVacancies.find(v => v.id === vacancyId)
    if (vacancy) {
      onVacancyUpdate(vacancyId, { selected: !vacancy.selected })
    }
  }

  const formatSalary = (salary?: any) => {
    if (!salary) return null
    const parts = []
    if (salary.from) parts.push(`от ${salary.from.toLocaleString()}`)
    if (salary.to) parts.push(`до ${salary.to.toLocaleString()}`)
    if (salary.currency) parts.push(salary.currency)
    return parts.join(' ')
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'Сегодня'
    if (diffDays === 1) return 'Вчера'
    if (diffDays < 7) return `${diffDays} дней назад`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} недель назад`
    return `${Math.floor(diffDays / 30)} месяцев назад`
  }

  const generateAll = () => {
    onGenerateAll()
  }

  const openModal = (vacancy: Vacancy, e: any) => {
    e.stopPropagation()
    setModalVacancy(vacancy)
  }

  const closeModal = () => {
    setModalVacancy(null)
  }

  const isGeneratingState = loading === 'generate' || !!generatingId
  const isSending = loading === 'send'
  const isGeneratingAndSending = loading === 'generate-and-send'

  if (isMobile) {
    return (
      <>
        {filteredVacancies.length > 0 && (
          <div className="hh-card p-4 mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-[#232529]">
              {isGenerating ? `Выбрано: ${filteredVacancies.length}` : `Найдено: ${filteredVacancies.length}`}
            </h3>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={toggleAll}
                className="hh-checkbox"
                id="select-all-mobile"
              />
              <label htmlFor="select-all-mobile" className="text-sm text-[#666666] cursor-pointer">
                Выбрать все
              </label>
            </div>
          </div>
        )}

        <div className="space-y-4 mb-16">
          {filteredVacancies.map(vacancy => (
            <div 
              key={vacancy.id} 
              className={`hh-card p-4 cursor-pointer ${
                vacancy.selected ? 'bg-green-50' : 'hover:bg-gray-50'
              }`}
              onClick={() => toggleVacancy(vacancy.id)}
            >
              <div className="flex items-start justify-between mb-3">
                <input
                  type="checkbox"
                  checked={vacancy.selected !== false}
                  onChange={e => e.stopPropagation()}
                  className="hh-checkbox mt-1 pointer-events-none"
                />
                <div className="flex-1 ml-3">
                  <a
                    href={`https://hh.ru/vacancy/${vacancy.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hh-link font-medium text-sm"
                    onClick={e => e.stopPropagation()}
                  >
                    {vacancy.name}
                  </a>
                </div>
              </div>

              <div className="space-y-2 text-sm text-[#999999] mb-3">
                <div className="font-medium text-[#232529]">{vacancy.employer?.name}</div>
                {vacancy.salary && (
                  <div className="text-[#4bb34b] font-medium">
                    {formatSalary(vacancy.salary)}
                  </div>
                )}
                <div>{vacancy.area?.name}</div>
                {(vacancy.employment?.name || vacancy.schedule?.name) && (
                  <div className="flex flex-wrap gap-2 text-xs">
                    {vacancy.employment?.name && <span>{vacancy.employment.name}</span>}
                    {vacancy.schedule?.name && <span>{vacancy.schedule.name}</span>}
                  </div>
                )}
                {vacancy.published_at && (
                  <div className="text-xs">{formatDate(vacancy.published_at)}</div>
                )}
              </div>

              {vacancy.description && (
                <p 
                  className="text-sm text-[#666666] mb-3 line-clamp-10 cursor-pointer hover:text-[#4bb34b]"
                  onClick={e => openModal(vacancy, e)}
                >
                  {vacancy.description}
                </p>
              )}

              {generatingId === vacancy.id ? (
                <div className="flex justify-center items-center h-[240px] bg-[#f4f4f5] rounded">
                  <span className="area-loader" />
                </div>
              ) : vacancy.aiLetter ? (
                <textarea
                  value={vacancy.aiLetter}
                  onChange={e => {
                    e.stopPropagation()
                    onVacancyUpdate(vacancy.id, { aiLetter: e.target.value })
                  }}
                  className="hh-input text-sm resize-none"
                  rows={10}
                  onClick={e => e.stopPropagation()}
                />
              ) : null}
            </div>
          ))}

          {filteredVacancies.length === 0 && (
            <div className="hh-card p-12 text-center text-[#999999]">
              {isGenerating ? 'Нет выбранных вакансий' : 'Используйте фильтры выше для поиска вакансий'}
            </div>
          )}
        </div>

        {filteredVacancies.length > 0 && (
          <div className="text-center mb-20 mt-6">
            <a 
              href="#filters" 
              className="inline-flex items-center gap-1 text-[#d6001c] hover:text-[#b8001a] text-sm"
            >
              ↑ Наверх к фильтрам
            </a>
          </div>
        )}

        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#e7e7e7] p-3">
          <div className="flex gap-2 mb-2">
            <LoadingButton
              onClick={generateAll}
              loading={isGeneratingState}
              disabled={isGeneratingState || isGeneratingAndSending || selectedCount === 0}
              className="hh-btn hh-btn-primary text-xs flex-1"
            >
              Создать отклики ({selectedCount})
            </LoadingButton>
            <LoadingButton
              onClick={onSendSelected}
              loading={isSending}
              disabled={isSending || isGeneratingAndSending || toSentCount === 0}
              className="hh-btn hh-btn-success text-xs flex-1"
            >
              Отправить ({toSentCount})
            </LoadingButton>
          </div>
          <LoadingButton
            onClick={onGenerateAndSend}
            loading={isGeneratingAndSending}
            disabled={isGeneratingAndSending || isGeneratingState || isSending || selectedNotSended === 0}
            className="hh-btn hh-btn-warning text-xs w-full"
          >
            {isGeneratingAndSending 
              ? (loading === 'generate-and-send' ? 'Создание откликов...' : 'Отправка откликов...') 
              : `Создать и отправить (${selectedNotSended})`
            }
          </LoadingButton>
        </div>

        {modalVacancy && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={closeModal}
          >
            <div 
              className="bg-white rounded-lg max-w-4xl max-h-[80vh] overflow-auto p-6"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-[#232529] mb-2">{modalVacancy.name}</h2>
                  <p className="text-lg text-[#666666]">{modalVacancy.employer?.name}</p>
                </div>
                <button 
                  onClick={closeModal}
                  className="text-2xl text-[#999999] hover:text-[#232529] leading-none"
                >
                  ×
                </button>
              </div>
              <div className="prose max-w-none">
                <div dangerouslySetInnerHTML={{ __html: modalVacancy.description || '' }} />
              </div>
            </div>
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <div className="hh-card overflow-hidden">
        <div className="p-4 border-b border-[#e7e7e7] flex justify-between items-center">
          <h3 className="text-lg font-semibold text-[#232529]">
            {isGenerating ? `Выбрано вакансий: ${filteredVacancies.length}` : `Найдено вакансий: ${filteredVacancies.length}`}
          </h3>
          <div className="flex gap-3">
            <LoadingButton
              onClick={generateAll}
              loading={isGeneratingState}
              disabled={isGeneratingState || isGeneratingAndSending || selectedCount === 0}
              className="hh-btn hh-btn-primary text-sm"
            >
              Создать отклики ({selectedCount})
            </LoadingButton>
            <LoadingButton
              onClick={onSendSelected}
              loading={isSending}
              disabled={isSending || isGeneratingAndSending || toSentCount === 0}
              className="hh-btn hh-btn-success text-sm"
            >
              Отправить ({toSentCount})
            </LoadingButton>
            <LoadingButton
              onClick={onGenerateAndSend}
              loading={isGeneratingAndSending}
              disabled={isGeneratingAndSending || isGeneratingState || isSending || selectedNotSended === 0}
              className="hh-btn hh-btn-warning text-sm"
            >
              {isGeneratingAndSending 
                ? (loading === 'generate-and-send' ? 'Создание...' : 'Отправка...') 
                : `Создать и отправить (${selectedNotSended})`
              }
            </LoadingButton>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#f4f4f5] text-sm">
              <tr>
                <th className="p-3 text-left w-10">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    className="hh-checkbox"
                  />
                </th>
                <th className="p-3 text-left min-w-[250px]">Вакансия</th>
                <th className="p-3 text-left min-w-[300px]">Описание</th>
                <th className="p-3 text-left min-w-[350px]">AI отклик</th>
              </tr>
            </thead>
            <tbody>
              {filteredVacancies.map(vacancy => (
                <tr key={vacancy.id} className="border-b border-[#e7e7e7] hover:bg-gray-50">
                  <td className="p-3 align-top">
                    <input
                      type="checkbox"
                      checked={vacancy.selected !== false}
                      onChange={e => onVacancyUpdate(vacancy.id, { selected: e.target.checked })}
                      className="hh-checkbox"
                    />
                  </td>
                  <td className="p-3 align-top text-left min-w-[250px]">
                    <div className="space-y-1">
                      <a
                        href={`https://hh.ru/vacancy/${vacancy.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hh-link font-medium block"
                      >
                        {vacancy.name}
                      </a>
                      <div className="text-sm font-medium text-[#232529]">{vacancy.employer?.name}</div>
                      {vacancy.salary && (
                        <div className="text-sm text-[#4bb34b] font-medium">
                          {formatSalary(vacancy.salary)}
                        </div>
                      )}
                      <div className="text-sm text-[#999999]">{vacancy.area?.name}</div>
                      {(vacancy.employment?.name || vacancy.schedule?.name) && (
                        <div className="text-sm text-[#999999]">
                          {[vacancy.employment?.name, vacancy.schedule?.name].filter(Boolean).join(' • ')}
                        </div>
                      )}
                      {vacancy.published_at && (
                        <div className="text-xs text-[#999999]">{formatDate(vacancy.published_at)}</div>
                      )}
                    </div>
                  </td>
                  <td className="p-3 align-top text-left min-w-[300px]">
                    <p 
                      className="text-sm text-[#666666] line-clamp-10 cursor-pointer hover:text-[#4bb34b]"
                      onClick={e => openModal(vacancy, e)}
                    >
                      {vacancy.description || vacancy.snippet?.requirement || vacancy.snippet?.responsibility || ''}
                    </p>
                  </td>
                  <td className="p-3 align-top text-left min-w-[300px]">
                    {generatingId === vacancy.id ? (
                      <div className="flex justify-center items-center h-[240px] bg-[#f4f4f5] rounded">
                        <span className="area-loader" />
                      </div>
                    ) : (
                      <textarea
                        value={vacancy.aiLetter || ''}
                        onChange={e => onVacancyUpdate(vacancy.id, { aiLetter: e.target.value })}
                        placeholder="AI отклик появится здесь..."
                        className="hh-input text-sm resize-none"
                        rows={10}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredVacancies.length === 0 && (
          <div className="p-12 text-center text-[#999999]">
            {isGenerating ? 'Нет выбранных вакансий' : 'Используйте фильтры выше для поиска вакансий'}
          </div>
        )}
      </div>

      {filteredVacancies.length > 0 && (
        <div className="text-center mt-6">
          <a 
            href="#filters" 
            className="inline-flex items-center gap-1 text-[#4bb34b] hover:text-[#369e36] text-sm"
          >
            ↑ Наверх к фильтрам
          </a>
        </div>
      )}

      {modalVacancy && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={closeModal}
        >
          <div 
            className="bg-white rounded-lg max-w-4xl max-h-[80vh] overflow-auto p-6"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-xl font-semibold text-[#232529] mb-2">{modalVacancy.name}</h2>
                <p className="text-lg text-[#666666]">{modalVacancy.employer?.name}</p>
              </div>
              <button 
                onClick={closeModal}
                className="text-2xl text-[#999999] hover:text-[#232529] leading-none"
              >
                ×
              </button>
            </div>
            <div className="prose max-w-none">
              <div dangerouslySetInnerHTML={{ __html: modalVacancy.description || '' }} />
            </div>
          </div>
        </div>
      )}
    </>
  )
}