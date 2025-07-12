// pages/payment/[status].tsx
import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { useCredits } from '../../hooks/useCredits'

export default function PaymentResult() {
  const router = useRouter()
  const { status } = router.query
  const { refreshCredits } = useCredits()
  const [checking, setChecking] = useState(true)
  
  useEffect(() => {
    if (!status) return
    
    const checkPayment = async () => {
      if (status === 'success') {
        // Даем время серверу обработать result URL
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        // Обновляем баланс
        await refreshCredits()
        
        // Показываем сообщение
        setTimeout(() => {
          router.push('/?payment=success')
        }, 1000)
      } else {
        router.push('/?payment=fail')
      }
      setChecking(false)
    }
    
    checkPayment()
  }, [status, refreshCredits, router])
  
  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mb-4"></div>
          <p>Проверяем статус платежа...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        {status === 'success' ? (
          <>
            <div className="text-green-500 text-6xl mb-4">✓</div>
            <h1 className="text-2xl font-bold mb-2">Оплата прошла успешно!</h1>
            <p>Токены начислены на ваш баланс</p>
          </>
        ) : (
          <>
            <div className="text-red-500 text-6xl mb-4">✗</div>
            <h1 className="text-2xl font-bold mb-2">Оплата не завершена</h1>
            <p>Попробуйте еще раз</p>
          </>
        )}
      </div>
    </div>
  )
}