import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import * as api from '../api'

const SUGGESTED_SLOTS = ['9am-10am', '10am-11am', '11am-12pm', '1pm-2pm', '2pm-3pm', '3pm-4pm']

export default function Booking() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [bookings, setBookings] = useState([])
  const [timeSlot, setTimeSlot] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  function handleAuthError(err) {
    if (err.status === 401) {
      logout()
      navigate('/login', { replace: true })
      return true
    }
    return false
  }

  async function refresh() {
    setError('')
    try {
      const data = await api.listBookings()
      setBookings(data)
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleCreate(e) {
    e.preventDefault()
    if (!timeSlot.trim()) return
    setError('')
    try {
      await api.createBooking(timeSlot.trim())
      setTimeSlot('')
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleDelete(id) {
    setError('')
    try {
      await api.deleteBooking(id)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleEdit(booking) {
    const next = window.prompt('New time slot:', booking.time_slot)
    if (next === null) return
    const trimmed = next.trim()
    if (!trimmed || trimmed === booking.time_slot) return
    setError('')
    try {
      await api.updateBooking(booking.id, trimmed)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <h1>Appointments</h1>
          <span className="muted">
            Signed in as <strong>{user.username}</strong>
            {user.is_admin && <span className="badge">admin</span>}
          </span>
        </div>
        <button className="secondary" onClick={handleLogout}>Log out</button>
      </header>

      <form className="card row" onSubmit={handleCreate}>
        <input
          aria-label="Time slot"
          placeholder="e.g. 10am-11am"
          value={timeSlot}
          onChange={(e) => setTimeSlot(e.target.value)}
          list="slot-suggestions"
        />
        <datalist id="slot-suggestions">
          {SUGGESTED_SLOTS.map((s) => <option key={s} value={s} />)}
        </datalist>
        <button type="submit">Book slot</button>
      </form>

      {error && <div className="error" role="alert">{error}</div>}

      {user.is_admin && (
        <div className="banner">Admin view: showing all appointments from every user.</div>
      )}

      <div className="card">
        {loading ? (
          <p className="muted">Loading…</p>
        ) : bookings.length === 0 ? (
          <p className="muted">No bookings yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                {user.is_admin && <th>User</th>}
                <th>Time slot</th>
                <th>Created</th>
                <th aria-label="Actions"></th>
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.id}>
                  <td>{b.id}</td>
                  {user.is_admin && <td>{b.username}</td>}
                  <td>{b.time_slot}</td>
                  <td className="muted">{new Date(b.created_at).toLocaleString()}</td>
                  <td className="actions">
                    <button className="link" onClick={() => handleEdit(b)}>Edit</button>
                    <button className="link danger" onClick={() => handleDelete(b.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
