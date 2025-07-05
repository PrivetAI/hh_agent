// frontend/src/pages/index.tsx
import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useVacancies } from '../hooks/useVacancies'
import VacancyFilters from '../components/VacancyFilters'
import VacanciesTable from '../components/VacanciesTable'
import ResumeSelector from '../components/ResumeSelector'
import LandingPage from '../components/LandingPage'
import SEOHead from '../components/Head'
import Footer from '../components/Footer'
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

  if (isLoading) {
    return (
      <>
        <SEOHead 
          title="Загрузка - HH Agent"
          noindex={true}
        />
        <div className="min-h-screen bg-[#f4f4f5] flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-3 border-[#d6001c] border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="mt-4 text-[#999999]">Загрузка...</p>
          </div>
        </div>
      </>
    )
  }

  if (!isAuthenticated) {
    return <LandingPage />
  }

  return <AuthenticatedHome />
}

function AuthenticatedHome() {
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null)
  const { refreshCredits, refreshTrigger, hasCredits, credits, applications24h } = useCredits()

  const {
    vacancies,
    loading,
    generatingId,
    generateAllLetters,
    sendApplications,
    searchVacancies,
    generateAndSendSelected,
    updateVacancy
  } = useVacancies(selectedResumeId, refreshCredits)

  const { logout } = useAuth()

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
            onSearch={searchVacancies}
            loading={loading === 'search'}
          />

          {loading === 'search' ? (
            <TableSkeleton rows={10} />
          ) : (
            <VacanciesTable
              vacancies={vacancies}
              onVacancyUpdate={updateVacancy}
              onGenerateAll={generateAllLetters}
              onSendSelected={sendApplications}
              onGenerateAndSend={generateAndSendSelected}
              loading={loading}
              generatingId={generatingId}
            />
          )}
        </main>

        <Footer />
      </div>
    </>
  )
}