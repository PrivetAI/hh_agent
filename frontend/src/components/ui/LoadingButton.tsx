interface LoadingButtonProps {
  loading?: boolean
  disabled?: boolean
  onClick?: () => void
  className?: string
  //@ts-ignore
  children?: React.ReactNode
}

export const LoadingButton = ({ 
  loading, 
  disabled, 
  onClick, 
  className = "", 
  children 
}: LoadingButtonProps) => (
  <button
    onClick={onClick}
    disabled={disabled || loading}
    className={`${className} ${(disabled || loading) ? 'opacity-50 cursor-not-allowed' : ''}`}
  >
    {loading ? <span className="hh-loader" /> : children}
  </button>
)