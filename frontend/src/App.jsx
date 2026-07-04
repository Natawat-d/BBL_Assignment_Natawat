import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './auth.jsx'
import Login from './pages/Login.jsx'
import Booking from './pages/Booking.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/booking"
        element={
          <ProtectedRoute>
            <Booking />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/booking" replace />} />
    </Routes>
  )
}
