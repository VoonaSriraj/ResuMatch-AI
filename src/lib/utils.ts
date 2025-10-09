import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Simple API helper for backend calls
export const api = {
  baseUrl: (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000',
  headers(): HeadersInit {
    const token = typeof window !== 'undefined' ? (localStorage.getItem('token') || '') : '';
    return {
      'Authorization': `Bearer ${token || 'dev'}`,
    };
  },
  async get(path: string): Promise<any> {
    const res = await fetch(`${this.baseUrl}${path}`, { headers: this.headers() });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async postJson(path: string, body: any): Promise<any> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...this.headers() },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async postForm(path: string, form: FormData): Promise<any> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.headers(),
      body: form,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
};
