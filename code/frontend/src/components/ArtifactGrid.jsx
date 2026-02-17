import { Link } from 'react-router-dom';

const ArtifactCard = ({ artifact }) => {
    // Assuming artifact.images is an array and we take the first one as thumbnail
    const thumbnail = artifact.images && artifact.images.length > 0
        ? artifact.images[0].file_url
        : 'https://via.placeholder.com/300x200?text=No+Image';

    return (
        <Link to={`/objects/${artifact.id}`} className="block group">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
                <div className="aspect-w-3 aspect-h-2">
                    <img
                        src={thumbnail}
                        alt={artifact.object_type}
                        className="w-full h-48 object-cover group-hover:opacity-90 transition-opacity"
                    />
                </div>
                <div className="p-4">
                    <h3 className="font-semibold text-lg text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">{artifact.object_type}</h3>
                    <p className="text-sm text-gray-500 mb-2">{artifact.date_display}</p>
                    <div className="flex flex-wrap gap-1">
                        {/* If tags were available on the object response, we'd list them here */}
                    </div>
                </div>
            </div>
        </Link>
    );
};

const ArtifactGrid = ({ artifacts, loading, error }) => {
    if (loading) return <div className="p-8 text-center text-gray-500">Loading artifacts...</div>;
    if (error) return <div className="p-8 text-center text-red-500">Error loading artifacts.</div>;
    if (!artifacts || artifacts.length === 0) return <div className="p-8 text-center text-gray-500">No artifacts found.</div>;

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-4">
            {artifacts.map(artifact => (
                <ArtifactCard key={artifact.id} artifact={artifact} />
            ))}
        </div>
    );
};

export default ArtifactGrid;
