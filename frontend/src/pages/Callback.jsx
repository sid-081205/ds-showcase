import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import axios from 'axios'

const API_URL = 'http://localhost:3001'

function Callback({ setUser }) {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  useEffect(() => {
    const code = searchParams.get('code')

    if (code) {
      // Exchange code for access token
      axios.post(`${API_URL}/auth/callback`, { code })
        .then(response => {
          const { access_token, user } = response.data

          // Store token and user info
          localStorage.setItem('spotify_access_token', access_token)
          localStorage.setItem('user_id', user.id)

          setUser(user)
          navigate('/insights')
        })
        .catch(error => {
          console.error('Authentication failed:', error)
          navigate('/')
        })
    } else {
      navigate('/')
    }
  }, [searchParams, navigate, setUser])

  return (
    <div className="loading">
      connecting to spotify...
    </div>
  )
}

export default Callback
