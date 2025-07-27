import { useState, useEffect } from 'react'
import ApiService from '../services/apiService'
import { SavedSearchItem, SavedSearchesResponse } from '../types'

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
      const response: SavedSearchesResponse = await apiService.getSavedSearches()
      setSavedSearches(response.items)
    } catch (error) {
      console.error('Ошибка загрузки сохраненных поисков:', error)
    } finally {
      setLoadingSearches(false)
    }
  }

  const handleSearch = (item: SavedSearchItem) => {
    // Извлекаем все параметры из URL
    try {
      const url = new URL(item.items.url)
      const params: any = {
        saved_search_id: item.id,
        page: 0
      }

      // Извлекаем все параметры из URL
      url.searchParams.forEach((value, key) => {
        // Пропускаем saved_search_id, так как уже добавили
        if (key !== 'saved_search_id') {
          params[key] = value
        }
      })

      console.log('Search params:', params)
      onSearch(params)
    } catch (error) {
      console.error('Ошибка парсинга URL:', error)
      // Fallback - используем только saved_search_id
      onSearch({
        saved_search_id: item.id,
        page: 0
      })
    }
  }

  const handleSearchNew = (item: SavedSearchItem) => {
    // Извлекаем все параметры из URL для новых вакансий
    try {
      const url = new URL(item.new_items.url)
      const params: any = {
        saved_search_id: item.id,
        page: 0
      }

      // Извлекаем все параметры из URL
      url.searchParams.forEach((value, key) => {
        // Пропускаем saved_search_id, так как уже добавили
        if (key !== 'saved_search_id') {
          params[key] = value
        }
      })

      console.log('New items search params:', params)
      onSearch(params)
    } catch (error) {
      console.error('Ошибка парсинга URL новых вакансий:', error)
      // Fallback
      handleSearch(item)
    }
  }

  if (loadingSearches) {
    return (
      <div className="flex justify-center py-12">
        <span className="inline-block w-5 h-5 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></span>
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
          className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-gray-900 truncate">{item.name}</h3>
          </div>

          <div className="space-y-2 mb-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Всего вакансий:</span>
              <span className="text-gray-900 font-medium">{item.items.count}</span>
            </div>

            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Новых вакансий:</span>
              <span className="text-gray-900 font-medium">{item.new_items.count}</span>
            </div>

            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Подписка:</span>
              <span className={`text-xs px-2 py-1 rounded ${item.subscription
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
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              onClick={() => handleSearch(item)}
              disabled={loading}
            >
              {loading ? 'Поиск...' : 'Найти вакансии'}
            </button>

            {item.new_items.count > 0 && (
              <button
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                onClick={() => handleSearchNew(item)}
                disabled={loading}
              >
                {loading ? 'Поиск...' : 'Найти новые'}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}