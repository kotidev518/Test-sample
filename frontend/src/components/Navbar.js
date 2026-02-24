import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Home, BookOpen, BarChart3, LogOut, Search, User } from 'lucide-react';
import { motion } from 'framer-motion';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  const isActive = (path) => location.pathname === path;

  const navItems = [
    { path: '/dashboard', label: 'DASHBOARD', icon: Home },
    { path: '/courses', label: 'COURSES', icon: BookOpen },
    { path: '/analytics', label: 'ANALYTICS', icon: BarChart3 },
  ];

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-50 bg-white/60 backdrop-blur-xl border-b border-gray-100"
      data-testid="navbar"
    >
      <div className="container mx-auto px-4 lg:px-8">
        <div className="flex h-16 items-center justify-between relative">
          {/* Logo */}
          <Link
            to="/dashboard"
            className="flex items-center gap-2 group z-10"
            data-testid="logo-link"
          >
            <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
              <BookOpen className="h-5 w-5 fill-current" />
            </div>
            <span className="text-lg font-heading font-extrabold tracking-tight-more text-gray-900 uppercase">
              SkillFlow AI
            </span>
          </Link>

          {/* Nav Links - Centered */}
          <div className="hidden md:flex items-center gap-8 absolute left-1/2 -translate-x-1/2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="relative py-2 group"
              >
                <span className={`text-[11px] font-bold tracking-[0.1em] transition-colors ${isActive(item.path) ? 'text-gray-900' : 'text-gray-400 hover:text-gray-600'
                  }`}>
                  {item.label}
                </span>
                {isActive(item.path) && (
                  <motion.div
                    layoutId="navbar-underline"
                    className="absolute bottom-0 left-0 right-0 h-[3px] bg-primary rounded-full"
                  />
                )}
              </Link>
            ))}
          </div>

          {/* Right Section: Search & User */}
          <div className="flex items-center gap-3 z-10">
            {/* <Button variant="ghost" size="icon" className="text-gray-500 hover:text-gray-900">
              <Search className="h-5 w-5" />
            </Button> */}

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="relative h-9 w-9 rounded-full bg-blue-50 hover:bg-blue-100 transition-colors"
                  data-testid="user-menu-trigger"
                >
                  <Avatar className="h-9 w-9">
                    <AvatarFallback className="bg-blue-50 text-blue-600 font-bold text-xs">
                      {user?.name?.charAt(0).toUpperCase() || 'S'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{user?.name}</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user?.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => navigate('/analytics')}
                  data-testid="profile-menu-item"
                >
                  <User className="mr-2 h-4 w-4" />
                  Profile & Analytics
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="text-destructive"
                  data-testid="logout-menu-item"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </motion.nav>
  );
};
