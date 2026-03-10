import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const uploadReceipt = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await axios.post(`${API_BASE}/receipts/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } catch (error) {
    throw error
  }
}

export const getReceipts = async (limit = 50, offset = 0) => {
  try {
    const response = await axios.get(`${API_BASE}/receipts`, {
      params: { limit, offset },
    })
    return response.data
  } catch (error) {
    throw error
  }
}

export const getReceipt = async (receiptId: string) => {
  try {
    const response = await axios.get(`${API_BASE}/receipts/${receiptId}`)
    return response.data
  } catch (error) {
    throw error
  }
}

export const reprocessReceipt = async (receiptId: string) => {
  try {
    const response = await axios.post(`${API_BASE}/receipts/${receiptId}/reprocess`)
    return response.data
  } catch (error) {
    throw error
  }
}

export const deleteReceipt = async (receiptId: string) => {
  await axios.delete(`${API_BASE}/receipts/${receiptId}`)
}

export const cleanupReceipts = async (receiptStatus = 'failed') => {
  const response = await axios.delete(`${API_BASE}/receipts/cleanup`, {
    params: { receipt_status: receiptStatus },
  })
  return response.data
}

export const getStats = async () => {
  const response = await axios.get(`${API_BASE}/receipts/stats`)
  return response.data
}
