import axios, { AxiosInstance } from 'axios'
import { AuthManager } from '../utils/auth'

// Получаем BASE_URL из переменных окружения
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Интерфейс для AI метаданных
interface AIMetadata {
  prompt_filename: string
  ai_model: string
}

// Интерфейс ответа от генерации письма
interface GenerateLetterResponse {
  content: string
  prompt_filename: string
  ai_model: string
}

// Интерфейс для информации о пользователе
interface UserInfo {
  user_id: string
  hh_user_id: string
  email: string | null
  first_name: string | null
  last_name: string | null
  credits: number
  applications_24h: number
  created_at: string | null
}

class ApiService {
  private static instance: ApiService
  private axios: AxiosInstance
  private pendingRequests: Map<string, Promise<any>> = new Map()

  private constructor() {
    this.axios = axios.create({
      baseURL: BASE_URL,
      timeout: 30000, // 30 секунд таймаут
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.axios.interceptors.request.use(
      config => {
        const token = AuthManager.getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        // Логируем запросы в dev режиме
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

    // Response interceptor for 401
    this.axios.interceptors.response.use(
      response => {
        // Логируем ответы в dev режиме
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

  // Helper to deduplicate requests
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
  async getAuthUrl() {
    const response = await this.axios.get('/api/auth/hh')
    return response.data
  }

  async authenticate(code: string) {
    return this.deduplicatedRequest(
      `auth:${code}`,
      async () => {
        // Используем прямой axios для auth, так как это может быть до инициализации токена
        const response = await axios.post(`${BASE_URL}/api/auth/callback`, null, { 
          params: { code },
          timeout: 30000,
        })
        return response.data
      }
    )
  }

  // Resume
  async getResumes() {
    return this.deduplicatedRequest(
      'resumes',
      async () => {
        const response = await this.axios.get('/api/resumes')
        return response.data
      }
    )
  }
    
  // Dictionaries
  async getDictionaries() {
    return this.deduplicatedRequest(
      'dictionaries',
      async () => {
        const response = await this.axios.get('/api/dictionaries')
        return response.data
      }
    )
  }

  async getAreas() {
    return this.deduplicatedRequest(
      'areas',
      async () => {
        const response = await this.axios.get('/api/areas')
        return response.data
      }
    )
  }

  // Vacancies - these should not be deduplicated as params can change
  async searchVacancies(params: any) {
    const response = await this.axios.get('/api/vacancies', { params })
    return response.data
  }
  
  async analyzeVacancy(id: string, resume_id?: string) {
    const response = await this.axios.post(`/api/vacancy/${id}/analyze`, null, {
      params: resume_id ? { resume_id } : {}
    })
    return response.data
  }

  // Обновленный метод генерации письма с типизированным ответом
  async generateLetter(id: string, resume_id?: string): Promise<GenerateLetterResponse> {
    const response = await this.axios.post(`/api/vacancy/${id}/generate-letter`, null, {
      params: resume_id ? { resume_id } : {}
    })
    return response.data
  }

  // Обновленный метод отправки заявки с поддержкой AI метаданных
  async applyToVacancy(
    id: string, 
    resume_id: string, 
    message: string, 
    aiMetadata?: AIMetadata
  ) {
    const payload: any = { 
      resume_id, 
      message 
    }

    // Добавляем AI метаданные если они есть
    if (aiMetadata) {
      payload.prompt_filename = aiMetadata.prompt_filename
      payload.ai_model = aiMetadata.ai_model
    }

    const response = await this.axios.post(`/api/vacancy/${id}/apply`, payload)
    return response.data
  }

  // User Info (заменяет checkCredits)
  async getUserInfo(): Promise<UserInfo> {
    return this.deduplicatedRequest(
      'user-info',
      async () => {
        const response = await this.axios.get('/api/user-info')
        return response.data
      }
    )
  }

  // Payment
  async getPaymentPackages() {
    const response = await this.axios.get('/api/payment/packages')
    return response.data
  }

  async createPayment(packageId: string) {
    const response = await this.axios.post('/api/payment/create', { package: packageId })
    return response.data
  }

  // History
  async getHistory() {
    const response = await this.axios.get('/api/history')
    return response.data
  }

  // Метод для проверки здоровья API
  async healthCheck() {
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
export type { AIMetadata, GenerateLetterResponse, UserInfo }