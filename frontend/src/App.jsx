import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import ProtectedRoute from './components/ProtectedRoute'

import PublicLayout from './layouts/PublicLayout'
import PatientLayout from './layouts/PatientLayout'
import DoctorLayout from './layouts/DoctorLayout'

import Landing from './pages/Landing'
import HowItWorks from './pages/HowItWorks'
import Login from './pages/Login'
import Register from './pages/Register'
import NotFound from './pages/NotFound'

import PatientDashboard from './pages/patient/Dashboard'
import Intake from './pages/patient/Intake'
import Review from './pages/patient/Review'
import Matching from './pages/patient/Matching'
import Consultation from './pages/patient/Consultation'
import History from './pages/patient/History'
import Privacy from './pages/patient/Privacy'

import DoctorDashboard from './pages/doctor/Dashboard'
import DoctorConsultations from './pages/doctor/Consultations'
import DoctorCase from './pages/doctor/CaseView'
import DoctorProfile from './pages/doctor/Profile'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
          </Route>

          <Route
            element={
              <ProtectedRoute role="patient">
                <PatientLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/patient/dashboard" element={<PatientDashboard />} />
            <Route path="/patient/intake" element={<Intake />} />
            <Route path="/patient/review" element={<Review />} />
            <Route path="/patient/matching" element={<Matching />} />
            <Route path="/patient/consultation" element={<Consultation />} />
            <Route path="/patient/history" element={<History />} />
            <Route path="/patient/privacy" element={<Privacy />} />
          </Route>

          <Route
            element={
              <ProtectedRoute role="professional">
                <DoctorLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/doctor/dashboard" element={<DoctorDashboard />} />
            <Route path="/doctor/consultations" element={<DoctorConsultations />} />
            <Route path="/doctor/consultation/:id" element={<DoctorCase />} />
            <Route path="/doctor/profile" element={<DoctorProfile />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
