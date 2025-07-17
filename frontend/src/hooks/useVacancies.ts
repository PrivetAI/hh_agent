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
  aiMetadata?: AIMetadata  // Новое поле для метаданных AI
}

export const useVacancies = (selectedResumeId?: string, onCreditsChange?: () => void) => {
  const [vacancies, setVacancies] = useState<VacancyWithAI[]>([])
  const [loading, setLoading] = useState('')
  const [generatingId, setGeneratingId] = useState<string>('')

  const apiService = ApiService.getInstance()

  // Updated searchVacancies method in useVacancies hook

  const searchVacancies = useCallback(async (params: any) => {
    setLoading('search')
    try {
      // Use unified search method - backend will handle resume-based search if resume_id is provided
      const data = await apiService.searchVacancies(params)
      const vacanciesWithSelection = (data.items || []).map((v: Vacancy) => ({
        ...v,
        selected: true,
        applied: false,
        aiLetter: undefined,
        aiMetadata: undefined
      }))
      setVacancies(vacanciesWithSelection)
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

  const analyzeVacancy = useCallback(async (id: string) => {
    try {
      const data = await apiService.analyzeVacancy(id, selectedResumeId)
      updateVacancy(id, { aiScore: data.score })
    } catch (err) {
      console.error('Analysis error:', err)
    }
  }, [apiService, updateVacancy, selectedResumeId])

  const generateLetter = useCallback(async (id: string) => {
    setGeneratingId(id)
    try {
      const data = await apiService.generateLetter(id, selectedResumeId)
      // Сохраняем и контент, и метаданные AI
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
        console.log('Calling onCreditsChange after generation')
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
        // Передаем AI метаданные при отправке
        await apiService.applyToVacancy(
          vacancy.id,
          selectedResumeId,
          vacancy.aiLetter,
          vacancy.aiMetadata  // Новый параметр с метаданными
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

  const generateAndSendSelected = useCallback(async () => {
    if (loading !== '') return

    const toGenerate = vacancies.filter(v => !v.aiLetter && v.selected)
    const toSendExisting = vacancies.filter(v => v.aiLetter && v.selected)

    if (toGenerate.length === 0 && toSendExisting.length === 0) {
      alert('Нет вакансий для обработки')
      return
    }

    setLoading('generate-and-send')
    let hasGeneratedAny = false
    let hasSentAny = false
    let totalSuccessfulSent = 0
    let totalFailedSent = 0
    const allErrors: string[] = []
    let updatedVacancies = [...vacancies]

    try {
      // Этап 1: Генерация откликов (если есть что генерировать)
      if (toGenerate.length > 0) {
        try {
          const creditsAmount = await (await apiService.getUserInfo()).credits
          if (creditsAmount < toGenerate.length) {
            const creditsSection = document.getElementById('credits-section')
            if (creditsSection) {
              creditsSection.scrollIntoView({ behavior: 'smooth' })
            }
            alert(`Недостаточно токенов для генерации. Нужно: ${toGenerate.length}, доступно: ${creditsAmount || 0}`)
            return
          }
        } catch (err) {
          console.error('Credits check error:', err)
          alert('Ошибка проверки токенов')
          return
        }

        const processedIds = new Set()

        for (const vacancy of toGenerate) {
          if (processedIds.has(vacancy.id)) continue
          processedIds.add(vacancy.id)

          setGeneratingId(vacancy.id)
          try {
            const data = await apiService.generateLetter(vacancy.id, selectedResumeId)
            // Обновляем локальный массив с метаданными
            updatedVacancies = updatedVacancies.map(v =>
              v.id === vacancy.id ? {
                ...v,
                aiLetter: data.content,
                aiMetadata: {
                  prompt_filename: data.prompt_filename,
                  ai_model: data.ai_model
                }
              } : v
            )
            setVacancies(updatedVacancies)
            hasGeneratedAny = true
          } catch (err) {
            console.error('Generation error:', err)
            allErrors.push(`Ошибка генерации для ${vacancy.name || vacancy.id}`)
          }
        }

        setGeneratingId('')
      }

      // Этап 2: Отправка всех готовых откликов
      const toSendFinal = updatedVacancies.filter(v => v.selected && v.aiLetter)

      if (toSendFinal.length > 0) {
        let successful = 0
        let failed = 0
        const sendErrors: string[] = []

        for (const vacancy of toSendFinal) {
          try {
            // Передаем метаданные при отправке
            await apiService.applyToVacancy(
              vacancy.id,
              selectedResumeId,
              vacancy.aiLetter,
              vacancy.aiMetadata
            )
            updatedVacancies = updatedVacancies.filter(v => v.id !== vacancy.id)
            successful++
            hasSentAny = true
          } catch (err: any) {
            console.error(`Failed to apply to ${vacancy.id}:`, err)
            const errorMsg = err.response?.data?.detail || err.message || 'Неизвестная ошибка'
            sendErrors.push(`${vacancy.name || vacancy.id}: ${errorMsg}`)
            failed++
          }
        }

        totalSuccessfulSent = successful
        totalFailedSent = failed
        allErrors.push(...sendErrors)
        setVacancies(updatedVacancies)
      }

      // Финальное сообщение
      let finalMessage = ''

      if (hasGeneratedAny) {
        finalMessage += `Создано откликов: ${toGenerate.length}\n`
      }

      if (totalSuccessfulSent > 0) {
        finalMessage += `Успешно отправлено: ${totalSuccessfulSent} откликов\n`
      }

      if (totalFailedSent > 0) {
        finalMessage += `Не удалось отправить: ${totalFailedSent}\n`
      }

      if (allErrors.length > 0 && allErrors.length <= 5) {
        finalMessage += '\nОшибки:\n' + allErrors.slice(0, 5).join('\n')
      }

      alert(finalMessage.trim() || 'Операция завершена')

    } catch (error) {
      console.error('Generate and send error:', error)
      alert('Произошла ошибка при выполнении операции')
    } finally {
      setLoading('')
      setGeneratingId('')

      // Обновляем кредиты если было сгенерировано что-то ИЛИ отправлено
      if ((hasGeneratedAny || hasSentAny) && onCreditsChange) {
        console.log('Calling onCreditsChange after generate-and-send')
        onCreditsChange()
      }
    }
  }, [vacancies, loading, apiService, selectedResumeId, onCreditsChange])

  return {
    vacancies,
    loading,
    generatingId,
    searchVacancies,
    updateVacancy,
    analyzeVacancy,
    generateLetter,
    generateAllLetters,
    sendApplications,
    generateAndSendSelected
  }
}