import { useParams, useNavigate } from 'react-router-dom';
import useObject from '../hooks/useObject';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

const ObjectPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { object, loading, error } = useObject(id);
    const { isAdmin } = useAuth();

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete this artifact?')) return;
        try {
            await api.delete(`/objects/${id}`);
            navigate('/search');
        } catch (err) {
            alert('Failed to delete object: ' + (err.response?.data?.detail || err.message));
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading object details...</div>;
    if (error) return <div className="p-8 text-center text-red-500">Error loading object.</div>;
    if (!object) return <div className="p-8 text-center text-gray-500">Object not found.</div>;

    return (
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
            <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                    <h1 className="text-2xl font-bold text-gray-900">{object.object_type}</h1>
                    <div className="space-x-4">
                        {isAdmin && (
                            <>
                                <button onClick={() => navigate(`/objects/${id}/edit`)} className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700">Edit</button>
                                <button onClick={handleDelete} className="px-3 py-1 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700">Delete</button>
                            </>
                        )}
                        <button
                            onClick={() => navigate(-1)}
                            className="text-sm font-medium text-gray-600 hover:text-gray-900"
                        >
                            Back
                        </button>
                    </div>
                </div>

                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Images Section */}
                    <div className="space-y-4">
                        {object.images && object.images.length > 0 ? (
                            object.images.map((img, index) => (
                                <div key={img.id || index} className="rounded-lg overflow-hidden border border-gray-200 bg-gray-100">
                                    <img
                                        src={img.file_url}
                                        alt={`${object.object_type} - ${img.view_type || 'View'}`}
                                        className="w-full h-auto object-contain min-h-[300px]"
                                        referrerPolicy="no-referrer"
                                        onError={(e) => { e.target.onerror = null; e.target.src = 'https://via.placeholder.com/600x400?text=Error+Loading+Image+from+Museum+Server' }}
                                    />
                                    {img.image_type && (
                                        <div className="p-2 text-xs text-center text-gray-500 bg-white border-t border-gray-200">
                                            {img.image_type} - {img.view_type}
                                        </div>
                                    )}
                                </div>
                            ))
                        ) : (
                            <div className="flex items-center justify-center h-64 bg-gray-100 rounded text-gray-400">
                                No Images Available
                            </div>
                        )}
                    </div>

                    {/* Metadata Section */}
                    <div className="space-y-6">
                        {object.description && (
                            <div>
                                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Description</h2>
                                <p className="text-gray-900 text-sm leading-relaxed">{object.description}</p>
                            </div>
                        )}
                        <div>
                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Basic Info</h2>
                            <dl className="grid grid-cols-1 gap-y-2 text-sm">
                                <div className="grid grid-cols-3">
                                    <dt className="text-gray-500">Material</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.material || 'N/A'}</dd>
                                </div>
                                <div className="grid grid-cols-3">
                                    <dt className="text-gray-500">Date</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.date_display}</dd>
                                </div>
                                <div className="grid grid-cols-3">
                                    <dt className="text-gray-500">Findspot</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.findspot || 'Unknown'}</dd>
                                </div>
                                {object.inventory_number && (
                                    <div className="grid grid-cols-3">
                                        <dt className="text-gray-500">Inventory #</dt>
                                        <dd className="col-span-2 font-medium text-gray-900">{object.inventory_number}</dd>
                                    </div>
                                )}
                            </dl>
                        </div>

                        {/* Dimensions */}
                        <div>
                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Dimensions</h2>
                            <dl className="grid grid-cols-1 gap-y-2 text-sm">
                                <div className="grid grid-cols-3">
                                    <dt className="text-gray-500">Height</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.height ? `${object.height} cm` : 'N/A'}</dd>
                                </div>
                                <div className="grid grid-cols-3">
                                    <dt className="text-gray-500">Width</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.width ? `${object.width} cm` : 'N/A'}</dd>
                                </div>
                                <div className="grid grid-cols-3">
                                    <dt className="text-gray-500">Depth</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.depth ? `${object.depth} cm` : 'N/A'}</dd>
                                </div>
                            </dl>
                        </div>

                        {/* Bibliography */}
                        {object.bibliography && object.bibliography.length > 0 && (
                            <div>
                                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Bibliography</h2>
                                <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
                                    {object.bibliography.map((ref, idx) => (
                                        <li key={idx}>{ref}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
};

export default ObjectPage;
