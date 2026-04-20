import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import SearchPage from './pages/SearchPage';
import MapPage from './pages/MapPage';
import ObjectPage from './pages/ObjectPage';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import EditObjectPage from './pages/EditObjectPage';
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/objects/new" element={<EditObjectPage />} />
            <Route path="/objects/:id" element={<ObjectPage />} />
            <Route path="/objects/:id/edit" element={<EditObjectPage />} />
            <Route path="/login" element={<LoginPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
