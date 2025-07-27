import Cookies from 'js-cookie'

export class AuthManager {
  private static readonly TOKEN_KEY = 'jwt_token'
  private static readonly REFRESH_KEY = 'refresh_token'

  static getToken(): string | undefined {
    return Cookies.get(AuthManager.TOKEN_KEY)
  }

  static setToken(token: string): void {
    Cookies.set(AuthManager.TOKEN_KEY, token, { expires: 1 }) // 1 day
  }

  static getRefreshToken(): string | undefined {
    return Cookies.get(AuthManager.REFRESH_KEY)
  }

  static setRefreshToken(token: string): void {
    Cookies.set(AuthManager.REFRESH_KEY, token, { expires: 30 }) // 30 days
  }

  static logout(): void {
    Cookies.remove(AuthManager.TOKEN_KEY)
    Cookies.remove(AuthManager.REFRESH_KEY)
  }

  static isAuthenticated(): boolean {
    return !!AuthManager.getToken()
  }

  static getAuthCodeFromUrl(): string | null {
    if (typeof window === 'undefined') return null
    
    return new URLSearchParams(window.location.search).get('code')
  }

  static clearAuthCodeFromUrl(): void {
    if (typeof window !== 'undefined') {
      window.history.replaceState({}, '', '/')
    }
  }
}