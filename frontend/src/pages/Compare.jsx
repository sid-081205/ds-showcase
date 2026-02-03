import { useState, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { UserPlus, Trash2, Play, Users } from "lucide-react"
import { useNavigate } from "react-router-dom"

export default function Compare() {
    const [users, setUsers] = useState([])
    const [loading, setLoading] = useState(true)
    const [addingUser, setAddingUser] = useState(false)
    const navigate = useNavigate()

    useEffect(() => {
        fetchUsers()
        // Poll for user updates every 3 seconds
        const interval = setInterval(fetchUsers, 3000)
        return () => clearInterval(interval)
    }, [])

    const fetchUsers = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8888/users')
            const data = await response.json()
            setUsers(data.users || [])
            setLoading(false)
        } catch (error) {
            console.error('Error fetching users:', error)
            setLoading(false)
        }
    }

    const handleAddUser = async () => {
        console.log('🔵 Add User button clicked!')
        setAddingUser(true)
        try {
            console.log('📡 Fetching /add-user endpoint...')
            const response = await fetch('http://127.0.0.1:8888/add-user')
            const data = await response.json()
            console.log('✅ Got OAuth URL:', data.url)

            // Open Spotify OAuth in popup
            const width = 600
            const height = 700
            const left = window.screen.width / 2 - width / 2
            const top = window.screen.height / 2 - height / 2

            console.log('🪟 Opening popup...')
            const popup = window.open(
                data.url,
                'Spotify Login',
                `width=${width},height=${height},left=${left},top=${top}`
            )

            // Listen for callback
            const checkPopup = setInterval(() => {
                if (popup.closed) {
                    console.log('🔴 Popup closed, refreshing users...')
                    clearInterval(checkPopup)
                    setAddingUser(false)
                    fetchUsers()
                }
            }, 500)
        } catch (error) {
            console.error('❌ Error adding user:', error)
            setAddingUser(false)
        }
    }

    const handleDeleteUser = async (userId) => {
        if (!confirm('Are you sure you want to remove this user?')) return

        try {
            await fetch(`http://127.0.0.1:8888/user/${userId}`, {
                method: 'DELETE'
            })
            fetchUsers()
        } catch (error) {
            console.error('Error deleting user:', error)
        }
    }

    const handleCollectData = async (userId) => {
        try {
            console.log(`📊 Collecting data for user ${userId}...`)
            await fetch(`http://127.0.0.1:8888/collect-user-data/${userId}`, {
                method: 'POST'
            })
            console.log('✅ Data collection request sent')
            // Data collection happens in background, status will update via polling
        } catch (error) {
            console.error('❌ Error collecting data:', error)
        }
    }

    const handleAnalyzeUser = async (userId) => {
        try {
            console.log(`🔬 Starting analysis for user ${userId}...`)
            await fetch(`http://127.0.0.1:8888/analyze-user/${userId}`, {
                method: 'POST'
            })
            console.log('✅ Analysis request sent')
            // Analysis happens in background, status will update via polling
        } catch (error) {
            console.error('❌ Error analyzing user:', error)
        }
    }

    const handleSeeComparisons = () => {
        navigate('/comparisons')
    }

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-400'
            case 'running': return 'bg-yellow-400'
            case 'failed': return 'bg-red-200'
            default: return 'bg-gray-200'
        }
    }

    const getStatusText = (status) => {
        switch (status) {
            case 'completed': return 'Analysis Complete ⚡️'
            case 'running': return 'Processing Data...'
            case 'failed': return 'Analysis Failed'
            default: return 'Pending'
        }
    }

    const readyUsers = users.filter(u => u.analysis_status === 'completed')
    const canCompare = readyUsers.length >= 2

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <p className="text-2xl font-black">Loading...</p>
            </div>
        )
    }

    return (
        <div className="container mx-auto py-12 px-4 space-y-12">
            <header className="text-center space-y-4">
                <h1 className="text-6xl font-black uppercase tracking-tighter">Music Comparison</h1>
                <p className="text-xl font-bold bg-white border-2 border-black inline-block px-4 py-1 neo-brutal">
                    {canCompare
                        ? `🎉 ${readyUsers.length} Users Ready to Compare!`
                        : "Add at least 2 users to see how your tastes overlap"}
                </p>

                {canCompare && (
                    <div className="pt-4">
                        <Button
                            onClick={handleSeeComparisons}
                            size="lg"
                            className="neo-brutal bg-accent hover:bg-black hover:text-white px-12 py-8 text-2xl font-black transition-all"
                        >
                            <Users className="mr-4 h-8 w-8" />
                            SEE COMPARISON RESULTS
                        </Button>
                    </div>
                )}
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Existing Users */}
                {users.map((user) => (
                    <Card
                        key={user.id}
                        className="neo-brutal bg-primary hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] transition-all"
                    >
                        <CardHeader className="border-b-[3px] border-black pb-4">
                            <CardTitle className="flex justify-between items-start">
                                <div className="flex-1">
                                    <p className="text-xl font-black">{user.display_name}</p>
                                    <p className="text-xs font-medium opacity-70 mt-1">
                                        {user.email || user.spotify_user_id}
                                    </p>
                                </div>
                                <button
                                    onClick={() => handleDeleteUser(user.id)}
                                    className="p-2 hover:bg-black/10 rounded border-2 border-black"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6 space-y-4">
                            {/* Status Badge */}
                            <div className={`${getStatusColor(user.analysis_status)} border-2 border-black p-3 text-center`}>
                                <p className="font-black text-sm uppercase">
                                    {getStatusText(user.analysis_status)}
                                </p>
                                {user.analysis_status === 'running' && (
                                    <div className="mt-2 w-full bg-white border-2 border-black h-2">
                                        <div
                                            className="h-full bg-black transition-all"
                                            style={{ width: `${user.analysis_progress || 0}%` }}
                                        />
                                    </div>
                                )}
                            </div>

                            {/* Action Buttons */}
                            <div className="space-y-2">
                                {user.analysis_status === 'pending' && (
                                    <>
                                        <Button
                                            onClick={() => handleCollectData(user.id)}
                                            className="w-full neo-brutal bg-white hover:bg-gray-100 font-bold"
                                            size="sm"
                                        >
                                            Collect Spotify Data
                                        </Button>
                                        <Button
                                            onClick={() => handleAnalyzeUser(user.id)}
                                            className="w-full neo-brutal bg-accent hover:bg-accent/90 font-bold"
                                            size="sm"
                                        >
                                            <Play className="mr-2 h-4 w-4" />
                                            Analyze Music
                                        </Button>
                                    </>
                                )}

                                {user.analysis_status === 'failed' && (
                                    <Button
                                        onClick={() => handleAnalyzeUser(user.id)}
                                        className="w-full neo-brutal bg-red-400 hover:bg-red-500 font-bold"
                                        size="sm"
                                    >
                                        Retry Analysis
                                    </Button>
                                )}

                                {user.analysis_status === 'completed' && (
                                    <div className="bg-green-100 border-2 border-black p-2 text-center">
                                        <p className="text-xs font-bold">Ready for Comparison!</p>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                ))}

                {/* Add User Card */}
                <Card className="neo-brutal bg-white border-dashed border-4 hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] transition-all cursor-pointer">
                    <CardContent className="flex flex-col items-center justify-center h-full min-h-[300px] p-8">
                        <button
                            onClick={handleAddUser}
                            disabled={addingUser}
                            className="flex flex-col items-center gap-4 w-full"
                        >
                            <div className="w-20 h-20 rounded-full bg-black flex items-center justify-center">
                                <UserPlus className="h-10 w-10 text-white" />
                            </div>
                            <div className="text-center">
                                <p className="text-2xl font-black uppercase">
                                    {addingUser ? 'Opening Spotify...' : 'Add User'}
                                </p>
                                <p className="text-sm font-medium opacity-70 mt-2">
                                    Connect a Spotify account to compare
                                </p>
                            </div>
                        </button>
                    </CardContent>
                </Card>
            </div>

            {/* Instructions */}
            <div className="bg-accent border-4 border-black p-8 text-center mt-12">
                <h2 className="text-2xl font-black mb-4 uppercase">How It Works</h2>
                <div className="grid md:grid-cols-3 gap-6 text-left">
                    <div>
                        <div className="text-4xl font-black mb-2">1.</div>
                        <p className="font-bold">Click "Add User" and connect via Spotify</p>
                    </div>
                    <div>
                        <div className="text-4xl font-black mb-2">2.</div>
                        <p className="font-bold">Collect data and analyze their music taste</p>
                    </div>
                    <div>
                        <div className="text-4xl font-black mb-2">3.</div>
                        <p className="text-sm font-medium uppercase mb-1">Mood Comparison & Recommendation</p>
                        <p className="text-sm font-medium">Moods are compared with friends, and a kNN algorithm is used to predict/recommend new songs (using our merged.csv)</p>
                    </div>
                </div>
            </div>

            {users.length > 0 && !canCompare && (
                <div className="bg-yellow-200 border-4 border-black p-6 text-center">
                    <p className="font-black text-lg">
                        Add at least 2 analyzed users to see comparisons!
                    </p>
                    <p className="font-medium mt-2 opacity-70">
                        ({readyUsers.length}/2 users analyzed)
                    </p>
                </div>
            )}
        </div>
    )
}
