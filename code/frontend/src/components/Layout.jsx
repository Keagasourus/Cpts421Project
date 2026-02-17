import { Link, Outlet } from 'react-router-dom';

const Layout = () => {
    return (
        <div className="flex h-screen flex-col">
            <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10 shadow-sm">
                <div className="flex items-center space-x-8">
                    <h1 className="text-xl font-bold text-gray-800">Academic Artifact Database</h1>
                    <nav className="flex space-x-4">
                        <Link to="/" className="text-gray-600 hover:text-blue-600 font-medium">Home</Link>
                        <Link to="/search" className="text-gray-600 hover:text-blue-600 font-medium">Data Gallery</Link>
                        <Link to="/map" className="text-gray-600 hover:text-blue-600 font-medium">Map View</Link>
                    </nav>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                <Outlet />
            </div>
        </div>
    );
};

export default Layout;
