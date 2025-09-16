import { useState, useEffect, useMemo } from 'react'
import Select from 'react-select'
import ApiService from '../services/apiService' // Import the real API service
import SearchHint from './ui/SearchHint'

interface ManualFiltersProps {
  onSearch: (params: any) => void
  loading: boolean
}

interface SearchFilters {
  text: string
  area: string
  salary: string
  only_with_salary: boolean
  remote: boolean
  experience: string
  employment: string
  schedule: string
  per_page: string
  excluded_text: string
}

interface Area {
  id: string
  name: string
  parent_id?: string
}

interface DictionaryItem {
  id: string
  name: string
}

interface Dictionaries {
  experience: DictionaryItem[]
  employment: DictionaryItem[]
  schedule: DictionaryItem[]
}

// Areas helper
class AreasHelper {
  static flattenRussianAreas(areas: any[]): Area[] {
    const russia = areas.find((country: any) => country.id === '113')
    if (!russia || !russia.areas) return []
    return russia.areas
  }

  static formatAreaName(area: Area): string {
    return area.name
  }
}

export default function ManualFilters({ onSearch, loading }: ManualFiltersProps) {
  const [areas, setAreas] = useState<Area[]>([])
  const [dictionaries, setDictionaries] = useState<Dictionaries | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [filters, setFilters] = useState<SearchFilters>({
    text: '',
    area: '',
    salary: '',
    only_with_salary: false,
    remote: false,
    experience: '',
    employment: '',
    schedule: '',
    per_page: '20',
    excluded_text: ''
  })

  useEffect(() => {
    const apiService = ApiService.getInstance()
    
    const loadData = async () => {
      try {
        setIsLoading(true)
        const [dictData, areasData] = await Promise.all([
          apiService.getDictionaries(),
          apiService.getAreas()
        ])
        
        setDictionaries(dictData)
        setAreas(AreasHelper.flattenRussianAreas(areasData))
      } catch (error) {
        console.error('Error loading data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  const handleSearch = () => {
    // Prepare search parameters - clean up empty values
    const searchParams = Object.entries(filters).reduce((acc, [key, value]) => {
      // Skip empty strings and convert them to undefined
      if (value === '') {
        return acc
      }
      if (value === false){
        return acc
      }
      // Handle special cases
      if (key === 'salary' && value === '') {
        return acc
      }
      acc[key] = value
      return acc
    }, {} as any)

    onSearch(searchParams)
  }

  const filteredAreaOptions = useMemo(() => {
    if (!inputValue) return []
    
    const searchTerm = inputValue.toLowerCase()
    return areas
      .filter(area => area.name.toLowerCase().includes(searchTerm))
      .slice(0, 50)
      .map(area => ({
        value: area.id,
        label: AreasHelper.formatAreaName(area)
      }))
  }, [areas, inputValue])

  const selectedArea = areas.find(a => a.id === filters.area)
  const selectedOption = selectedArea ? {
    value: selectedArea.id,
    label: AreasHelper.formatAreaName(selectedArea)
  } : null

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  // Show loading state while data is being fetched
  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-2 text-gray-600">Загрузка данных...</span>
      </div>
    )
  }

  return (
    <>
      {/* Keywords */}
       <div className="mb-4">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={filters.text}
            onChange={e => updateFilter('text', e.target.value)}
            placeholder="Ключевые слова"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
          />
          <SearchHint />
        </div>
        <div className="md:hidden">
          <SearchHint />
        </div>
      </div>

      {/* Excluded Keywords */}
      <div className="mb-4">
        <input
          type="text"
          value={filters.excluded_text}
          onChange={e => updateFilter('excluded_text', e.target.value)}
          placeholder="Исключить слова"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* City, Salary, Only with Salary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <Select
          value={selectedOption}
          onChange={opt => updateFilter('area', opt?.value || '')}
          options={filteredAreaOptions}
          onInputChange={setInputValue}
          inputValue={inputValue}
          placeholder="Начните вводить город..."
          isClearable
          isSearchable
          noOptionsMessage={() => inputValue ? "Город не найден" : "Начните вводить название"}
          className="react-select-container"
          classNamePrefix="react-select"
        />

        <input
          type="number"
          value={filters.salary}
          onChange={e => updateFilter('salary', e.target.value)}
          placeholder="Зарплата от"
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
        />

        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.only_with_salary}
            onChange={e => updateFilter('only_with_salary', e.target.checked)}
            className="w-4 h-4 rounded border-2 border-gray-300 checked:bg-blue-600 checked:border-blue-600"
          />
          <span className="text-sm text-gray-700">Только с зарплатой</span>
        </label>
      </div>

      {/* Experience, Employment, Remote */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <select
          value={filters.experience}
          onChange={e => updateFilter('experience', e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 bg-white"
        >
          <option value="">Любой опыт</option>
          {dictionaries?.experience?.map(exp => (
            <option key={exp.id} value={exp.id}>{exp.name}</option>
          ))}
        </select>

        <select
          value={filters.employment}
          onChange={e => updateFilter('employment', e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 bg-white"
        >
          <option value="">Тип занятости</option>
          {dictionaries?.employment?.map(emp => (
            <option key={emp.id} value={emp.id}>{emp.name}</option>
          ))}
        </select>

        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.remote}
            onChange={e => updateFilter('remote', e.target.checked)}
            className="w-4 h-4 rounded border-2 border-gray-300 checked:bg-blue-600 checked:border-blue-600"
          />
          <span className="text-sm text-gray-700">Удаленная работа</span>
        </label>
      </div>

      {/* Results per page */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <select
          value={filters.per_page}
          onChange={e => updateFilter('per_page', e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 bg-white w-full md:w-auto"
        >
          <option value="20">20 вакансий</option>
          <option value="50">50 вакансий</option>
          <option value="100">100 вакансий</option>
        </select>
      </div>

      {/* Search Button */}
      <button
        onClick={handleSearch}
        disabled={loading}
        className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? (
          <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
        ) : (
          'Найти вакансии'
        )}
      </button>
    </>
  )
}