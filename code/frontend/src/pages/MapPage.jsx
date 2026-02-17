import MapVisualizer from '../components/MapVisualizer';

const MapPage = () => {
    return (
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
            <div className="max-w-7xl mx-auto h-full flex flex-col">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Geographic Distribution</h2>
                <div className="flex-1 min-h-[500px]">
                    <MapVisualizer />
                </div>
            </div>
        </main>
    );
};

export default MapPage;
