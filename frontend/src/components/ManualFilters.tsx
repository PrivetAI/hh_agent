import { useState, useEffect, useMemo } from 'react'
import Select from 'react-select'

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

// Mock API Service for demonstration
const mockApiService = {
  getDictionaries: async (): Promise<Dictionaries> => ({
    experience: [
      { id: 'noExperience', name: 'Нет опыта' },
      { id: 'between1And3', name: 'От 1 года до 3 лет' },
      { id: 'between3And6', name: 'От 3 до 6 лет' },
      { id: 'moreThan6', name: 'Более 6 лет' }
    ],
    employment: [
      { id: 'full', name: 'Полная занятость' },
      { id: 'part', name: 'Частичная занятость' },
      { id: 'project', name: 'Проектная работа' }
    ],
    schedule: [
      { id: 'fullDay', name: 'Полный день' },
      { id: 'shift', name: 'Сменный график' },
      { id: 'flexible', name: 'Гибкий график' },
      { id: 'remote', name: 'Удаленная работа' }
    ]
  }),
  getAreas: async (): Promise<any[]> => [{
    id: '113',
    name: 'Россия',
    areas: [
      { id: '1', name: 'Москва' },
      { id: '2', name: 'Санкт-Петербург' },
      { id: '3', name: 'Новосибирск' }
    ]
  }]
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
    Promise.all([
      mockApiService.getDictionaries(),
      mockApiService.getAreas()
    ]).then(([dictData, areasData]) => {
      setDictionaries(dictData)
      setAreas(AreasHelper.flattenRussianAreas(areasData))
    }).catch(console.error)
  }, [])

  const handleSearch = () => {
    // Prepare search parameters - clean up empty values
    const searchParams = Object.entries(filters).reduce((acc, [key, value]) => {
      // Skip empty strings and convert them to undefined
      if (value === '') {
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

  return (
    <>
      {/* Keywords */}
      <div className="mb-4">
        <input
          type="text"
          value={filters.text}
          onChange={e => updateFilter('text', e.target.value)}
          placeholder="Ключевые слова"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Excluded Keywords */}
      <div className="mb-4">
        <input
          type="text"
          value={filters.excluded_text}
          onChange={e => updateFilter('excluded_text', e.target.value)}
          placeholder="Исключить слова (через пробел)"
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