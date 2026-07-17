import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { resetSchema } from '../lib/validation';
import api from '../api/axios';
import toast from 'react-hot-toast';
import { useState } from 'react';

export default function ResetPassword() {
  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(resetSchema) });
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      await api.post('/auth/password/reset/', data);
      setSent(true);
      toast.success('Reset email sent (check console/logs in dev)');
    } catch {
      toast.error('Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  if (sent) return <div className="auth-container"><p>Check your email for reset instructions.</p></div>;

  return (
    <div className="auth-container">
      <form onSubmit={handleSubmit(onSubmit)}>
        <h2>Reset Password</h2>
        <input placeholder="Email" {...register('email')} />
        {errors.email && <p className="error">{errors.email.message}</p>}
        <button disabled={loading}>{loading ? 'Sending...' : 'Send Reset Link'}</button>
      </form>
    </div>
  );
}