import { useState, useEffect } from 'react';
import api from '../services/api';

const useMapData = () => {
    const [mapData, setMapData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchMapData = async () => {
            try {
                const response = await api.get('/objects/map');
                setMapData(response.data);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch map data:", err);
                setError(err);
                setLoading(false);
            }
        };

        fetchMapData();
    }, []);

    return { mapData, loading, error };
};

export default useMapData;
