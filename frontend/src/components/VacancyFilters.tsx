import { useState, useEffect, useMemo } from 'react'
import Select from 'react-select'
import ApiService from '../services/apiService'
import { AreasHelper } from '../utils/areas'
import { VacancyFiltersProps, Area, Dictionaries, SearchFilters } from '../types'

export default function VacancyFilters({ onSearch, loading }: VacancyFiltersProps) {
  const [areas, setAreas] = useState<Area[]>([])
  const [dictionaries, setDictionaries] = useState<Dictionaries | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [filters, setFilters] = useState<SearchFilters>({
    url: '',
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

  const handleSearch = () => {
    if (filters.url) {
      try {
        const url = new URL(filters.url)
        onSearch(Object.fromEntries(url.searchParams))
      } catch {
        alert('Неверный URL')
      }
    } else {
      const params = Object.entries(filters).reduce((acc, [key, value]) => {
        if (value && key !== 'url' && key !== 'excluded_text') {
          acc[key] = value
        }
        return acc
      }, {} as any)

      // Формируем текст поиска с исключениями через NOT
      let searchText = filters.text
      if (filters.excluded_text) {
        const excludedWords = filters.excluded_text
          .split(' ')
          .filter(word => word.trim())
          .map(word => `NOT "${word.trim()}"`)
          .join(' ')
        
        searchText = searchText 
          ? `${searchText} ${excludedWords}`
          : excludedWords
      }

      if (searchText) {
        params.text = searchText
      }

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

  return (
    <div className="hh-card p-4 mb-4" id="filters">
      <div className="mb-4">
        <input
          type="text"
          value={filters.url}
          onChange={e => updateFilter('url', e.target.value)}
          placeholder="Вставьте ссылку с hh.ru или используйте фильтры ниже"
          className="hh-input"
        />
      </div>
      <div className="mb-4 text-center text-gray-500">
        или
      </div>

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

      <button
        onClick={handleSearch}
        disabled={loading}
        className="hh-btn hh-btn-primary w-full"
      >
        {loading ? <span className="hh-loader"></span> : 'Найти вакансии'}
      </button>
    </div>
  )
}