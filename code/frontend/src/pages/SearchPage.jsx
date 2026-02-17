import { useState } from 'react';
import FilterSidebar from '../components/FilterSidebar';
import ArtifactGrid from '../components/ArtifactGrid';
import useArtifacts from '../hooks/useArtifacts';

const SearchPage = () => {
    const [filters, setFilters] = useState({
        search: '',
        selectedTags: [],
        startDate: null,
        endDate: null
    });

    const { artifacts, loading, error } = useArtifacts(filters);

    return (
        <div className="flex flex-1 overflow-hidden h-full">
            <FilterSidebar filters={filters} onFilterChange={setFilters} />

            <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
                <div className="max-w-7xl mx-auto space-y-6">
                    <div className="flex justify-between items-center mb-4">
                        <div className="w-full md:w-1/2">
                            <input
                                type="text"
                                placeholder="Search materials..."
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                                value={filters.search}
                            />
                        </div>
                    </div>

                    {/* Results Section */}
                    <section>
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-semibold text-gray-800">
                                Search Results ({artifacts ? artifacts.length : 0})
                            </h2>
                        </div>
                        <ArtifactGrid artifacts={artifacts} loading={loading} error={error} />
                    </section>
                </div>
            </main>
        </div>
    );
};

export default SearchPage;
