import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema } from '../lib/validation';
import api from '../api/axios';
import toast from 'react-hot-toast';
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function Login() {
  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(loginSchema) });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      const res = await api.post('/auth/login/', data);
      localStorage.setItem('access', res.data.access_token || res.data.access);
      toast.success('Logged in!');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <form onSubmit={handleSubmit(onSubmit)}>
        <h2>Log In</h2>
        <input placeholder="Email" {...register('email')} />
        {errors.email && <p className="error">{errors.email.message}</p>}
        <input type="password" placeholder="Password" {...register('password')} />
        {errors.password && <p className="error">{errors.password.message}</p>}
        <button disabled={loading}>{loading ? 'Logging in...' : 'Log In'}</button>
        <p><Link to="/reset-password">Forgot password?</Link> · <Link to="/signup">Sign up</Link></p>
      </form>
    </div>
  );
}