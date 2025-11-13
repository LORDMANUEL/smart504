import * as React from 'react';

const AdminLayout = ({
  sidebar,
  children,
}: {
  sidebar: React.ReactNode;
  children: React.ReactNode;
}) => {
  return (
    <div className="flex h-screen bg-gray-100">
      <aside className="w-64 bg-gray-200 p-6 shadow-[5px_5px_10px_#bebebe,-5px_-5px_10px_#ffffff]">
        {sidebar}
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  );
};

export { AdminLayout };
