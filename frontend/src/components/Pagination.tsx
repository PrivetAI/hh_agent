import React from 'react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  loading?: boolean
}

export default function Pagination({ currentPage, totalPages, onPageChange, loading }: PaginationProps) {
  // Не показываем пагинацию если только 1 страница
  if (totalPages <= 1) return null

  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const showPages = 5 // Количество видимых номеров страниц
    
    if (totalPages <= showPages + 2) {
      // Показываем все страницы если их мало
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      // Всегда показываем первую страницу
      pages.push(1)
      
      let start = Math.max(2, currentPage - Math.floor(showPages / 2))
      let end = Math.min(totalPages - 1, start + showPages - 1)
      
      // Корректируем start если end упирается в конец
      if (end === totalPages - 1) {
        start = Math.max(2, end - showPages + 1)
      }
      
      // Добавляем многоточие в начале если нужно
      if (start > 2) {
        pages.push('...')
      }
      
      // Добавляем страницы в середине
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      
      // Добавляем многоточие в конце если нужно
      if (end < totalPages - 1) {
        pages.push('...')
      }
      
      // Всегда показываем последнюю страницу
      pages.push(totalPages)
    }
    
    return pages
  }

  const handlePageClick = (page: number) => {
    if (page !== currentPage && !loading) {
      onPageChange(page)
      // Скроллим к началу таблицы
      const table = document.querySelector('.hh-card')
      if (table) {
        table.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
  }

  return (
    <div className="flex justify-center items-center mt-6 gap-0.5">
      {/* Кнопка "Назад" */}
      <button
        onClick={() => handlePageClick(currentPage - 1)}
        disabled={currentPage === 1 || loading}
        className={`px-3 py-2 rounded-lg border ${
          currentPage === 1 || loading
            ? 'border-gray-200 text-gray-400 cursor-not-allowed'
            : 'border-[#e7e7e7] text-[#666666] hover:bg-gray-50 hover:border-[#0066ff]'
        }`}
        aria-label="Предыдущая страница"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      {/* Номера страниц */}
      {getPageNumbers().map((page, index) => {
        if (page === '...') {
          return (
            <span key={`ellipsis-${index}`} className="px-3 py-2 text-[#999999]">
              ...
            </span>
          )
        }
        
        const pageNum = page as number
        const isActive = pageNum === currentPage
        
        return (
          <button
            key={pageNum}
            onClick={() => handlePageClick(pageNum)}
            disabled={loading}
            className={`px-3 py-2 rounded-lg border transition-colors ${
              isActive
                ? 'bg-[#d6001c] text-white border-[#d6001c]'
                : loading
                ? 'border-gray-200 text-gray-400 cursor-not-allowed'
                : 'border-[#e7e7e7] text-[#666666] hover:bg-gray-50 hover:border-[#0066ff]'
            }`}
            aria-label={`Страница ${pageNum}`}
            aria-current={isActive ? 'page' : undefined}
          >
            {pageNum}
          </button>
        )
      })}

      {/* Кнопка "Вперед" */}
      <button
        onClick={() => handlePageClick(currentPage + 1)}
        disabled={currentPage === totalPages || loading}
        className={`px-3 py-2 rounded-lg border ${
          currentPage === totalPages || loading
            ? 'border-gray-200 text-gray-400 cursor-not-allowed'
            : 'border-[#e7e7e7] text-[#666666] hover:bg-gray-50 hover:border-[#0066ff]'
        }`}
        aria-label="Следующая страница"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  )
}