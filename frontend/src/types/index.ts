// AI metadata interface
export interface AIMetadata {
  prompt_filename: string
  ai_model: string
}

// Updated Vacancy interface with AI metadata support
export interface Vacancy {
  id: string
  name: string
  salary?: {
    from?: number
    to?: number
    currency?: string
  }
  employer: { name: string }
  snippet?: {
    requirement?: string
    responsibility?: string
  }
  area: { name: string }
  published_at?: string
  schedule?: { name: string }
  employment?: { name: string }
  description?: string
  descriptionLoading?: boolean
  aiScore?: number
  aiLetter?: string
  aiMetadata?: AIMetadata  // Added AI metadata support
  selected?: boolean
  applied?: boolean  // Added applied status
}

// Extended vacancy interface for useVacancies hook
export interface VacancyWithAI extends Vacancy {
  aiLetter?: string
  aiMetadata?: AIMetadata
}

export interface Resume {
  id: string
  first_name: string
  last_name: string
  title: string
  total_experience?: {
    months: number
  }
  full_text: string
  skill_set?: string[]
}

export interface Area {
  id: string
  name: string
  parent_id?: string
  areas?: Area[]
}

export interface DictionaryItem {
  id: string
  name: string
}

export interface Dictionaries {
  experience: DictionaryItem[]
  employment: DictionaryItem[]
  schedule: DictionaryItem[]
}

export interface SearchFilters {
  url: string
  text: string
  area: string
  salary: string
  only_with_salary: boolean
  experience: string
  employment: string
  schedule: string
  remote: boolean
  excluded_text: string
  per_page: string
}

export interface VacancyFiltersProps {
  onSearch: (params: any) => void
  loading: boolean
}

// Updated props to use VacancyWithAI for better type safety
export interface VacanciesTableProps {
  vacancies: VacancyWithAI[]
  onVacancyUpdate: (id: string, updates: Partial<VacancyWithAI>) => void
  onAnalyze: (id: string) => void
  onGenerate: (id: string) => void
  onSendSelected: () => void
  generatingId?: string  // Added to track which vacancy is being generated
  loading?: string       // Added to track loading states
}

export interface PaymentPackage {
  id: string
  credits: number
  amount: number
  currency: string
  popular?: boolean
}

// API response interfaces for better type safety
export interface GenerateLetterResponse {
  content: string
  prompt_filename: string
  ai_model: string
}

export interface CreditsResponse {
  has_credits: boolean
  credits: number
}

export interface VacancyAnalysisResponse {
  score: number
}

export interface VacancySearchResponse {
  items: Vacancy[]
  found: number
  pages: number
  page: number
  per_page: number
}