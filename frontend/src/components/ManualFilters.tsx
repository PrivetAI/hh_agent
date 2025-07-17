import { useState, useEffect, useMemo } from 'react'
import Select from 'react-select'
import ApiService from '../services/apiService'
import { AreasHelper } from '../utils/areas'
import { Area, Dictionaries, SearchFilters } from '../types'

interface ManualFiltersProps {
  onSearch: (params: any) => void
  loading: boolean
  selectedResumeId: string | null
}

export default function ManualFilters({ onSearch, loading, selectedResumeId }: ManualFiltersProps) {
  const [areas, setAreas] = useState<Area[]>([])
  const [dictionaries, setDictionaries] = useState<Dictionaries | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [searchMode, setSearchMode] = useState<'resume' | 'filters'>('resume')
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

  const apiService = ApiService.getInstance()

  useEffect(() => {
    Promise.all([
      apiService.getDictionaries(),
      apiService.getAreas()
    ]).then(([dictData, areasData]) => {
      setDictionaries(dictData)
      setAreas(AreasHelper.flattenRussianAreas(areasData))
    }).catch(console.error)
  }, [])

  const handleSearch = async () => {
    if (searchMode === 'resume') {
      if (!selectedResumeId) {
        alert('Выберите резюме')
        return
      }
      
      try {
        const response = await apiService.searchVacanciesByResume(selectedResumeId)
        onSearch(response)
      } catch (error) {
        console.error('Ошибка поиска по резюме:', error)
      }
    } else {
      const params = Object.entries(filters).reduce((acc, [key, value]) => {
        if (value) {
          if (key === 'remote' && value === true) {
            acc.work_format = 'REMOTE'
          } else if (key === 'excluded_text' && value) {
            acc.excluded_text = value
          } else if (key === 'per_page' && value) {
            acc.per_page = value
          } else if (key === 'experience' && value) {
            acc.experience = value
          } else if (key === 'employment' && value) {
            acc.employment = value
          } else if (key === 'schedule' && value) {
            acc.schedule = value
          } else if (key !== 'remote' && key !== 'excluded_text' && key !== 'per_page' && key !== 'experience' && key !== 'employment' && key !== 'schedule' && value) {
            acc[key] = value
          }
        }
        return acc
      }, {} as any)

      onSearch(params)
    }
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

  const isFiltersMode = searchMode === 'filters'

  return (
    <>
      <div className="mb-6">
        <div className="flex gap-6">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="radio"
              name="searchMode"
              value="resume"
              checked={searchMode === 'resume'}
              onChange={e => setSearchMode(e.target.value as 'resume')}
              className="text-blue-600"
            />
            <span className="text-sm text-[#232529]">Для моего резюме</span>
          </label>
          
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="radio"
              name="searchMode"
              value="filters"
              checked={searchMode === 'filters'}
              onChange={e => setSearchMode(e.target.value as 'filters')}
              className="text-blue-600"
            />
            <span className="text-sm text-[#232529]">Фильтры</span>
          </label>
        </div>
      </div>

      {isFiltersMode && (
        <>
          <div className="mb-4">
            <input
              type="text"
              value={filters.text}
              onChange={e => updateFilter('text', e.target.value)}
              placeholder="Ключевые слова"
              className="hh-input w-full"
            />
          </div>

          <div className="mb-4">
            <input
              type="text"
              value={filters.excluded_text}
              onChange={e => updateFilter('excluded_text', e.target.value)}
              placeholder="Исключить слова (через пробел)"
              className="hh-input w-full"
            />
          </div>

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
              loadingMessage={() => "Поиск..."}
              classNames={{
                control: () => 'hh-select-control',
                menu: () => 'hh-select-menu',
                option: () => 'hh-select-option'
              }}
            />

            <input
              type="number"
              value={filters.salary}
              onChange={e => updateFilter('salary', e.target.value)}
              placeholder="Зарплата от"
              className="hh-input"
            />

            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.only_with_salary}
                onChange={e => updateFilter('only_with_salary', e.target.checked)}
                className="hh-checkbox"
              />
              <span className="text-sm text-[#232529]">Только с зарплатой</span>
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <select
              value={filters.experience}
              onChange={e => updateFilter('experience', e.target.value)}
              className="hh-select"
            >
              <option value="">Любой опыт</option>
              {dictionaries?.experience?.map(exp => (
                <option key={exp.id} value={exp.id}>{exp.name}</option>
              ))}
            </select>

            <select
              value={filters.employment}
              onChange={e => updateFilter('employment', e.target.value)}
              className="hh-select"
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
                className="hh-checkbox"
              />
              <span className="text-sm text-[#232529]">Удаленная работа</span>
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <select
              value={filters.per_page}
              onChange={e => updateFilter('per_page', e.target.value)}
              className="hh-select w-full md:w-auto"
            >
              <option value="20">20 вакансий</option>
              <option value="50">50 вакансий</option>
              <option value="100">100 вакансий</option>
            </select>
          </div>
        </>
      )}

      <button
        onClick={handleSearch}
        disabled={loading || (searchMode === 'resume' && !selectedResumeId)}
        className="hh-btn hh-btn-primary w-full"
      >
        {loading ? <span className="hh-loader"></span> : 'Найти вакансии'}
      </button>
    </>
  )
}