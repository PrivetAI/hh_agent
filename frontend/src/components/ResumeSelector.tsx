import { useState, useEffect } from 'react'
import { Resume } from '../types'
import ApiService from '../services/apiService'

interface ResumeSelectorProps {
  selectedResumeId: string | null
  onResumeSelect: (resumeId: string) => void
}

export default function ResumeSelector({ selectedResumeId, onResumeSelect }: ResumeSelectorProps) {
  const [resumes, setResumes] = useState<Resume[]>([])
  const [loading, setLoading] = useState(true)
  const apiService = ApiService.getInstance()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      // Загружаем резюме и информацию о пользователе параллельно
      const [resumesData] = await Promise.all([
        apiService.getResumes(),
      ])
      
      setResumes(resumesData)
      
      // Auto-select first resume if none selected
      if (resumesData.length > 0 && !selectedResumeId) {
        onResumeSelect(resumesData[0].id)
      }
    } catch (err) {
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatExperience = (months?: number) => {
    if (!months) return 'Без опыта'
    const years = Math.floor(months / 12)
    const remainingMonths = months % 12
    if (years === 0) return `${remainingMonths} мес`
    if (remainingMonths === 0) return `${years} лет`
    return `${years} лет ${remainingMonths} мес`
  }

  if (loading) {
    return (
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-[#999999]">Выберите резюме</h3>
          <div className="h-5 bg-gray-200 rounded w-32 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="hh-card p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (resumes.length === 0) {
    return (
      <div className="hh-card p-4 mb-4 text-center text-[#999999]">
        У вас нет резюме на hh.ru. Создайте резюме для использования сервиса.
      </div>
    )
  }

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-[#999999]">Выберите резюме для откликов</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {resumes.map(resume => (
          <div
            key={resume.id}
            onClick={() => onResumeSelect(resume.id)}
            className={`hh-card p-4 cursor-pointer transition-all ${
              selectedResumeId === resume.id 
                ? 'ring-2 ring-[#d6001c] bg-red-50' 
                : 'hover:shadow-md'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <h4 className="font-medium text-[#232529] flex-1">
                {resume.title || 'Без названия'}
              </h4>
              {selectedResumeId === resume.id && (
                <svg className="w-5 h-5 text-[#d6001c] flex-shrink-0 ml-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            
            <div className="text-sm text-[#666666] space-y-1">
              <div>{resume.first_name} {resume.last_name}</div>
              {resume.total_experience && (
                <div className="text-xs">
                  Опыт: {formatExperience(resume.total_experience.months)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}