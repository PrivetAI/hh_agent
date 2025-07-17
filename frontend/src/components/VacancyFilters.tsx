import { useState } from 'react'
import ManualFilters from './ManualFilters'
import SavedSearches from './SavedSearches'

interface VacancyFiltersProps {
  onSearch: (params: any) => void
  loading: boolean
  selectedResumeId: string | null
}

export default function VacancyFilters({ onSearch, loading, selectedResumeId }: VacancyFiltersProps) {
  const [activeTab, setActiveTab] = useState<'manual' | 'saved'>('manual')

  return (
    <div className="hh-card p-4 mb-4" id="filters">
      <div className="flex mb-4 border-b">
        <button
          className={`pb-2 px-4 font-medium ${
            activeTab === 'manual'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
          onClick={() => setActiveTab('manual')}
        >
          Поиск
        </button>
        <button
          className={`pb-2 px-4 font-medium ${
            activeTab === 'saved'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
          onClick={() => setActiveTab('saved')}
        >
          Сохраненные поиски
        </button>
      </div>

      {activeTab === 'manual' && (
        <ManualFilters 
          onSearch={onSearch} 
          loading={loading} 
          selectedResumeId={selectedResumeId}
        />
      )}

      {activeTab === 'saved' && (
        <SavedSearches onSearch={onSearch} loading={loading} />
      )}
    </div>
  )
}