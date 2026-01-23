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
      // 1. Trigger Google Popup
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
      
      // 2. Call backend to sync user
      await authService.googleLogin(user.displayName, user.email);
      
      // 3. Force refresh user profile in context
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
        // Use authService.login which calls backend /auth/login after firebase auth
        // BUT wait, AuthContext.login does firebase login too.
        // Let's stick to the requirements: "Call Firebase signInWithEmailAndPassword -> On success -> Send user data to backend"
        
        // The existing AuthContext.login does: signInWithEmailAndPassword -> getProfile (which calls /auth/me).
        // The requirements ask to call POST /auth/login.
        // I will modify the flow slightly here or reuse context if it fits. 
        // To strictly follow "On success: Send user data to backend POST /auth/login", I should do it manually here or update context.
        // For minimal disruption, I will do it here manually similar to context but using the new service method.
        
        // 1. Firebase Login
        // We use the SDK directly to avoid the context's auto logic for a moment, 
        // but context listener is still active. 
        await import('firebase/auth').then(module => 
             module.signInWithEmailAndPassword(auth, formData.email, formData.password)
        );
        
        // 2. Backend Login (Update session/stats if needed)
        // Since we are using standard Firebase Auth, we verify the backend state
        const userProfile = await authService.login();
        
        // 3. Update context manualy to be sure 
        // (onAuthStateChanged might race, but checkUser handles it)
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
      // Handle Firebase Auth errors
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
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#F2F4F7]" data-testid="auth-page">
      {/* Background with soft gradient similar to reference */}
      <div className="absolute inset-0 bg-gradient-to-b from-white to-[#F2F4F7] z-0" />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-[400px] z-10"
      >
        <Card className="border-0 shadow-lg rounded-3xl bg-white overflow-hidden">
          <CardHeader className="text-center pb-2 pt-8">
            <div className="mx-auto mb-4 p-3 rounded-full bg-red-500/10 w-fit">
              <GraduationCap className="h-8 w-8 text-red-500" />
            </div>
            <CardTitle className="text-2xl font-bold text-gray-900">
              {isLogin ? 'Welcome back' : 'Create an Account'}
            </CardTitle>
            <CardDescription className="text-gray-500 text-sm mt-1">
              {isLogin
                ? 'Please enter your details to sign in.'
                : 'Start your personalized learning journey.'}
            </CardDescription>
          </CardHeader>

          <CardContent className="px-8 pb-8">
             {/* Social Login Section */}
             <div className="space-y-3 mb-6">
                <Button 
                  type="button" 
                  variant="outline" 
                  className="w-full h-11 bg-white border-gray-200 hover:bg-gray-50 text-gray-700 font-medium rounded-xl flex items-center justify-center gap-2 transition-all transform hover:scale-[1.01]"
                  onClick={handleGoogleSignIn}
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      fill="#4285F4"
                    />
                    <path
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      fill="#34A853"
                    />
                    <path
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      fill="#FBBC05"
                    />
                    <path
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      fill="#EA4335"
                    />
                  </svg>
                  {isLogin ? 'Sign in with Google' : 'Sign up with Google'}
                </Button>
             </div>

             <div className="relative flex items-center justify-center mb-6">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-4 text-gray-400 font-medium">OR</span>
                </div>
             </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div className="space-y-1.5">
                  <Label htmlFor="name" className="text-sm font-semibold text-gray-700">Full Name</Label>
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={handleChange}
                    required={!isLogin}
                    className="h-11 rounded-xl bg-gray-50 border-gray-200 focus:bg-white transition-colors"
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-sm font-semibold text-gray-700">E-mail Address</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Enter your email..."
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="h-11 rounded-xl bg-gray-50 border-gray-200 focus:bg-white transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-sm font-semibold text-gray-700">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="h-11 rounded-xl bg-gray-50 border-gray-200 focus:bg-white transition-colors pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {!isLogin && (
                <div className="space-y-3 pt-2">
                  <Label className="text-sm font-semibold text-gray-700">Starting Difficulty Level</Label>
                  <RadioGroup
                    value={formData.initial_level}
                    onValueChange={(value) =>
                      setFormData({ ...formData, initial_level: value })
                    }
                    className="flex flex-col gap-2"
                  >
                    {['Easy', 'Medium', 'Hard'].map((level) => (
                       <label 
                        key={level} 
                        htmlFor={level.toLowerCase()}
                        className={`flex items-center space-x-3 border rounded-xl p-3 cursor-pointer transition-all duration-200 ${
                          formData.initial_level === level 
                            ? 'bg-gray-900 border-gray-900 text-white shadow-md' 
                            : 'bg-white border-gray-200 hover:bg-gray-50 text-gray-700'
                        }`}
                       >
                        <RadioGroupItem value={level} id={level.toLowerCase()} className={`border-2 ${formData.initial_level === level ? 'border-white text-white' : 'border-gray-300'}`} />
                        <span className="font-medium text-sm flex-1">
                          {level}
                        </span>
                        {level === 'Easy' && <span className="text-xs opacity-70">Beginner</span>}
                        {level === 'Medium' && <span className="text-xs opacity-70">Intermediate</span>}
                        {level === 'Hard' && <span className="text-xs opacity-70">Advanced</span>}
                      </label>
                    ))}
                  </RadioGroup>
                </div>
              )}
                
              {isLogin && (
                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center space-x-2">
                        <Checkbox 
                            id="remember" 
                            checked={rememberMe} 
                            onCheckedChange={setRememberMe}
                            className="rounded-md border-gray-300 data-[state=checked]:bg-gray-900 data-[state=checked]:text-white"
                        />
                        <Label htmlFor="remember" className="text-sm font-medium text-gray-600 cursor-pointer">
                            Remember me
                        </Label>
                    </div>
                    <a href="#" className="text-sm font-medium text-gray-500 hover:text-gray-900 underline decoration-gray-300 underline-offset-4">
                        Forgot password?
                    </a>
                  </div>
              )}

              <Button
                type="submit"
                className="w-full h-11 bg-gray-900 hover:bg-black text-white rounded-xl font-medium mt-2 shadow-lg shadow-gray-900/10 transition-transform active:scale-[0.98]"
                disabled={loading}
              >
                {loading ? (
                    <div className="flex items-center gap-2">
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        <span>Please wait...</span>
                    </div>
                ) : (
                    isLogin ? 'Sign in' : 'Sign Up'
                )}
              </Button>
            </form>
          </CardContent>
          
          <CardFooter className="bg-gray-50/50 p-6 flex justify-center border-t border-gray-100">
             <div className="text-sm text-gray-500">
                 {isLogin ? "Don't have an account yet? " : "Already have an account? "}
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
