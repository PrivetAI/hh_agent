import { useState, useEffect } from 'react'
import ApiService from '../services/apiService'
import { LoadingButton } from './ui/LoadingButton'
import { PaymentPackage } from '../types'
import { useCredits } from '../hooks/useCredits'


interface CreditsInfoProps {
    needTokens?: boolean
    credits: number
    applications24h: number
    hasCredits: boolean
    onCreditsChange?: () => void
}

export const CreditsInfo = ({
    needTokens,
    credits,
    applications24h,
    hasCredits,
    onCreditsChange
}: CreditsInfoProps) => {
    const [packages, setPackages] = useState<PaymentPackage[]>([])
    const [packagesLoading, setPackagesLoading] = useState(true)
    const [paymentLoading, setPaymentLoading] = useState(false)
    const [selectedPackageId, setSelectedPackageId] = useState<string | null>(null)
    const [showPackages, setShowPackages] = useState(false)

    const apiService = ApiService.getInstance()

    useEffect(() => {
        const fetchPackages = async () => {
            try {
                const packagesResponse = await apiService.getPaymentPackages()
                setPackages(packagesResponse)

                if (packagesResponse.length > 0) {
                    setSelectedPackageId(packagesResponse[0].id)
                }
            } catch (err) {
                console.error('Failed to fetch packages:', err)
            } finally {
                setPackagesLoading(false)
            }
        }

        fetchPackages()
    }, [apiService])

    const handlePurchase = async () => {
        if (!selectedPackageId) return

        setPaymentLoading(true)
        try {
            const payment = await apiService.createPayment(selectedPackageId)
            if (payment.payment_url) {
                // Сохраняем ID платежа
                localStorage.setItem('pending_payment_id', payment.payment_id)

                // Открываем в новом окне
                const paymentWindow = window.open(payment.payment_url, '_blank')

                // Начинаем проверку статуса
                startPaymentStatusCheck(payment.payment_id, paymentWindow)
            }
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Ошибка создания платежа')
        } finally {
            setPaymentLoading(false)
        }
    }

    const startPaymentStatusCheck = (paymentId: string, paymentWindow: Window | null) => {
        let checkCount = 0
        const maxChecks = 60 // Проверяем 5 минут (60 * 5 сек)

        const checkInterval = setInterval(async () => {
            checkCount++

            // Проверяем закрыто ли окно оплаты
            if (paymentWindow && paymentWindow.closed) {
                // Делаем финальную проверку через 2 секунды
                setTimeout(async () => {
                    if (onCreditsChange) {
                        await onCreditsChange()
                    }
                    clearInterval(checkInterval)
                    localStorage.removeItem('pending_payment_id')
                }, 2000)
                return
            }

            // Проверяем статус платежа на сервере
            try {
                const userInfo = await apiService.getUserInfo()
                const storedCredits = localStorage.getItem('last_credits_amount')

                if (!storedCredits || parseInt(storedCredits) < userInfo.credits) {
                    // Кредиты увеличились - платеж успешен
                    clearInterval(checkInterval)
                    localStorage.removeItem('pending_payment_id')
                    localStorage.setItem('last_credits_amount', userInfo.credits.toString())

                    if (onCreditsChange) {
                        await onCreditsChange()
                    }
                }
            } catch (error) {
                console.error('Error checking payment status:', error)
            }

            // Останавливаем после максимального количества проверок
            if (checkCount >= maxChecks) {
                clearInterval(checkInterval)
                localStorage.removeItem('pending_payment_id')
            }
        }, 5000) // Проверяем каждые 5 секунд
    }

    // При загрузке компонента проверяем незавершенные платежи
    useEffect(() => {
        const pendingPaymentId = localStorage.getItem('pending_payment_id')
        if (pendingPaymentId && onCreditsChange) {
            // Возобновляем проверку статуса
            startPaymentStatusCheck(pendingPaymentId, null)
        }
    }, [])

    const getTokenWord = (count: number) => {
        const lastDigit = count % 10
        const lastTwoDigits = count % 100

        if (lastTwoDigits >= 11 && lastTwoDigits <= 14) return 'токенов'
        if (lastDigit === 1) return 'токен'
        if (lastDigit >= 2 && lastDigit <= 4) return 'токена'
        return 'токенов'
    }
    const selectedPackage = packages.find(pkg => pkg.id === selectedPackageId)

    return (
        <div id="credits-section" className={`hh-card p-4 md:p-6 mb-4 ${(!hasCredits || needTokens) ? 'border-orange-300 bg-orange-50' : ''}`}>
            <div>
                <span className="text-xl md:text-xl font-bold text-[#232529]">Доступно: {credits} {getTokenWord(credits)}</span>
                <div className="text-sm md:text-base text-[#666666] md:ml-3 mt-2">1 токен = 1 отклик</div>
                <div className="text-sm md:text-base text-[#666666] md:ml-3 mb-4"> Откликов за сегодня <span className="font-bold text-[#232529]">{applications24h}/200</span> (лимит headhunter)</div>
            </div>

            {(!hasCredits || needTokens) && (
                <span className="text-sm text-orange-600 font-medium">
                    {needTokens ? 'Купите токены для генерации откликов' : 'Пополните баланс для генерации откликов'}
                </span>
            )}

            <div className="md:hidden">
                <div
                    onClick={() => setShowPackages(!showPackages)}
                    className="flex items-center justify-between py-3 border-t border-[#e7e7e7] cursor-pointer transition-colors hover:bg-gray-50 -mx-4 px-4"
                >
                    <span className="text-base font-medium text-[#232529]">Купить токены</span>
                    <svg
                        className={`w-5 h-5 text-[#999999] transition-transform ${showPackages ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>

                {showPackages && (
                    <div className="pt-4 pb-2 border-t border-[#e7e7e7] -mx-4 px-4">
                        <div className="space-y-3">
                            {packages.map(pkg => {
                                const pricePerToken = (pkg.amount / pkg.credits).toFixed(1)
                                const isSelected = selectedPackageId === pkg.id

                                return (
                                    <div
                                        key={pkg.id}
                                        onClick={() => setSelectedPackageId(pkg.id)}
                                        className={`border rounded-lg p-3 cursor-pointer transition-all ${isSelected
                                            ? 'ring-2 ring-[#d6001c] bg-red-50 border-[#d6001c]'
                                            : 'hover:shadow-md border-[#e7e7e7] active:bg-gray-50'
                                            }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <div className="font-bold text-base text-[#232529]">
                                                    {pkg.credits} токенов
                                                </div>
                                                <div className="text-sm text-[#999999] mt-0.5">
                                                    {pkg.amount.toLocaleString('ru-RU')} ₽
                                                </div>
                                                <div className="text-xs text-[#666666] font-medium mt-1">
                                                    {pricePerToken} ₽ за отклик
                                                </div>
                                            </div>
                                            {isSelected && (
                                                <svg className="w-5 h-5 text-[#d6001c] flex-shrink-0 ml-3" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                                </svg>
                                            )}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>

                        <LoadingButton
                            loading={paymentLoading}
                            onClick={handlePurchase}
                            disabled={!selectedPackageId}
                            className="hh-btn hh-btn-primary w-full py-3 text-base mt-4"
                        >
                            {selectedPackage
                                ? `Оплатить ${selectedPackage.amount.toLocaleString('ru-RU')} ₽`
                                : 'Выберите пакет'
                            }
                        </LoadingButton>

                        <div className="text-xs text-[#999999] text-center mt-3">
                            {'Оплата через СБП • '}<a href="/offerta">Публичная офферта</a>
                        </div>
                    </div>
                )}
            </div>

            <div className="hidden md:block">
                <div className="grid grid-cols-3 gap-4 mb-5">
                    {packages.map(pkg => {
                        const pricePerToken = (pkg.amount / pkg.credits).toFixed(1)
                        const isSelected = selectedPackageId === pkg.id

                        return (
                            <div
                                key={pkg.id}
                                onClick={() => setSelectedPackageId(pkg.id)}
                                className={`border rounded-lg p-4 cursor-pointer transition-all ${isSelected
                                    ? 'ring-2 ring-[#d6001c] bg-red-50 border-[#d6001c]'
                                    : 'hover:shadow-md border-[#e7e7e7]'
                                    }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="font-bold text-xl text-[#232529]">
                                            {pkg.credits} токенов
                                        </div>
                                        <div className="text-base text-[#999999] mt-1">
                                            {pkg.amount.toLocaleString('ru-RU')} ₽
                                        </div>
                                        <div className="text-sm text-[#666666] font-medium mt-2">
                                            {pricePerToken} ₽ за отклик
                                        </div>
                                    </div>
                                    {isSelected && (
                                        <svg className="w-6 h-6 text-[#d6001c] flex-shrink-0 ml-2" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                        </svg>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>

                <LoadingButton
                    loading={paymentLoading}
                    onClick={handlePurchase}
                    disabled={!selectedPackageId}
                    className="hh-btn hh-btn-primary mx-auto block px-10 py-3 text-base"
                >
                    {selectedPackage
                        ? `Купить за ${selectedPackage.amount.toLocaleString('ru-RU')} ₽`
                        : 'Выберите пакет'
                    }
                </LoadingButton>

                <div className="mt-4 text-sm text-[#999999] text-center">
                    {'Оплата через СБП • '}
                    <a href="/offerta">
                        Публичная офферта
                    </a>
                </div>
            </div>
        </div>
    )
}