// frontend/src/pages/index.tsx
import { useState, useCallback } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useVacancies } from '../hooks/useVacancies'
import VacancyFilters from '../components/VacancyFilters'
import VacanciesTable from '../components/VacanciesTable'
import ResumeSelector from '../components/ResumeSelector'
import LandingPage from '../components/LandingPage'
import SEOHead from '../components/Head'
import Footer from '../components/Footer'
import Pagination from '../components/Pagination'
import { TableSkeleton } from '../components/ui/Skeleton'
import { CreditsInfo } from '../components/CreditsInfo'
import { useCredits } from '../hooks/useCredits'

export default function Home() {
  const {
    token,
    resume,
    isLoading,
    isAuthenticated,
    logout,
  } = useAuth()


  if (!isAuthenticated) {
    return <LandingPage />
  }

  return <AuthenticatedHome />
}

function AuthenticatedHome() {
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null)
  const [currentSearchParams, setCurrentSearchParams] = useState<any>({})
  const { refreshCredits, refreshTrigger, hasCredits, credits, applications24h } = useCredits()
  
  // Храним per_page отдельно для передачи в фильтры
  const [perPage, setPerPage] = useState<string>('20')

  const {
    vacancies,
    loading,
    generatingId,
    generateAllLetters,
    sendApplications,
    searchVacancies,
    generateAndSendSelected,
    updateVacancy,
    paginationMeta
  } = useVacancies(selectedResumeId, refreshCredits)

  const { logout } = useAuth()

  // Обработчик поиска с сохранением параметров
  const handleSearch = useCallback((params: any) => {
    // Сохраняем параметры поиска для пагинации
    setCurrentSearchParams(params)
    // Обновляем per_page если он изменился
    if (params.per_page) {
      setPerPage(params.per_page)
    }
    // Сбрасываем на первую страницу при новом поиске
    searchVacancies({ ...params, page: 0 })
  }, [searchVacancies])

  // Обработчик изменения страницы
  const handlePageChange = useCallback((page: number) => {
    // Для saved_search_url нужно особое обращение
    if (currentSearchParams.saved_search_url) {
      // Парсим URL и добавляем/обновляем параметр page
    try {
        const url = new URL(currentSearchParams.saved_search_url)
        url.searchParams.set('page', String(page - 1))
        searchVacancies({ 
          saved_search_url: url.toString(),
          page: page - 1 
        })
      } catch (error) {
        console.error('Error parsing saved search URL:', error)
        searchVacancies({ ...currentSearchParams, page: page - 1 })
      }
    } else {
      // Обычный поиск
      searchVacancies({ ...currentSearchParams, page: page - 1 })
    }
  }, [currentSearchParams, searchVacancies])

  return (
    <>
      <SEOHead 
        title="Панель управления - HH Agent"
        description="Управляйте своими откликами на вакансии с помощью AI. Создавайте персонализированные сопроводительные письма автоматически."
        noindex={true}
      />
      
      <div className="min-h-screen bg-[#f4f4f5] flex flex-col">
        <header className="bg-white border-b border-[#e7e7e7]">
          <div className="max-w-6xl mx-auto px-4 py-3 flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <span className="text-[#d6001c] font-bold text-xl">hh</span>
              <span className="text-[#232529] font-medium">агент</span>
            </div>
            <div className="flex items-center space-x-4">
              <a 
                href="/payment-terms" 
                className="text-sm text-[#666666] hover:text-[#d6001c] hidden sm:block"
              >
                Условия и цены
              </a>
              <button 
                onClick={logout} 
                className="text-sm text-[#999999] hover:text-[#d6001c]"
                aria-label="Выйти из аккаунта"
              >
                Выйти
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 max-w-6xl mx-auto px-4 py-6 pb-6 md:pb-6 w-full">
          <ResumeSelector
            selectedResumeId={selectedResumeId}
            onResumeSelect={setSelectedResumeId}
          />
          <CreditsInfo
            needTokens={!hasCredits}
            credits={credits}
            applications24h={applications24h}
            hasCredits={hasCredits}
            onCreditsChange={refreshCredits}
          />

          <VacancyFilters
            selectedResumeId={selectedResumeId}
            onSearch={handleSearch}
            loading={loading === 'search'}
          />

          {loading === 'search' ? (
            <TableSkeleton rows={10} />
          ) : (
            <>
              <VacanciesTable
                vacancies={vacancies}
                onVacancyUpdate={updateVacancy}
                onGenerateAll={generateAllLetters}
                onSendSelected={sendApplications}
                onGenerateAndSend={generateAndSendSelected}
                loading={loading}
                generatingId={generatingId}
              />
              
              {/* Добавляем компонент пагинации */}
              <Pagination
                currentPage={paginationMeta.page + 1} // API использует 0-based, UI 1-based
                totalPages={paginationMeta.pages}
                onPageChange={handlePageChange}
                loading={loading === 'search'}
              />
              
              {/* Информация о результатах */}
              {paginationMeta.found > 0 && (
                <div className="text-center mt-4 text-sm text-[#999999]">
                  Показано {vacancies.length} из {paginationMeta.found} вакансий
                </div>
              )}
            </>
          )}
        </main>

        <Footer />
      </div>
    </>
  )
}