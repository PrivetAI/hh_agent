import { useState, useCallback, useEffect } from 'react'
import ApiService from '../services/apiService'
import { UserInfo } from '../types'

export const useCredits = (isAuthenticated = true) => {
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
  const [loading, setLoading] = useState(true)

  const apiService = ApiService.getInstance()

  const fetchUserInfo = useCallback(async () => {
    // Не делаем запрос если пользователь не авторизован
    if (!isAuthenticated) {
      setLoading(false)
      return
    }

    try {
      const response = await apiService.getUserInfo()
      setUserInfo(response)
    } catch (err) {
      console.error('Failed to fetch user info:', err)
      // Сброс данных при ошибке (возможно, токен недействителен)
      setUserInfo(null)
    } finally {
      setLoading(false)
    }
  }, [apiService, isAuthenticated])

  const refreshCredits = useCallback(() => {
    if (!isAuthenticated) return
    
    setRefreshTrigger(prev => prev + 1)
    fetchUserInfo()
  }, [fetchUserInfo, isAuthenticated])

  // Fetch user info только для авторизованных пользователей
  useEffect(() => {
    if (isAuthenticated) {
      fetchUserInfo()
    } else {
      setLoading(false)
      setUserInfo(null)
    }
  }, [fetchUserInfo, isAuthenticated])

  // Сброс данных при выходе из системы
  useEffect(() => {
    if (!isAuthenticated) {
      setUserInfo(null)
      setLoading(false)
    }
  }, [isAuthenticated])

  return {
    refreshTrigger,
    refreshCredits,
    userInfo,
    hasCredits: (userInfo?.credits || 0) > 0,
    credits: userInfo?.credits || 0,
    applications24h: userInfo?.applications_24h || 0,
    creditsLoading: loading,
    // Дополнительные полезные данные
    userName: userInfo ? `${userInfo.first_name || ''} ${userInfo.last_name || ''}`.trim() || 'Пользователь' : '',
    userEmail: userInfo?.email || ''
  }
}

// Альтернативный вариант с переименованием хука для большей ясности
export const useUserInfo = useCredits