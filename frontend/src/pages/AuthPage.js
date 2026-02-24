import React, { useState, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { GraduationCap, Eye, EyeOff, CheckCircle2, XCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { signInWithPopup, GoogleAuthProvider, browserLocalPersistence, browserSessionPersistence, setPersistence, sendPasswordResetEmail } from 'firebase/auth';
import { auth } from '@/firebase';
import { authService } from '@/services/authService';

// Password validation requirements
const validatePassword = (password) => {
  return {
    hasLowercase: /[a-z]/.test(password),
    hasUppercase: /[A-Z]/.test(password),
    hasNumber: /\d/.test(password),
    hasSpecial: /[@#$]/.test(password),
    hasMinLength: password.length >= 8,
  };
};

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
  const [emailError, setEmailError] = useState('');

  // Forgot password modal state
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetLoading, setResetLoading] = useState(false);

  const { register: authContextRegister, checkUser } = useAuth();
  const navigate = useNavigate();

  // Password validation
  const passwordValidation = useMemo(() => validatePassword(formData.password), [formData.password]);
  const isPasswordValid = Object.values(passwordValidation).every(Boolean);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    const provider = new GoogleAuthProvider();
    provider.setCustomParameters({ prompt: 'select_account' });

    try {
      // Set persistence based on remember me (for Google, we'll use local as default)
      await setPersistence(auth, browserLocalPersistence);

      const result = await signInWithPopup(auth, provider);
      const user = result.user;
      await authService.googleLogin(user.displayName, user.email);
      const userProfile = await checkUser();
      toast.success('Successfully signed in with Google!');
      if (userProfile?.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/dashboard');
      }
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
        // Set persistence based on "Remember me" checkbox
        const persistence = rememberMe ? browserLocalPersistence : browserSessionPersistence;
        await setPersistence(auth, persistence);

        // Firebase Login
        await import('firebase/auth').then(module =>
          module.signInWithEmailAndPassword(auth, formData.email, formData.password)
        );
        await authService.login();
        await checkUser();
        toast.success('Welcome back!');
      } else {
        // Pre-flight check: Validate email domain before Firebase creates the account
        await authService.validateEmail(formData.email);

        await authContextRegister(
          formData.email,
          formData.password,
          formData.name,
          formData.initial_level
        );
        toast.success('Account created successfully!');
      }
      const user = await checkUser();
      if (user?.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/dashboard');
      }
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
        if (errorMessage === 'enter a valid domain') {
          setEmailError('enter a valid domain');
          setLoading(false);
          return;
        }
      }
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle forgot password
  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!resetEmail) {
      toast.error('Please enter your email address');
      return;
    }

    setResetLoading(true);
    console.log("Starting password reset flow for:", resetEmail);

    try {
      // 1. Pre-flight check: Validate email domain via our backend
      console.log("Calling backend validation...");
      await authService.validateEmail(resetEmail);
      console.log("Backend validation successful.");

      // 2. If valid, trigger real Firebase Password Reset Email
      // Use the already imported sendPasswordResetEmail from line 14
      console.log("Triggering Firebase password reset email...");
      await sendPasswordResetEmail(auth, resetEmail);
      console.log("Firebase password reset email triggered successfully.");

      toast.success('Password reset email sent! Check your inbox.');
      setForgotPasswordOpen(false);
      setResetEmail('');
    } catch (error) {
      console.error("Password Reset Error:", error);
      let errorMessage = 'Failed to send reset email';

      if (error.response?.data?.detail) {
        // Backend validation error (e.g. "enter a valid domain")
        errorMessage = error.response.data.detail;
      } else if (error.code) {
        // Firebase specific errors
        switch (error.code) {
          case 'auth/user-not-found':
            errorMessage = 'No account found with this email.';
            break;
          case 'auth/invalid-email':
            errorMessage = 'Please enter a valid email address.';
            break;
          default:
            errorMessage = error.message;
        }
      }

      toast.error(errorMessage);
    } finally {
      console.log("Reset password flow completed.");
      setResetLoading(false);
    }
  };

  const handleChange = (e) => {
    if (e.target.name === 'email') setEmailError('');
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (

    <div className="relative min-h-screen w-full flex items-center justify-center bg-[#f6f7ff]">

      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-50 via-white to-pink-50" />


      {/* Card */}
      <div className="relative w-full max-w-sm z-10">

        <div className="bg-white rounded-[2.5rem] shadow-2xl p-6">


          {/* Header */}
          <div className="text-center mb-6">

            <div className="mx-auto mb-4 w-14 h-14 rounded-full
              bg-gradient-to-br from-purple-500 to-pink-500
              flex items-center justify-center">

              <GraduationCap className="text-white w-6 h-6" />

            </div>

            <h1 className="text-2xl font-bold">
              Step into Learn
            </h1>

            <p className="text-gray-500 text-sm">
              Your learning journey
            </p>

          </div>


          {/* Google */}
          <Button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full mb-4 bg-white border"
          >
            Continue with Google
          </Button>


          {/* Divider */}
          <div className="flex items-center my-4">

            <div className="flex-1 h-px bg-gray-200" />

            <span className="px-3 text-xs text-gray-400">
              OR
            </span>

            <div className="flex-1 h-px bg-gray-200" />

          </div>


          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">


            {/* Name */}
            {!isLogin && (

              <div>

                <Label>Full Name</Label>

                <Input
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                />

              </div>
            )}


            {/* Email */}
            <div>

              <Label>Email</Label>

              <Input
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
              />

            </div>


            {/* Password */}
            <div>

              <Label>Password</Label>

              <div className="relative">

                <Input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={handleChange}
                  required
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>

              </div>


              {/* Password Rules */}
              {!isLogin && formData.password && (

                <div className="mt-2 space-y-1">

                  <ValidationItem
                    valid={passwordValidation.hasLowercase}
                    text="Lowercase letter"
                  />

                  <ValidationItem
                    valid={passwordValidation.hasUppercase}
                    text="Uppercase letter"
                  />

                  <ValidationItem
                    valid={passwordValidation.hasNumber}
                    text="Number"
                  />

                  <ValidationItem
                    valid={passwordValidation.hasSpecial}
                    text="Special char (@#$)"
                  />

                  <ValidationItem
                    valid={passwordValidation.hasMinLength}
                    text="8+ characters"
                  />

                </div>
              )}

            </div>


            {/* Remember */}
            {isLogin && (

              <div className="flex justify-between text-sm">

                <div className="flex gap-2 items-center">

                  <Checkbox
                    checked={rememberMe}
                    onCheckedChange={setRememberMe}
                  />

                  Keep me signed in

                </div>

                <button
                  type="button"
                  onClick={() => {
                    setResetEmail(formData.email);
                    setForgotPasswordOpen(true);
                  }}
                  className="text-purple-600"
                >
                  Forgot?
                </button>

              </div>
            )}


            {/* Difficulty */}
            {!isLogin && (

              <div>

                <p className="text-sm mb-2">
                  Difficulty
                </p>

                <div className="flex gap-3">

                  {[
                    { name: "Easy", icon: "🌱" },
                    { name: "Medium", icon: "🔥" },
                    { name: "Hard", icon: "🚀" },
                  ].map((item) => (

                    <button
                      key={item.name}
                      type="button"
                      onClick={() =>
                        setFormData({
                          ...formData,
                          initial_level: item.name,
                        })
                      }
                      className={`flex-1 p-2 border rounded-xl
                        ${formData.initial_level === item.name
                          ? "bg-green-50 border-green-400"
                          : ""
                        }`}
                    >
                      <div>{item.icon}</div>
                      {item.name}
                    </button>

                  ))}

                </div>

              </div>
            )}


            {/* Submit */}
            <Button
              type="submit"
              disabled={loading || (!isLogin && !isPasswordValid)}
              className="w-full bg-gradient-to-r from-pink-500 to-purple-600"
            >
              {loading
                ? "Please wait..."
                : isLogin
                  ? "Sign In"
                  : "Create Account"}
            </Button>

          </form>


          {/* Footer */}
          <div className="text-center mt-5 text-sm">

            {isLogin ? "Don't have an account?" : "Already registered?"}

            <button
              onClick={() => setIsLogin(!isLogin)}
              className="ml-2 text-purple-600"
            >
              {isLogin ? "Sign Up" : "Sign In"}
            </button>

          </div>

        </div>

      </div>


      {/* Forgot Password Modal */}
      <Dialog
        open={forgotPasswordOpen}
        onOpenChange={setForgotPasswordOpen}
      >

        <DialogContent>

          <DialogHeader>

            <DialogTitle>
              Reset Password
            </DialogTitle>

            <DialogDescription>
              Enter your email
            </DialogDescription>

          </DialogHeader>

          <form
            onSubmit={handleForgotPassword}
            className="space-y-4"
          >

            <Input
              type="email"
              value={resetEmail}
              onChange={(e) => setResetEmail(e.target.value)}
              required
            />

            <Button
              type="submit"
              disabled={resetLoading}
              className="w-full"
            >
              {resetLoading ? "Sending..." : "Send Link"}
            </Button>

          </form>

        </DialogContent>

      </Dialog>

    </div>
  );
};



// ================= PASSWORD ITEM =================

const ValidationItem = ({ valid, text }) => {

  return (

    <div className="flex items-center gap-2 text-xs">

      {valid ? (
        <CheckCircle2 size={14} className="text-green-500" />
      ) : (
        <XCircle size={14} className="text-red-400" />
      )}

      <span
        className={
          valid ? "text-green-600" : "text-gray-400"
        }
      >
        {text}
      </span>

    </div>
  );
};

export default AuthPage;
