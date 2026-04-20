import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const EditObjectPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { isAdmin } = useAuth();
    
    const isEditMode = Boolean(id);
    const [loading, setLoading] = useState(isEditMode);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    
    // Form fields
    const [formData, setFormData] = useState({
        object_type: '',
        material: '',
        findspot: '',
        date_display: '',
        date_start: 0,
        date_end: 0,
        inventory_number: '',
        description: '',
        latitude: '',
        longitude: ''
    });

    // Image Upload
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [existingImages, setExistingImages] = useState([]);

    useEffect(() => {
        if (!isAdmin) {
            navigate('/login');
            return;
        }

        if (isEditMode) {
            const fetchObject = async () => {
                try {
                    const response = await api.get(`/objects/${id}`);
                    const obj = response.data;
                    setFormData({
                        object_type: obj.object_type || '',
                        material: obj.material || '',
                        findspot: obj.findspot || '',
                        date_display: obj.date_display || '',
                        date_start: obj.date_start || 0,
                        date_end: obj.date_end || 0,
                        inventory_number: obj.inventory_number || '',
                        description: obj.description || '',
                        latitude: obj.latitude || '',
                        longitude: obj.longitude || ''
                    });
                    setExistingImages(obj.images || []);
                } catch (err) {
                    setError('Failed to fetch object details');
                } finally {
                    setLoading(false);
                }
            };
            fetchObject();
        }
    }, [id, isAdmin, navigate, isEditMode]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleFileChange = (e) => {
        setSelectedFiles(Array.from(e.target.files));
    };

    const handleRemoveExistingImage = (indexToRemove) => {
        setExistingImages(prev => prev.filter((_, idx) => idx !== indexToRemove));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError('');

        try {
            // First, upload new images
            let newImageUrls = [];
            if (selectedFiles.length > 0) {
                const formDataParams = new FormData();
                selectedFiles.forEach(file => formDataParams.append('files', file));
                
                const uploadResponse = await api.post('/upload-images', formDataParams, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                newImageUrls = uploadResponse.data.urls.map(url => ({ file_url: url, image_type: 'Photograph', view_type: 'Front' }));
            }

            // Combine with existing images
            const finalImages = [
                ...existingImages.map(img => ({ file_url: img.file_url, image_type: img.image_type, view_type: img.view_type })),
                ...newImageUrls
            ];

            const payload = {
                ...formData,
                date_start: parseInt(formData.date_start, 10),
                date_end: parseInt(formData.date_end, 10),
                latitude: formData.latitude ? parseFloat(formData.latitude) : null,
                longitude: formData.longitude ? parseFloat(formData.longitude) : null,
                images: finalImages
            };

            if (isEditMode) {
                await api.put(`/objects/${id}`, payload);
            } else {
                const createRes = await api.post('/objects', payload);
                navigate(`/objects/${createRes.data.id}`);
                return;
            }

            navigate(`/objects/${id}`);
        } catch (err) {
            setError(err.response?.data?.detail || 'Operation failed');
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div className="max-w-4xl mx-auto p-4">
            <h1 className="text-3xl font-bold mb-6">{isEditMode ? 'Edit Artifact' : 'Add New Artifact'}</h1>
            {error && <div className="p-4 mb-6 bg-red-100 text-red-700 rounded">{error}</div>}
            
            <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 shadow rounded border border-gray-100">
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Type *</label>
                        <input required type="text" name="object_type" value={formData.object_type} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. Vase"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Inventory Number</label>
                        <input type="text" name="inventory_number" value={formData.inventory_number} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Material</label>
                        <input type="text" name="material" value={formData.material} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. Clay"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Findspot</label>
                        <input type="text" name="findspot" value={formData.findspot} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Date Display *</label>
                        <input required type="text" name="date_display" value={formData.date_display} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. c. 300 BC"/>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Start Year *</label>
                            <input required type="number" name="date_start" value={formData.date_start} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">End Year *</label>
                            <input required type="number" name="date_end" value={formData.date_end} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                        </div>
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Latitude</label>
                        <input type="number" step="any" name="latitude" value={formData.latitude} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Longitude</label>
                        <input type="number" step="any" name="longitude" value={formData.longitude} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700">Description</label>
                    <textarea name="description" value={formData.description} onChange={handleChange} rows="4" className="mt-1 w-full p-2 border rounded"></textarea>
                </div>

                <div className="border-t pt-6">
                    <h2 className="text-xl font-semibold mb-4">Images</h2>
                    {existingImages.length > 0 && (
                        <div className="mb-4">
                            <p className="text-sm font-medium text-gray-700 mb-2">Existing Images:</p>
                            <div className="flex flex-wrap gap-4">
                                {existingImages.map((img, idx) => (
                                    <div key={idx} className="relative group">
                                        <img src={img.file_url} alt="artifact" className="h-24 w-24 object-cover rounded shadow" />
                                        <button type="button" onClick={() => handleRemoveExistingImage(idx)} className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 w-6 h-6 flex items-center justify-center shadow opacity-80 hover:opacity-100">
                                            &times;
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Upload New Images</label>
                        <input type="file" multiple accept="image/*" onChange={handleFileChange} className="mt-1 block w-full text-sm text-gray-500
                            file:mr-4 file:py-2 file:px-4
                            file:rounded file:border-0
                            file:text-sm file:font-semibold
                            file:bg-blue-50 file:text-blue-700
                            hover:file:bg-blue-100" 
                        />
                    </div>
                </div>

                <div className="flex justify-end gap-4 border-t pt-4">
                    <button type="button" onClick={() => navigate(-1)} className="px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded">
                        Cancel
                    </button>
                    <button type="submit" disabled={saving} className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded disabled:bg-blue-300 transition">
                        {saving ? 'Saving...' : 'Save Artifact'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default EditObjectPage;
