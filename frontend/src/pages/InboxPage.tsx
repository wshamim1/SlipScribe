import { useState, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Upload, CheckCircle, AlertCircle, Loader, Trash2 } from 'lucide-react'
import { uploadReceipt, getReceipts, reprocessReceipt, deleteReceipt, cleanupReceipts } from '@/services/api'

interface Receipt {
  id: string
  merchant_name?: string
  total?: number | string
  purchase_date?: string
  status: string
}

export default function InboxPage() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set())
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set())
  const [cleaningUp, setCleaningUp] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Fetch receipts — auto-poll every 2s while any receipt is processing
  const { data: receiptsData, refetch: refetchReceipts } = useQuery({
    queryKey: ['receipts'],
    queryFn: () => getReceipts(),
    refetchInterval: (query) => {
      const receipts = query.state.data?.receipts ?? []
      return receipts.some((r: Receipt) => r.status === 'processing') ? 2000 : false
    },
  })

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFiles(files)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFiles(files)
    }
  }

  const handleFiles = async (files: FileList) => {
    setUploading(true)
    setUploadError(null)
    setUploadSuccess(false)

    try {
      // Upload each file
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        console.log('Uploading file:', file.name)
        await uploadReceipt(file)
      }

      setUploadSuccess(true)
      setTimeout(() => setUploadSuccess(false), 3000)
      
      // Refresh receipts
      refetchReceipts()

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error: any) {
      if (error.response?.status === 409) {
        setUploadError('Already uploaded: this file already exists in your inbox.')
      } else {
        const message = error.response?.data?.detail || error.message || 'Upload failed'
        setUploadError(message)
      }
      console.error('Upload error:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleChooseFiles = () => {
    fileInputRef.current?.click()
  }

  const handleRunOCR = async (receiptId: string) => {
    setProcessingIds(prev => new Set(prev).add(receiptId))
    try {
      await reprocessReceipt(receiptId)
      refetchReceipts()
    } catch (error: any) {
      console.error('OCR trigger failed:', error)
    } finally {
      setProcessingIds(prev => {
        const next = new Set(prev)
        next.delete(receiptId)
        return next
      })
    }
  }

  const handleDelete = async (receiptId: string) => {
    setDeletingIds(prev => new Set(prev).add(receiptId))
    try {
      await deleteReceipt(receiptId)
      refetchReceipts()
    } catch (error: any) {
      console.error('Delete failed:', error)
    } finally {
      setDeletingIds(prev => {
        const next = new Set(prev)
        next.delete(receiptId)
        return next
      })
    }
  }

  const handleCleanup = async () => {
    setCleaningUp(true)
    try {
      await cleanupReceipts('failed')
      await cleanupReceipts('pending')
      refetchReceipts()
    } catch (error: any) {
      console.error('Cleanup failed:', error)
    } finally {
      setCleaningUp(false)
    }
  }

  const receipts: Receipt[] = receiptsData?.receipts || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Receipt Inbox</h2>
        <p className="mt-1 text-sm text-gray-600">
          Upload receipts to extract line items and track spending
        </p>
      </div>

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer
          ${isDragging 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${uploading ? 'opacity-60' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/heic,application/pdf"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          disabled={uploading}
        />
        
        {uploading ? (
          <>
            <Loader className="w-12 h-12 mx-auto text-blue-500 mb-4 animate-spin" />
            <p className="text-lg font-medium text-gray-900">Uploading...</p>
          </>
        ) : (
          <>
            <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-900 mb-2">
              Drop receipt images here
            </p>
            <p className="text-sm text-gray-600 mb-4">
              or click to browse (JPEG, PNG, HEIC, PDF)
            </p>
            <button 
              onClick={handleChooseFiles}
              disabled={uploading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              Choose Files
            </button>
          </>
        )}
      </div>

      {/* Success Message */}
      {uploadSuccess && (
        <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
          <CheckCircle className="w-5 h-5" />
          <span>Receipt uploaded successfully!</span>
        </div>
      )}

      {/* Error Message */}
      {uploadError && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          <AlertCircle className="w-5 h-5" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Recent Receipts */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Receipts</h3>
          {receipts.some(r => r.status === 'failed' || r.status === 'pending') && (
            <button
              onClick={handleCleanup}
              disabled={cleaningUp}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 border border-red-200 rounded hover:bg-red-100 disabled:opacity-50 transition-colors"
            >
              {cleaningUp ? <Loader className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
              Clear failed &amp; pending
            </button>
          )}
        </div>
        
        {receipts.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <p className="text-gray-500">No receipts yet. Upload your first receipt to get started!</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Merchant</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Amount</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {receipts.map((receipt) => (
                    <tr key={receipt.id} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {receipt.merchant_name || '—'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {receipt.purchase_date ? new Date(receipt.purchase_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                        {receipt.total ? `$${Number(receipt.total).toFixed(2)}` : '—'}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`
                          px-2 py-1 rounded-full text-xs font-medium
                          ${receipt.status === 'completed' ? 'bg-green-100 text-green-800' :
                            receipt.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                            receipt.status === 'failed' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'}
                        `}>
                          {receipt.status.charAt(0).toUpperCase() + receipt.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex items-center gap-2">
                          {receipt.status !== 'processing' && (
                            <button
                              onClick={() => handleRunOCR(receipt.id)}
                              disabled={processingIds.has(receipt.id)}
                              className={`flex items-center gap-1 px-3 py-1 text-xs font-medium rounded transition-colors disabled:opacity-50 ${
                                receipt.status === 'completed'
                                  ? 'text-blue-600 border border-blue-300 hover:bg-blue-50'
                                  : 'text-white bg-blue-600 hover:bg-blue-700'
                              }`}
                            >
                              {processingIds.has(receipt.id) ? (
                                <><Loader className="w-3 h-3 animate-spin" /> Queuing…</>
                              ) : receipt.status === 'completed' ? (
                                'Re-run OCR'
                              ) : (
                                'Run OCR'
                              )}
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(receipt.id)}
                            disabled={deletingIds.has(receipt.id)}
                            className="p-1 text-gray-400 hover:text-red-600 disabled:opacity-50 transition-colors"
                            title="Delete receipt"
                          >
                            {deletingIds.has(receipt.id)
                              ? <Loader className="w-4 h-4 animate-spin" />
                              : <Trash2 className="w-4 h-4" />
                            }
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
