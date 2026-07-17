import { useEffect, useState } from 'react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function Settings() {
  const [profile, setProfile] = useState({ email: '', first_name: '', last_name: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [pwForm, setPwForm] = useState({ old_password: '', new_password1: '', new_password2: '' });
  const [pwSaving, setPwSaving] = useState(false);

  useEffect(() => {
    api.get('/auth/user/')
      .then(res => setProfile(res.data))
      .catch(() => toast.error('Failed to load profile'))
      .finally(() => setLoading(false));
  }, []);

  const saveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch('/auth/user/', profile);
      toast.success('Profile updated');
    } catch {
      toast.error('Update failed');
    } finally {
      setSaving(false);
    }
  };

  const changePassword = async (e) => {
    e.preventDefault();
    setPwSaving(true);
    try {
      await api.post('/auth/password/change/', pwForm);
      toast.success('Password changed');
      setPwForm({ old_password: '', new_password1: '', new_password2: '' });
    } catch (err) {
      const msg = Object.values(err.response?.data || {})[0]?.[0] || 'Password change failed';
      toast.error(msg);
    } finally {
      setPwSaving(false);
    }
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div style={{ maxWidth: 420 }}>
      <h2>Profile</h2>
      <form onSubmit={saveProfile} style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 32 }}>
        <input value={profile.email} disabled placeholder="Email" />
        <input
          value={profile.first_name || ''}
          onChange={e => setProfile({ ...profile, first_name: e.target.value })}
          placeholder="First name"
        />
        <input
          value={profile.last_name || ''}
          onChange={e => setProfile({ ...profile, last_name: e.target.value })}
          placeholder="Last name"
        />
        <button disabled={saving}>{saving ? 'Saving...' : 'Save Profile'}</button>
      </form>

      <h2>Change Password</h2>
      <form onSubmit={changePassword} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <input
          type="password"
          placeholder="Current password"
          value={pwForm.old_password}
          onChange={e => setPwForm({ ...pwForm, old_password: e.target.value })}
        />
        <input
          type="password"
          placeholder="New password"
          value={pwForm.new_password1}
          onChange={e => setPwForm({ ...pwForm, new_password1: e.target.value })}
        />
        <input
          type="password"
          placeholder="Confirm new password"
          value={pwForm.new_password2}
          onChange={e => setPwForm({ ...pwForm, new_password2: e.target.value })}
        />
        <button disabled={pwSaving}>{pwSaving ? 'Changing...' : 'Change Password'}</button>
      </form>
    </div>
  );
}