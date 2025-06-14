import React from 'react';

const GroupsPage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md text-center">
        <h1 className="text-3xl font-bold mb-4">Groups Page</h1>
        <p className="text-lg text-gray-700">Manage your groups here!</p>
        {/* Add group listing, creation, and management UI */}
      </div>
    </div>
  );
};

export default GroupsPage;