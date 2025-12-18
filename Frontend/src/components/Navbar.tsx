import { Link, useLocation } from 'react-router-dom';
import { Shield, Moon, Sun } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';

const Navbar = () => {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  const navLinks = [
    { path: '/', label: 'Dashboard' },
    { path: '/audit', label: 'Code Audit' },
    { path: '/qa', label: 'Q&A Chat' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="glass-panel sticky top-0 z-50 border-b border-gray-200 dark:border-slate-700">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text">
              Guardian AI
            </span>
          </Link>

          {/* Navigation Links and Theme Toggle - Pushed to Right */}
          <div className="flex items-center gap-2 ml-auto">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  isActive(link.path)
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                    : 'text-gray-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800'
                }`}
              >
                {link.label}
              </Link>
            ))}
            
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-slate-800 flex items-center justify-center hover:scale-110 transition-transform"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5 text-yellow-500" />
              ) : (
                <Moon className="w-5 h-5 text-slate-700" />
              )}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
