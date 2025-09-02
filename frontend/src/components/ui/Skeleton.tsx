export const Skeleton = ({ className = "" }: { className?: string }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
)

export const TableSkeleton = ({ rows = 5 }: { rows?: number }) => (
  <div className="hh-card overflow-hidden">
    <div className="p-4 border-b border-[#e7e7e7] flex justify-between items-center">
      <Skeleton className="h-6 w-32 sm:w-48" />
      <div className="hidden sm:flex gap-3">
        <Skeleton className="h-9 w-40" />
        <Skeleton className="h-9 w-36" />
      </div>
      <Skeleton className="h-9 w-20 sm:hidden" />
    </div>
    
    {/* Desktop таблица */}
    <div className="hidden md:block overflow-x-auto">
      <table className="w-full">
        <thead className="bg-[#f4f4f5] text-sm">
          <tr>
            <th className="p-3 w-10"><Skeleton className="h-4 w-4" /></th>
            <th className="p-3 text-left min-w-[250px]"><Skeleton className="h-4 w-20" /></th>
            <th className="p-3 text-left min-w-[350px]"><Skeleton className="h-4 w-20" /></th>
            <th className="p-3 text-left min-w-[300px]"><Skeleton className="h-4 w-20" /></th>
            <th className="p-3 text-left w-[100px]"><Skeleton className="h-4 w-16" /></th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <tr key={i} className="border-b border-[#e7e7e7]">
              <td className="p-3 align-top">
                <Skeleton className="h-4 w-4" />
              </td>
              <td className="p-3 align-top text-left min-w-[250px]">
                <div className="space-y-1">
                  <Skeleton className="h-5 w-64" />
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-4 w-32 bg-[#4bb34b]/20" />
                  <Skeleton className="h-4 w-36" />
                  <Skeleton className="h-3 w-40" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </td>
              <td className="p-3 align-top text-left min-w-[300px]">
                <div className="space-y-1">
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-5/6" />
                  <Skeleton className="h-3 w-4/5" />
                  <Skeleton className="h-3 w-3/4" />
                  <Skeleton className="h-3 w-4/6" />
                </div>
              </td>
              <td className="p-3 align-top text-left min-w-[300px]">
                <Skeleton className="h-24 w-full rounded" />
              </td>
              <td className="p-3 align-top text-left">
                <Skeleton className="h-7 w-16" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

    {/* Мобильные карточки */}
    <div className="md:hidden">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="p-4 border-b border-[#e7e7e7] last:border-b-0">
          <div className="flex items-start justify-between mb-2">
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-7 w-16" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-5 w-4/5" />
            <Skeleton className="h-4 w-3/5" />
            <Skeleton className="h-4 w-24 bg-[#4bb34b]/20" />
            <Skeleton className="h-3 w-2/3" />
            <div className="space-y-1 mt-3">
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-5/6" />
              <Skeleton className="h-3 w-3/4" />
            </div>
            <Skeleton className="h-20 w-full rounded mt-3" />
          </div>
        </div>
      ))}
    </div>
  </div>
)