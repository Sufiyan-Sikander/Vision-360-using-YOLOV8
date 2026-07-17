import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(6, 'Min 6 characters'),
});

export const signupSchema = z.object({
  email: z.string().email('Invalid email'),
  password1: z.string().min(6, 'Min 6 characters'),
  password2: z.string().min(6, 'Min 6 characters'),
}).refine((data) => data.password1 === data.password2, {
  message: "Passwords don't match",
  path: ['password2'],
});

export const resetSchema = z.object({
  email: z.string().email('Invalid email'),
});