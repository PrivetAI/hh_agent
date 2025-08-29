import { useState, useCallback } from 'react'
import ApiService from '../services/apiService'
import { Vacancy } from '../types'

// Расширенный интерфейс для AI метаданных
interface AIMetadata {
  prompt_filename: string
  ai_model: string
}

// Расширенный интерфейс вакансии
interface VacancyWithAI extends Vacancy {
  aiLetter?: string
  aiMetadata?: AIMetadata
}

// Интерфейс для метаданных пагинации
interface PaginationMeta {
  page: number
  pages: number
  per_page: number
  found: number
}

export const useVacancies = (selectedResumeId?: string, onCreditsChange?: () => void) => {
  const [vacancies, setVacancies] = useState<VacancyWithAI[]>([])
  const [loading, setLoading] = useState('')
  const [generatingId, setGeneratingId] = useState<string>('')
  const [paginationMeta, setPaginationMeta] = useState<PaginationMeta>({
    page: 0,
    pages: 0,
    per_page: 20,
    found: 0
  })

  const apiService = ApiService.getInstance()

  const searchVacancies = useCallback(async (params: any) => {
    setLoading('search')
    try {
      // Сохраняем per_page из параметров или используем значение по умолчанию
     // Если это поиск по сохраненному поиску, устанавливаем per_page в 100
      if (params.saved_search_id) {
        params.per_page = 100
      }
      
      const perPage = params.per_page ? parseInt(params.per_page) : 20
      
      // Убеждаемся что page передается как число
      if (params.page !== undefined) {
        params.page = parseInt(params.page)
      } else {
        params.page = 0
      }
      
    
      const data = await apiService.searchVacancies(params)
      
      const vacanciesWithSelection = (data.items || []).map((v: Vacancy) => ({
        ...v,
        selected: true,
        applied: v.applied || false,
        aiLetter: undefined,
        aiMetadata: undefined
      }))
      
      setVacancies(vacanciesWithSelection)
      
      // Обновляем метаданные пагинации
      setPaginationMeta({
        page: data.page || 0,
        pages: data.pages || 0,
        per_page: data.per_page || perPage,
        found: data.found || 0
      })
    } catch (err: any) {
      console.error('Search error:', err)
      alert(err.response?.data?.detail || 'Ошибка поиска')
    } finally {
      setLoading('')
    }
  }, [apiService])
  
  const updateVacancy = useCallback((id: string, updates: Partial<VacancyWithAI>) => {
    setVacancies(prev => prev.map(v => v.id === id ? { ...v, ...updates } : v))
  }, [])

  const generateLetter = useCallback(async (id: string) => {
    setGeneratingId(id)
    try {
      const data = await apiService.generateLetter(id, selectedResumeId)
      updateVacancy(id, {
        aiLetter: data.content,
        aiMetadata: {
          prompt_filename: data.prompt_filename,
          ai_model: data.ai_model
        }
      })
    } catch (err) {
      console.error('Generation error:', err)
    } finally {
      setGeneratingId('')
    }
  }, [apiService, updateVacancy, selectedResumeId])

  const generateAllLetters = useCallback(async () => {
    if (loading === 'generate' || loading === 'generate-and-send') return

    const toGenerate = vacancies.filter(v => !v.aiLetter && v.selected)

    if (toGenerate.length === 0) return

    try {
      const creditsAmount = await (await apiService.getUserInfo()).credits
      if (!creditsAmount || creditsAmount < toGenerate.length) {
        const creditsSection = document.getElementById('credits-section')
        if (creditsSection) {
          creditsSection.scrollIntoView({ behavior: 'smooth' })
        }
        alert(`Недостаточно токенов. Нужно: ${toGenerate.length}, доступно: ${creditsAmount || 0}`)
        return
      }
    } catch (err) {
      console.error('Credits check error:', err)
      alert('Ошибка проверки токенов')
      return
    }

    setLoading('generate')
    const processedIds = new Set()
    let hasGeneratedAny = false

    try {
      for (const vacancy of toGenerate) {
        if (processedIds.has(vacancy.id)) continue
        processedIds.add(vacancy.id)

        setGeneratingId(vacancy.id)
        try {
          const data = await apiService.generateLetter(vacancy.id, selectedResumeId)
          setVacancies(prev => prev.map(v =>
            v.id === vacancy.id ? {
              ...v,
              aiLetter: data.content,
              aiMetadata: {
                prompt_filename: data.prompt_filename,
                ai_model: data.ai_model
              }
            } : v
          ))
          hasGeneratedAny = true
        } catch (err) {
          console.error('Generation error:', err)
        }
      }
    } finally {
      setGeneratingId('')
      setLoading('')

      if (hasGeneratedAny && onCreditsChange) {
        onCreditsChange()
      }
    }
  }, [vacancies, loading, apiService, selectedResumeId, onCreditsChange])

  const sendApplications = useCallback(async () => {
    const selected = vacancies.filter(v => v.selected && v.aiLetter)
    if (selected.length === 0) {
      alert('Нет вакансий для отправки или все уже отправлены')
      return
    }

    setLoading('send')
    let successful = 0
    let failed = 0
    const errors: string[] = []

    for (const vacancy of selected) {
      try {
        await apiService.applyToVacancy(
          vacancy.id,
          selectedResumeId,
          vacancy.aiLetter,
          vacancy.aiMetadata
        )
        setVacancies(prev => prev.filter(v => v.id !== vacancy.id))
        successful++
      } catch (err: any) {
        console.error(`Failed to apply to ${vacancy.id}:`, err)
        const errorMsg = err.response?.data?.detail || err.message || 'Неизвестная ошибка'
        errors.push(`${vacancy.name || vacancy.id}: ${errorMsg}`)
        failed++
      }
    }

    let message = ''
    if (successful > 0) {
      message += `Успешно отправлено: ${successful} откликов`
    }
    if (failed > 0) {
      message += `${successful > 0 ? '\n' : ''}Не удалось отправить: ${failed}`
      if (errors.length <= 3) {
        message += '\n' + errors.join('\n')
      }
    }

    alert(message || 'Операция завершена')
    setLoading('')
  }, [vacancies, apiService, selectedResumeId])

  return {
    vacancies,
    loading,
    generatingId,
    searchVacancies,
    updateVacancy,
    generateLetter,
    generateAllLetters,
    sendApplications,
    paginationMeta
  }
}