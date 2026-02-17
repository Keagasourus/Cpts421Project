import { useState, useEffect } from 'react';
import api from '../services/api';

const useObject = (id) => {
    const [object, setObject] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!id) return;

        const fetchObject = async () => {
            setLoading(true);
            try {
                const response = await api.get(`/objects/${id}`);
                setObject(response.data);
                setLoading(false);
            } catch (err) {
                console.error(`Failed to fetch object ${id}:`, err);
                setError(err);
                setLoading(false);
            }
        };

        fetchObject();
    }, [id]);

    return { object, loading, error };
};

export default useObject;
