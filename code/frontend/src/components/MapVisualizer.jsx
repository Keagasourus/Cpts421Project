import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import useMapData from '../hooks/useMapData';
import L from 'leaflet';

// Fix for default marker icon in React-Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const MapVisualizer = () => {
    const { mapData, loading, error } = useMapData();

    if (loading) return <div className="h-64 flex items-center justify-center bg-gray-100 rounded">Loading Map...</div>;
    if (error) return <div className="h-64 flex items-center justify-center bg-red-50 text-red-500 rounded">Error loading map.</div>;

    // Default center (e.g., Mediterranean or global) - can be adjusted
    const defaultCenter = [34.0, 18.0];
    const defaultZoom = 5;

    return (
        <div className="h-full w-full rounded-lg overflow-hidden border border-gray-300 shadow-sm z-0">
            <MapContainer center={defaultCenter} zoom={defaultZoom} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {mapData.map((item) => (
                    item.latitude && item.longitude ? (
                        <Marker key={item.id} position={[item.latitude, item.longitude]}>
                            <Popup>
                                <strong>{item.name}</strong>
                                <br />
                                <Link to={`/objects/${item.id}`} className="text-blue-600 hover:underline">View Details</Link>
                            </Popup>
                        </Marker>
                    ) : null
                ))}
            </MapContainer>
        </div>
    );
};

export default MapVisualizer;
