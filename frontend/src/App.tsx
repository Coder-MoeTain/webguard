import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DatasetGeneration from './pages/DatasetGeneration'
import DatasetUpload from './pages/DatasetUpload'
import DatasetBrowser from './pages/DatasetBrowser'
import FeatureExtraction from './pages/FeatureExtraction'
import TrainingConfig from './pages/TrainingConfig'
import TrainingMonitor from './pages/TrainingMonitor'
import ModelEvaluation from './pages/ModelEvaluation'
import FeatureImportance from './pages/FeatureImportance'
import RobustnessAnalysis from './pages/RobustnessAnalysis'
import InferenceTesting from './pages/InferenceTesting'
import ModelManagement from './pages/ModelManagement'
import ModelDetail from './pages/ModelDetail'
import ReportExport from './pages/ReportExport'
import VulnerabilityTestLab from './pages/VulnerabilityTestLab'
import IDSDashboard from './pages/IDSDashboard'

function App() {
  const { isAuthenticated } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
      <Route path="/" element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
        <Route index element={<Dashboard />} />
        <Route path="datasets/generate" element={<DatasetGeneration />} />
        <Route path="datasets/upload" element={<DatasetUpload />} />
        <Route path="datasets/browse" element={<DatasetBrowser />} />
        <Route path="features/extract" element={<FeatureExtraction />} />
        <Route path="training/config" element={<TrainingConfig />} />
        <Route path="training/monitor/:jobId" element={<TrainingMonitor />} />
        <Route path="evaluation" element={<ModelEvaluation />} />
        <Route path="feature-importance" element={<FeatureImportance />} />
        <Route path="robustness" element={<RobustnessAnalysis />} />
        <Route path="inference" element={<InferenceTesting />} />
        <Route path="test-lab" element={<VulnerabilityTestLab />} />
        <Route path="ids" element={<IDSDashboard />} />
        <Route path="models" element={<ModelManagement />} />
        <Route path="models/:modelId" element={<ModelDetail />} />
        <Route path="reports" element={<ReportExport />} />
      </Route>
    </Routes>
  )
}

export default App
