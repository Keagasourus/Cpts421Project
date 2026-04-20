import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Layout = () => {
    const { user, isAdmin, logout } = useAuth();

    return (
        <div className="flex h-screen flex-col">
            <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10 shadow-sm">
                <div className="flex items-center space-x-8">
                    <h1 className="text-xl font-bold text-gray-800">Academic Artifact Database</h1>
                    <nav className="flex space-x-4">
                        <Link to="/" className="text-gray-600 hover:text-blue-600 font-medium">Home</Link>
                        <Link to="/search" className="text-gray-600 hover:text-blue-600 font-medium">Data Gallery</Link>
                        <Link to="/map" className="text-gray-600 hover:text-blue-600 font-medium">Map View</Link>
                        {isAdmin && <Link to="/objects/new" className="text-blue-600 hover:text-blue-800 font-medium ml-4">+ Add Artifact</Link>}
                    </nav>
                </div>
                <div>
                    {user ? (
                        <div className="flex items-center space-x-4">
                            <span className="text-sm font-medium text-gray-700">Hi, {user.username}</span>
                            <button onClick={logout} className="text-sm font-medium text-red-600 hover:text-red-800">Logout</button>
                        </div>
                    ) : (
                        <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-blue-600">Admin Login</Link>
                    )}
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                <Outlet />
            </div>
        </div>
    );
};

export default Layout;
