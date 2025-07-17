import axios, { AxiosInstance } from 'axios'
import { AuthManager } from '../utils/auth'
import { 
  AIMetadata, 
  GenerateLetterResponse, 
  SavedSearchesResponse, 
  SavedSearchItem, 
  UserInfo,
  VacancySearchResponse,
  VacancyAnalysisResponse,
  Dictionaries,
  Area,
  Resume,
  PaymentPackage
} from '../types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL
console.log('BASE_URL:', BASE_URL)

class ApiService {
  private static instance: ApiService
  private axios: AxiosInstance
  private pendingRequests: Map<string, Promise<any>> = new Map()

  private constructor() {
    this.axios = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.axios.interceptors.request.use(
      config => {
        const token = AuthManager.getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        if (process.env.NODE_ENV === 'development') {
          console.log(`API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`)
        }

        return config
      },
      error => {
        console.error('Request interceptor error:', error)
        return Promise.reject(error)
      }
    )

    this.axios.interceptors.response.use(
      response => {
        if (process.env.NODE_ENV === 'development') {
          console.log(`API Response: ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`)
        }
        return response
      },
      async error => {
        if (process.env.NODE_ENV === 'development') {
          console.error('API Error:', error.response?.status, error.response?.data)
        }

        if (error.response?.status === 401) {
          AuthManager.logout()
          window.location.href = '/'
        }
        return Promise.reject(error)
      }
    )
  }

  static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService()
    }
    return ApiService.instance
  }

  private async deduplicatedRequest<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
    const pending = this.pendingRequests.get(key)
    if (pending) {
      return pending
    }

    const promise = requestFn()
      .then(result => {
        this.pendingRequests.delete(key)
        return result
      })
      .catch(error => {
        this.pendingRequests.delete(key)
        throw error
      })

    this.pendingRequests.set(key, promise)
    return promise
  }

  // Auth
  async getAuthUrl(): Promise<{ url: string }> {
    const response = await this.axios.get('/api/auth/hh')
    return response.data
  }

  async authenticate(code: string): Promise<{ access_token: string }> {
    return this.deduplicatedRequest(
      `auth:${code}`,
      async () => {
        const response = await axios.post(`${BASE_URL}/api/auth/callback`, null, {
          params: { code },
          timeout: 30000,
        })
        return response.data
      }
    )
  }

  // Resume
  async getResumes(): Promise<Resume[]> {
    return this.deduplicatedRequest(
      'resumes',
      async () => {
        const response = await this.axios.get('/api/resumes')
        return response.data
      }
    )
  }

  // Dictionaries
  async getDictionaries(): Promise<Dictionaries> {
    return this.deduplicatedRequest(
      'dictionaries',
      async () => {
        const response = await this.axios.get('/api/dictionaries')
        return response.data
      }
    )
  }

  async getAreas(): Promise<Area[]> {
    return this.deduplicatedRequest(
      'areas',
      async () => {
        const response = await this.axios.get('/api/areas')
        return response.data
      }
    )
  }

  // Vacancies
  async searchVacancies(params: any): Promise<VacancySearchResponse> {
    const response = await this.axios.get('/api/vacancies', { params })
    return response.data
  }

  async searchVacanciesByResume(resumeId: string): Promise<VacancySearchResponse> {
    const response = await this.axios.get(`/api/vacancies/by-resume/${resumeId}`)
    return response.data
  }

  async analyzeVacancy(id: string, resume_id?: string): Promise<VacancyAnalysisResponse> {
    const response = await this.axios.post(`/api/vacancy/${id}/analyze`, null, {
      params: resume_id ? { resume_id } : {}
    })
    return response.data
  }

  async generateLetter(id: string, resume_id?: string): Promise<GenerateLetterResponse> {
    const response = await this.axios.post(`/api/vacancy/${id}/generate-letter`, null, {
      params: resume_id ? { resume_id } : {}
    })
    return response.data
  }

  async applyToVacancy(
    id: string,
    resume_id: string,
    message: string,
    aiMetadata?: AIMetadata
  ): Promise<{ success: boolean }> {
    const payload: any = {
      resume_id,
      message
    }

    if (aiMetadata) {
      payload.prompt_filename = aiMetadata.prompt_filename
      payload.ai_model = aiMetadata.ai_model
    }

    const response = await this.axios.post(`/api/vacancy/${id}/apply`, payload)
    return response.data
  }

  // User Info
  async getUserInfo(): Promise<UserInfo> {
    return this.deduplicatedRequest(
      'user-info',
      async () => {
        const response = await this.axios.get('/api/user-info')
        return response.data
      }
    )
  }

  // Saved Searches
  async getSavedSearches(): Promise<SavedSearchesResponse> {
    return this.deduplicatedRequest(
      'saved-searches',
      async () => {
        const response = await this.axios.get('/api/saved-searches')
        return response.data
      }
    )
  }

  async getVacanciesBySavedSearch(
    savedSearchId: string, 
    page: number = 0, 
    per_page: number = 100
  ): Promise<VacancySearchResponse> {
    const response = await this.axios.get(`/api/saved-searches/${savedSearchId}/vacancies`, {
      params: { page, per_page }
    })
    return response.data
  }

  // Payment
  async getPaymentPackages(): Promise<PaymentPackage[]> {
    const response = await this.axios.get('/api/payment/packages')
    return response.data
  }

  async createPayment(packageId: string): Promise<{ payment_url: string }> {
    const response = await this.axios.post('/api/payment/create', { package: packageId })
    return response.data
  }

  // History
  async getHistory(): Promise<any> {
    const response = await this.axios.get('/api/history')
    return response.data
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await this.axios.get('/health')
      return response.data
    } catch (error) {
      console.error('Health check failed:', error)
      throw error
    }
  }
}

export default ApiService