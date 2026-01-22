import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import MoodAnalysis from './pages/MoodAnalysis'
import Compare from './pages/Compare'

function App() {
    return (
        <Routes>
            <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="mood-analysis" element={<MoodAnalysis />} />
                <Route path="compare" element={<Compare />} />
            </Route>
        </Routes>
    )
}

export default App
