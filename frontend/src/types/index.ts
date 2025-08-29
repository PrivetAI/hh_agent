// AI metadata interface
export interface AIMetadata {
  prompt_filename: string
  ai_model: string
}

// Vacancy interface with AI metadata support
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
  aiMetadata?: AIMetadata
  selected?: boolean
  applied?: boolean
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
  selectedResumeId: string
}

export interface VacanciesTableProps {
  vacancies: VacancyWithAI[]
  onVacancyUpdate: (id: string, updates: Partial<VacancyWithAI>) => void
  onAnalyze: (id: string) => void
  onGenerate: (id: string) => void
  onSendSelected: () => void
  generatingId?: string
  loading?: string
}

export interface PaymentPackage {
  id: string
  credits: number
  amount: number
  currency: string
  popular?: boolean
}

// API response interfaces
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

// User info interface
export interface UserInfo {
  user_id: string
  hh_user_id: string
  email: string | null
  first_name: string | null
  last_name: string | null
  credits: number
  applications_24h: number
  created_at: string | null
}

// Saved search interfaces
export interface SavedSearchItems {
  count: number
  url: string
}

export interface SavedSearchNewItems {
  count: number
  url: string
}

export interface SavedSearchItem {
  id: string
  created_at: string
  name: string
  items: SavedSearchItems
  new_items: SavedSearchNewItems
  email_subscription: boolean
  subscription: boolean
}

export interface SavedSearchesResponse {
  items: SavedSearchItem[]
  found: number
  pages: number
  page: number
  per_page: number
}
export interface CoverLetterStats {
  total_generated: number
  last_24h_generated: number
  timestamp: string
}