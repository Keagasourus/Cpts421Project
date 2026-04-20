import { useState, useEffect } from 'react';
import api from '../services/api';

const useArtifacts = (filters) => {
    const [artifacts, setArtifacts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchArtifacts = async () => {
            setLoading(true);
            try {
                const params = {};

                if (filters.search) params.material = filters.search;
                if (filters.startDate) params.date_start = filters.startDate;
                if (filters.endDate) params.date_end = filters.endDate;

                // TODO: Backend does not support tag-based filtering yet.
                // When backend adds a 'tags' query param, pass filters.selectedTags here.

                const response = await api.get('/objects/search', { params });
                setArtifacts(response.data);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch artifacts:", err);
                setError(err);
                setLoading(false);
            }
        };

        fetchArtifacts();
    }, [filters]); // Re-run when filters change

    return { artifacts, loading, error };
};

export default useArtifacts;
