import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from '@/components/Layout'
import HomePage from '@/pages/HomePage'
import UploadPage from '@/pages/UploadPage'
import AssessmentsPage from '@/pages/AssessmentsPage'
import AssessmentDetailPage from '@/pages/AssessmentDetailPage'
import BatchAssessmentPage from '@/pages/BatchAssessmentPage'
import ReportsPage from '@/pages/ReportsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/assessments" element={<AssessmentsPage />} />
          <Route path="/assessments/:id" element={<AssessmentDetailPage />} />
          <Route path="/batch/:batchId" element={<BatchAssessmentPage />} />
          <Route path="/reports" element={<ReportsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
