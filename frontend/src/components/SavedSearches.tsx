import { useState, useEffect } from 'react'
import ApiService from '../services/apiService'
import { SavedSearchItem } from '../types'

interface SavedSearchesProps {
  onSearch: (params: any) => void
  loading: boolean
}

export default function SavedSearches({ onSearch, loading }: SavedSearchesProps) {
  const [savedSearches, setSavedSearches] = useState<SavedSearchItem[]>([])
  const [loadingSearches, setLoadingSearches] = useState(false)

  const apiService = ApiService.getInstance()

  useEffect(() => {
    loadSavedSearches()
  }, [])

  const loadSavedSearches = async () => {
    setLoadingSearches(true)
    try {
      const response = await apiService.getSavedSearches()
      setSavedSearches(response.items)
    } catch (error) {
      console.error('Ошибка загрузки сохраненных поисков:', error)
    } finally {
      setLoadingSearches(false)
    }
  }

  const handleSearch = async (item: SavedSearchItem) => {
    try {
      const response = await apiService.getVacanciesBySavedSearch(item.id)
      onSearch(response)
    } catch (error) {
      console.error('Ошибка поиска по сохраненному поиску:', error)
    }
  }

  if (loadingSearches) {
    return (
      <div className="flex justify-center py-12">
        <span className="area-loader"></span>
      </div>
    )
  }

  if (savedSearches.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        Нет сохраненных поисков
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {savedSearches.map(item => (
        <div
          key={item.id}
          className="hh-card p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-[#232529] truncate">{item.name}</h3>
          </div>
          
          <div className="space-y-2 mb-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Всего вакансий:</span>
              <span className="text-[#232529] font-medium">{item.items.count}</span>
            </div>
            
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Новых вакансий:</span>
              <span className="text-[#232529] font-medium">{item.new_items.count}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Подписка:</span>
              <span className={`text-xs px-2 py-1 rounded ${
                item.subscription
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {item.subscription ? 'Активна' : 'Неактивна'}
              </span>
            </div>
          </div>
          
          <div className="text-xs text-gray-400 mb-3">
            Создан: {new Date(item.created_at).toLocaleDateString('ru-RU', {
              day: '2-digit',
              month: '2-digit', 
              year: 'numeric',
            })}
          </div>
          
          <div className="flex gap-2">
            <button
              className="hh-btn hh-btn-primary flex-1"
              onClick={() => handleSearch(item)}
              disabled={loading}
            >
              {loading ? 'Поиск...' : 'Найти вакансии'}
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}