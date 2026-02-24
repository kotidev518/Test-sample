import React from 'react';
import { BookOpen, Share2, Globe } from 'lucide-react';

export const Footer = () => {
    return (
        <footer className="w-full border-t border-gray-100 bg-white/40 backdrop-blur-md py-8">
            <div className="container mx-auto px-4 lg:px-8">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                    {/* Logo Section */}
                    <div className="flex items-center gap-2 grayscale opacity-60">
                        <BookOpen className="h-5 w-5 fill-current" />
                        <span className="text-sm font-heading font-black tracking-tight uppercase">
                            SkillFlow
                        </span>
                    </div>

                    {/* Copyright Section */}
                    <div className="text-[10px] font-bold text-gray-400 tracking-[0.1em] uppercase text-center">
                        © 2024 SKILLFLOW AI LEARNING PLATFORM. ALL RIGHTS RESERVED.
                    </div>

                    {/* Icons Section */}
                    <div className="flex items-center gap-4 text-gray-400">
                        <Globe className="h-4 w-4 hover:text-gray-600 cursor-pointer transition-colors" />
                        <Share2 className="h-4 w-4 hover:text-gray-600 cursor-pointer transition-colors" />
                    </div>
                </div>
            </div>
        </footer>
    );
};
