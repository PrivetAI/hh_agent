import { useState, useCallback } from 'react'
import ApiService from '../services/apiService'
import { Vacancy } from '../types'

interface AIMetadata {
  prompt_filename: string
  ai_model: string
}

interface VacancyWithAI extends Vacancy {
  aiLetter?: string
  aiMetadata?: AIMetadata
}

interface PaginationMeta {
  page: number
  pages: number
  per_page: number
  found: number
}

export const useVacancies = (selectedResumeId?: string, onCreditsChange?: () => void) => {
  const [vacancies, setVacancies] = useState<VacancyWithAI[]>([])
  const [loading, setLoading] = useState('')
  const [generatingIds, setGeneratingIds] = useState<string[]>([])
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
      if (params.saved_search_id) {
        params.per_page = 100
      }

      const perPage = params.per_page ? parseInt(params.per_page) : 20

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
    setGeneratingIds(prev => [...prev, id])
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
      setGeneratingIds(prev => prev.filter(gId => gId !== id))
    }
  }, [apiService, updateVacancy, selectedResumeId])

  const generateAllLetters = useCallback(async () => {
    if (loading === 'generate') return

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
    setGeneratingIds(toGenerate.map(v => v.id))
    
    let hasGeneratedAny = false

    try {
      const promises = toGenerate.map(vacancy =>
        apiService.generateLetter(vacancy.id, selectedResumeId)
          .then(data => {
            updateVacancy(vacancy.id, {
              aiLetter: data.content,
              aiMetadata: {
                prompt_filename: data.prompt_filename,
                ai_model: data.ai_model
              }
            })
            
            setGeneratingIds(prev => prev.filter(id => id !== vacancy.id))
            hasGeneratedAny = true
            
            return { success: true, id: vacancy.id }
          })
          .catch(err => {
            console.error(`Generation error for ${vacancy.id}:`, err)
            setGeneratingIds(prev => prev.filter(id => id !== vacancy.id))
            return { success: false, id: vacancy.id, error: err }
          })
      )

      const results = await Promise.allSettled(promises)

      const succeeded = results.filter(r => r.status === 'fulfilled' && r.value.success).length
      const failed = results.filter(r => r.status === 'fulfilled' && !r.value.success).length

      if (failed > 0) {
        console.log(`Генерация завершена: ${succeeded} успешно, ${failed} с ошибками`)
      }
    } finally {
      setLoading('')
      setGeneratingIds([])

      if (hasGeneratedAny && onCreditsChange) {
        onCreditsChange()
      }
    }
  }, [vacancies, loading, apiService, selectedResumeId, onCreditsChange, updateVacancy])

  const sendApplications = useCallback(async () => {
    const selected = vacancies.filter(v => v.selected && v.aiLetter)
    if (selected.length === 0) {
      alert('Нет вакансий для отправки')
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
    generatingIds,
    searchVacancies,
    updateVacancy,
    generateLetter,
    generateAllLetters,
    sendApplications,
    paginationMeta
  }
}