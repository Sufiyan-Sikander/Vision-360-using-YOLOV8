import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { signupSchema } from '../lib/validation';
import api from '../api/axios';
import toast from 'react-hot-toast';
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function Signup() {
  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(signupSchema) });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      await api.post('/auth/registration/', data);
      toast.success('Account created! Please log in.');
      navigate('/login');
    } catch (err) {
      const msg = Object.values(err.response?.data || {})[0]?.[0] || 'Signup failed';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <form onSubmit={handleSubmit(onSubmit)}>
        <h2>Sign Up</h2>
        <input placeholder="Email" {...register('email')} />
        {errors.email && <p className="error">{errors.email.message}</p>}
        <input type="password" placeholder="Password" {...register('password1')} />
        {errors.password1 && <p className="error">{errors.password1.message}</p>}
        <input type="password" placeholder="Confirm password" {...register('password2')} />
        {errors.password2 && <p className="error">{errors.password2.message}</p>}
        <button disabled={loading}>{loading ? 'Signing up...' : 'Sign Up'}</button>
        <p><Link to="/login">Already have an account?</Link></p>
      </form>
    </div>
  );
}