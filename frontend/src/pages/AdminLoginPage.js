import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ShieldAlert, Eye, EyeOff, Lock } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { signInWithEmailAndPassword, browserLocalPersistence, setPersistence } from 'firebase/auth';
import { auth } from '@/firebase';
import { authService } from '@/services/authService';

const AdminLoginPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const { checkUser } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Set local persistence for admin login
      await setPersistence(auth, browserLocalPersistence);
      
      // 1. Firebase Login
      await signInWithEmailAndPassword(auth, formData.email, formData.password);
      
      // 2. Refresh profile from backend to get role
      await authService.login();
      const userProfile = await checkUser();
      
      // 3. Verify Admin Role
      if (userProfile?.role === 'admin') {
        toast.success('Admin access granted. Welcome back!');
        navigate('/admin');
      } else {
        // Not an admin - sign out and show error
        await auth.signOut();
        toast.error('Access Denied: Admin privileges required.');
      }
    } catch (error) {
      console.error("Admin Login Error:", error);
      let errorMessage = 'Authentication failed';
      if (error.code) {
        switch (error.code) {
          case 'auth/user-not-found':
          case 'auth/wrong-password':
          case 'auth/invalid-credential':
            errorMessage = 'Invalid admin credentials.';
            break;
          case 'auth/too-many-requests':
            errorMessage = 'Too many attempts. Please try again later.';
            break;
          default:
            errorMessage = error.message;
        }
      }
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#0a0a0a]">
      {/* Background Decorative Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-red-900/10 blur-[120px] rounded-full" />
        <div className="absolute -bottom-[20%] -right-[10%] w-[50%] h-[50%] bg-blue-900/10 blur-[120px] rounded-full" />
      </div>
      
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="relative w-full max-w-[400px] z-10"
      >
        <Card className="border-0 shadow-2xl rounded-2xl bg-[#141414] text-white overflow-hidden border border-white/5">
          <CardHeader className="text-center pb-2 pt-8 px-8">
            <div className="mx-auto mb-4 p-3 rounded-2xl bg-gradient-to-br from-red-500 to-red-700 shadow-lg shadow-red-500/20 w-fit">
              <ShieldAlert className="h-8 w-8 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight">
              Admin Portal
            </CardTitle>
            <CardDescription className="text-gray-400 text-sm mt-2">
              Secure access for system administrators only
            </CardDescription>
          </CardHeader>

          <CardContent className="px-8 pb-10 pt-4">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Admin Email
                </Label>
                <div className="relative">
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="admin@platform.com"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="h-11 bg-white/5 border-white/10 text-white placeholder:text-gray-600 focus:border-red-500/50 focus:ring-red-500/20 rounded-xl pl-10"
                  />
                  <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500">
                    <Lock size={16} />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Secret Key
                </Label>
                <div className="relative">
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="h-11 bg-white/5 border-white/10 text-white placeholder:text-gray-600 focus:border-red-500/50 focus:ring-red-500/20 rounded-xl pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                className="w-full h-11 bg-white hover:bg-gray-200 text-black font-bold rounded-xl transition-all active:scale-[0.98] disabled:opacity-50 mt-4 shadow-lg shadow-white/5"
                disabled={loading}
              >
                {loading ? (
                    <div className="flex items-center gap-2">
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-black border-t-transparent" />
                        <span>Authenticating...</span>
                    </div>
                ) : (
                    'Authorize Access'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
        
        <div className="mt-8 text-center">
          <button 
            onClick={() => navigate('/auth')}
            className="text-gray-500 text-sm hover:text-gray-300 transition-colors"
          >
            ← Back to Student Login
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default AdminLoginPage;
