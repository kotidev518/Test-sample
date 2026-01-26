import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { GraduationCap, Eye, EyeOff } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { auth } from '@/firebase';
import { authService } from '@/services/authService';

const AuthPage = () => {
  const location = useLocation();
  const [isLogin, setIsLogin] = useState(location.state?.isLogin ?? true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    initial_level: 'Easy'
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  
  const { login: authContextLogin, register: authContextRegister, checkUser } = useAuth();
  const navigate = useNavigate();

  const handleGoogleSignIn = async () => {
    setLoading(true);
    const provider = new GoogleAuthProvider();
    provider.setCustomParameters({ prompt: 'select_account' });
    
    try {
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
      await authService.googleLogin(user.displayName, user.email);
      await checkUser();
      toast.success('Successfully signed in with Google!');
      navigate('/dashboard');
    } catch (error) {
      console.error("Google Sign-In Error:", error);
      let errorMessage = "Google sign-in failed. Please try again.";
      if (error.code === 'auth/popup-closed-by-user' || error.code === 'auth/cancelled-popup-request') {
        errorMessage = "Sign-in cancelled.";
      } else if (error.code === 'auth/popup-blocked') {
        errorMessage = "Popup blocked. Please allow popups for this site.";
      }
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        await import('firebase/auth').then(module => 
             module.signInWithEmailAndPassword(auth, formData.email, formData.password)
        );
        await authService.login();
        await checkUser();
        toast.success('Welcome back!');
      } else {
        await authContextRegister(
          formData.email,
          formData.password,
          formData.name,
          formData.initial_level
        );
        toast.success('Account created successfully!');
      }
      navigate('/dashboard');
    } catch (error) {
      let errorMessage = 'Authentication failed';
      if (error.code) {
        switch (error.code) {
          case 'auth/email-already-in-use':
            errorMessage = 'This email is already registered. Please sign in.';
            break;
          case 'auth/weak-password':
            errorMessage = 'Password should be at least 6 characters.';
            break;
          case 'auth/invalid-email':
            errorMessage = 'Please enter a valid email address.';
            break;
          case 'auth/user-not-found':
          case 'auth/wrong-password':
          case 'auth/invalid-credential':
            errorMessage = 'Invalid email or password.';
            break;
          case 'auth/too-many-requests':
            errorMessage = 'Too many attempts. Please try again later.';
            break;
          default:
            errorMessage = error.message || 'Authentication failed';
        }
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
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
    <div className="min-h-screen flex items-center justify-center p-2 bg-[#F2F4F7]" data-testid="auth-page">
      <div className="absolute inset-0 bg-gradient-to-b from-white to-[#F2F4F7] z-0" />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-[360px] z-10"
      >
        <Card className="border-0 shadow-lg rounded-2xl bg-white overflow-hidden">
          <CardHeader className="text-center pb-1 pt-4 px-5">
            <div className="mx-auto mb-2 p-2 rounded-full bg-red-500/10 w-fit">
              <GraduationCap className="h-6 w-6 text-red-500" />
            </div>
            <CardTitle className="text-xl font-bold text-gray-900">
              {isLogin ? 'Welcome back' : 'Create Account'}
            </CardTitle>
            <CardDescription className="text-gray-500 text-xs mt-0.5">
              {isLogin
                ? 'Enter your details to sign in'
                : 'Start your learning journey'}
            </CardDescription>
          </CardHeader>

          <CardContent className="px-5 pb-4">
             {/* Google Sign-In */}
             <Button 
               type="button" 
               variant="outline" 
               className="w-full h-9 bg-white border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg flex items-center justify-center gap-2 mb-3"
               onClick={handleGoogleSignIn}
             >
               <svg className="w-4 h-4" viewBox="0 0 24 24">
                 <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                 <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                 <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                 <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
               </svg>
               {isLogin ? 'Sign in with Google' : 'Sign up with Google'}
             </Button>

             {/* Divider */}
             <div className="relative flex items-center justify-center mb-3">
                <span className="w-full border-t border-gray-200" />
                <span className="absolute bg-white px-3 text-xs text-gray-400">OR</span>
             </div>

            <form onSubmit={handleSubmit} className="space-y-2.5">
              {/* Name (Signup only) */}
              {!isLogin && (
                <div className="space-y-1">
                  <Label htmlFor="name" className="text-xs font-semibold text-gray-700">Full Name</Label>
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={handleChange}
                    required={!isLogin}
                    className="h-9 text-sm rounded-lg bg-gray-50 border-gray-200"
                  />
                </div>
              )}

              {/* Email */}
              <div className="space-y-1">
                <Label htmlFor="email" className="text-xs font-semibold text-gray-700">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="h-9 text-sm rounded-lg bg-gray-50 border-gray-200"
                />
              </div>

              {/* Password */}
              <div className="space-y-1">
                <Label htmlFor="password" className="text-xs font-semibold text-gray-700">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="h-9 text-sm rounded-lg bg-gray-50 border-gray-200 pr-9"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {/* Difficulty Level (Signup only) - Horizontal compact */}
              {!isLogin && (
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-gray-700">Difficulty Level</Label>
                  <RadioGroup
                    value={formData.initial_level}
                    onValueChange={(value) => setFormData({ ...formData, initial_level: value })}
                    className="flex gap-2"
                  >
                    {['Easy', 'Medium', 'Hard'].map((level) => (
                       <label 
                        key={level} 
                        htmlFor={level.toLowerCase()}
                        className={`flex-1 flex items-center justify-center border rounded-lg py-2 px-2 cursor-pointer transition-all text-xs font-medium ${
                          formData.initial_level === level 
                            ? 'bg-gray-900 border-gray-900 text-white' 
                            : 'bg-white border-gray-200 hover:bg-gray-50 text-gray-700'
                        }`}
                       >
                        <RadioGroupItem value={level} id={level.toLowerCase()} className="sr-only" />
                        {level}
                      </label>
                    ))}
                  </RadioGroup>
                </div>
              )}
                
              {/* Remember me / Forgot (Login only) */}
              {isLogin && (
                  <div className="flex items-center justify-between pt-0.5">
                    <div className="flex items-center space-x-1.5">
                        <Checkbox 
                            id="remember" 
                            checked={rememberMe} 
                            onCheckedChange={setRememberMe}
                            className="h-3.5 w-3.5 rounded border-gray-300"
                        />
                        <Label htmlFor="remember" className="text-xs text-gray-600 cursor-pointer">
                            Remember me
                        </Label>
                    </div>
                    <a href="#" className="text-xs text-gray-500 hover:text-gray-900 underline">
                        Forgot password?
                    </a>
                  </div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full h-9 bg-gray-900 hover:bg-black text-white text-sm rounded-lg font-medium mt-1"
                disabled={loading}
              >
                {loading ? (
                    <div className="flex items-center gap-2">
                        <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        <span>Please wait...</span>
                    </div>
                ) : (
                    isLogin ? 'Sign in' : 'Sign Up'
                )}
              </Button>
            </form>
          </CardContent>
          
          {/* Footer */}
          <CardFooter className="bg-gray-50/50 py-3 px-5 flex justify-center border-t border-gray-100">
             <div className="text-xs text-gray-500">
                 {isLogin ? "Don't have an account? " : "Already have an account? "}
                 <button
                    onClick={() => setIsLogin(!isLogin)}
                    className="font-bold text-gray-900 hover:underline"
                 >
                    {isLogin ? "Sign Up" : "Sign In"}
                 </button>
             </div>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
};

export default AuthPage;
