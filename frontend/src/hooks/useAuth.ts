import { useState, useEffect, useCallback } from 'react'
import ApiService from '../services/apiService'
import { AuthManager } from '../utils/auth'
import { Resume } from '../types'
export const useAuth = () => {
  const [token, setToken] = useState<string>('')
  const [resume, setResume] = useState<Resume | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const apiService = ApiService.getInstance()

  const authenticate = useCallback(async (code: string) => {
    try {
      const authData = await apiService.authenticate(code)
      const { token: newToken } = authData
      
      AuthManager.setToken(newToken)
      setToken(newToken)
      setIsAuthenticated(true)
      AuthManager.clearAuthCodeFromUrl()
      
    } catch (err) {
      console.error('Auth error:', err)
      throw err
    }
  }, [])

  const logout = useCallback(() => {
    AuthManager.logout()
    setToken('')
    localStorage.clear()
    sessionStorage.clear()
    setResume(null)
    setIsAuthenticated(false)
    setTimeout(() => {
      window.location.reload()
    }, 1000);
  }, [])

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = AuthManager.getToken()
      const authCode = AuthManager.getAuthCodeFromUrl()

      if (savedToken) {
        setToken(savedToken)
        setIsAuthenticated(true)
      } else if (authCode) {
        try {
          await authenticate(authCode)
        } catch (err: any) {
          alert(err.response?.data?.detail || 'Ошибка авторизации')
        }
      }

      setIsLoading(false)
    }

    initAuth()
  }, [])

  return {
    token,
    resume,
    isLoading,
    isAuthenticated,
    authenticate,
    logout,
  }
}