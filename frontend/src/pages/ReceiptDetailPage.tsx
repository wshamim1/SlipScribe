import { useParams } from 'react-router-dom'

export default function ReceiptDetailPage() {
  const { id } = useParams()

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Receipt Details</h2>
        <p className="mt-1 text-sm text-gray-600">ID: {id}</p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
        <p className="text-gray-500">Receipt detail view coming soon...</p>
      </div>
    </div>
  )
}
