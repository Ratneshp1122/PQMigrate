import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Shield, PlusCircle, LogOut, ShieldCheck } from 'lucide-react';
import clsx from 'clsx';

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Scans', path: '/scans', icon: Shield },
    { name: 'New Scan', path: '/scans/new', icon: PlusCircle },
  ];

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-sans">
      <aside className="w-64 border-r border-gray-800 bg-gray-900/50 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-800">
          <ShieldCheck className="w-6 h-6 text-blue-500 mr-2" />
          <span className="font-bold text-lg tracking-wide">PQMigrate</span>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive 
                    ? 'bg-blue-600/10 text-blue-400' 
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                )}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-800">
          <button 
            onClick={handleLogout}
            className="flex items-center w-full px-3 py-2 text-sm font-medium text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5 mr-3" />
            Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto relative">
        <Outlet />
      </main>
    </div>
  );
}
