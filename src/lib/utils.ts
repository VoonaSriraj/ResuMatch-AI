import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Enhanced API helper for backend calls
export const api = {
  baseUrl: (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000',
  
  // Updated headers method to ensure 'dev' token is used in development
  headers(): HeadersInit {
    // In development, always use 'dev' token if no token is found
    let token = '';
    if (typeof window !== 'undefined') {
      token = localStorage.getItem('token') || '';
      
      // In development, use 'dev' token if no token is set
      if (import.meta.env.DEV && !token) {
        token = 'dev';
        console.log('Using development token');
      }
      
      console.log('Current token:', token ? '***' : 'none');
    }
    
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  },

  async get(path: string): Promise<any> {
    try {
      const url = `${this.baseUrl}${path}`;
      const headers = this.headers();
      console.log(`GET ${url}`, { headers });
      
      const res = await fetch(url, { 
        headers,
        credentials: 'include'  // Important for sending cookies if using HTTP-only cookies
      });
      
      if (!res.ok) {
        const error = await this.handleErrorResponse(res);
        throw error;
      }
      return await res.json();
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  },

  async postJson(path: string, body: any): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify(body),
        credentials: 'include'  // Important for sending cookies if using HTTP-only cookies
      });

      if (!res.ok) {
        const error = await this.handleErrorResponse(res);
        throw error;
      }
      return await res.json();
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  },

  async postForm(path: string, form: FormData): Promise<any> {
    try {
      // Remove Content-Type header to let the browser set it with the correct boundary
      const { 'Content-Type': _, ...headers } = this.headers();
      
      const res = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: {
          ...headers,
          // Don't set Content-Type, let the browser set it with boundary
        },
        body: form,
        credentials: 'include'  // Important for sending cookies if using HTTP-only cookies
      });

      if (!res.ok) {
        const error = await this.handleErrorResponse(res);
        throw error;
      }
      return await res.json();
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  },

  async handleErrorResponse(res: Response): Promise<Error> {
    const errorText = await res.text();
    let errorMessage = errorText;
    
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorJson.message || errorText;
    } catch {
      // If not JSON, use the text as is
    }

    const error = new Error(errorMessage) as any;
    error.status = res.status;
    error.response = { data: { detail: errorMessage } };
    return error;
  },

  handleError(error: any): void {
    console.error('API Error:', {
      message: error.message,
      status: error.status,
      response: error.response,
      stack: error.stack
    });
    
    // Handle 401 Unauthorized errors
    if (error.status === 401) {
      console.log('Authentication error - current path:', window.location.pathname);
      // Only redirect if we're not already on the login page
      if (window.location.pathname !== '/login') {
        console.log('Redirecting to login...');
        // Store the current URL to redirect back after login
        localStorage.setItem('redirectAfterLogin', window.location.pathname);
        // Redirect to login page or show login modal
        window.location.href = '/login';
      }
    }
    
    // You can add more specific error handling here
  }
};
