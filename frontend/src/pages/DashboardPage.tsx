import { useQuery } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { getStats } from '../services/api'

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Spending Dashboard</h2>
          <p className="mt-1 text-sm text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Spending Dashboard</h2>
          <p className="mt-1 text-sm text-red-600">Failed to load stats.</p>
        </div>
      </div>
    )
  }

  const avgPerReceipt =
    stats.all_time.receipt_count > 0
      ? stats.all_time.total_spent / stats.all_time.receipt_count
      : 0

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Spending Dashboard</h2>
        <p className="mt-1 text-sm text-gray-600">
          Track your spending by month and merchant
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-600">Total Spent (This Month)</h3>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            ${Number(stats.this_month.total_spent).toFixed(2)}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {stats.this_month.receipt_count} receipt{stats.this_month.receipt_count !== 1 ? 's' : ''}
          </p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-600">Total Spent (All Time)</h3>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            ${Number(stats.all_time.total_spent).toFixed(2)}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {stats.all_time.receipt_count} receipt{stats.all_time.receipt_count !== 1 ? 's' : ''}
          </p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-sm font-medium text-gray-600">Avg per Receipt</h3>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            ${avgPerReceipt.toFixed(2)}
          </p>
          <p className="text-sm text-gray-500 mt-1">across all completed receipts</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Spending Chart */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Monthly Spending</h3>
          {stats.monthly.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={stats.monthly} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`, 'Spent']} />
                <Bar dataKey="total" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top Merchants */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Top Merchants</h3>
          {stats.top_merchants.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No data yet</p>
          ) : (
            <ul className="space-y-3">
              {stats.top_merchants.map((m: { name: string; total: number; count: number }) => (
                <li key={m.name} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{m.name}</p>
                    <p className="text-xs text-gray-500">{m.count} receipt{m.count !== 1 ? 's' : ''}</p>
                  </div>
                  <span className="text-sm font-semibold text-gray-900">
                    ${Number(m.total).toFixed(2)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
