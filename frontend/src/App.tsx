import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import InboxPage from './pages/InboxPage'
import ReceiptDetailPage from './pages/ReceiptDetailPage'
import DashboardPage from './pages/DashboardPage'
import InsightsPage from './pages/InsightsPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<InboxPage />} />
          <Route path="receipts/:id" element={<ReceiptDetailPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="insights" element={<InsightsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
