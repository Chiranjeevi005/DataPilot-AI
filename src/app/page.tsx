"use client";

import NavBar from "@/components/NavBar";
import Sidebar from "@/components/Sidebar";
import Hero from "@/components/Hero";
import { useSidebarStore } from "@/lib/store";

import { cn } from '@/lib/utils';

export default function Home() {
  const isOpen = useSidebarStore((state) => state.isOpen);

  return (
    <div className="flex min-h-screen pt-16 relative">
      <NavBar />
      <Sidebar />
      <main className={cn("flex-1 p-6 lg:p-10 flex flex-col min-h-[calc(100vh-64px)] transition-all duration-300", isOpen ? "md:ml-20 lg:ml-72" : "ml-0")}>
        <Hero />

        <footer className="mt-auto pt-10 flex flex-col md:flex-row justify-between items-center text-sm text-slate-400 gap-4">
          <div>
            © DataPilot AI — Automated insights from your data
          </div>
          <div className="flex gap-4">
            <a href="#" className="hover:text-slate-600 transition-colors">Docs</a>
            <span>•</span>
            <a href="#" className="hover:text-slate-600 transition-colors">Privacy</a>
            <span>•</span>
            <a href="#" className="hover:text-slate-600 transition-colors">Contact</a>
          </div>
        </footer>
      </main>
    </div>
  );
}
