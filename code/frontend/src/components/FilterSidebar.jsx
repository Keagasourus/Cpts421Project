import { useState, useEffect } from 'react';
import useTags from '../hooks/useTags';

const FilterSidebar = ({ filters, onFilterChange }) => {
    const { tags, loading: tagsLoading, error: tagsError } = useTags();
    const [localStartDate, setLocalStartDate] = useState(filters.startDate || '');
    const [localEndDate, setLocalEndDate] = useState(filters.endDate || '');

    // Handle tag selection
    const handleTagChange = (tag) => {
        const currentTags = filters.selectedTags || [];
        let newTags;
        if (currentTags.includes(tag)) {
            newTags = currentTags.filter(t => t !== tag);
        } else {
            newTags = [...currentTags, tag];
        }
        onFilterChange({ ...filters, selectedTags: newTags });
    };

    // Handle date changes (debounce could be added here or in parent)
    const handleDateChange = (type, value) => {
        if (type === 'startDate') setLocalStartDate(value);
        if (type === 'endDate') setLocalEndDate(value);

        onFilterChange({
            ...filters,
            [type]: value ? parseInt(value, 10) : null
        });
    };

    return (
        <aside className="w-64 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto h-full hidden md:block">
            <h2 className="text-lg font-semibold mb-4">Filters</h2>

            {/* Date Range Section */}
            <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Time Period (Year)</h3>
                <div className="flex flex-col gap-2">
                    <input
                        type="number"
                        placeholder="Start Year"
                        value={localStartDate}
                        onChange={(e) => handleDateChange('startDate', e.target.value)}
                        className="p-2 border border-gray-300 rounded text-sm w-full"
                    />
                    <input
                        type="number"
                        placeholder="End Year"
                        value={localEndDate}
                        onChange={(e) => handleDateChange('endDate', e.target.value)}
                        className="p-2 border border-gray-300 rounded text-sm w-full"
                    />
                </div>
            </div>

            {/* Tags Section */}
            <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Tags</h3>
                {tagsLoading ? (
                    <p className="text-sm text-gray-500">Loading tags...</p>
                ) : tagsError ? (
                    <p className="text-sm text-red-500">Error loading tags.</p>
                ) : (
                    <div className="space-y-1">
                        {tags.map(tag => (
                            <label key={tag} className="flex items-center space-x-2 cursor-pointer hover:bg-gray-100 p-1 rounded">
                                <input
                                    type="checkbox"
                                    checked={(filters.selectedTags || []).includes(tag)}
                                    onChange={() => handleTagChange(tag)}
                                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-sm text-gray-700">{tag}</span>
                            </label>
                        ))}
                    </div>
                )}
            </div>
        </aside>
    );
};

export default FilterSidebar;
