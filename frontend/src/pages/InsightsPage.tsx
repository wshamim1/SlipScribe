export default function InsightsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Spending Insights</h2>
        <p className="mt-1 text-sm text-gray-600">
          Anomalies and overspend alerts
        </p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
        <p className="text-gray-500">No insights yet. Upload some receipts to see spending patterns!</p>
      </div>
    </div>
  )
}
