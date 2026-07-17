import { useEffect, useState } from 'react';
import api from '../api/axios';
import toast from 'react-hot-toast';

function statusColor(status, lastFrameAt) {
  if (status === 'offline') return '#e5484d';
  if (status === 'pending') return '#f5a524';
  if (!lastFrameAt) return '#f5a524';
  const seconds = (Date.now() - new Date(lastFrameAt).getTime()) / 1000;
  if (seconds < 60) return '#3dd68c';
  if (seconds < 300) return '#f5a524';
  return '#e5484d';
}

export default function Cameras() {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', rtsp_url: '' });
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    api.get('/cameras/')
      .then(res => setCameras(res.data.results || res.data))
      .catch(() => toast.error('Failed to load cameras'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const addCamera = async (e) => {
    e.preventDefault();
    if (!form.name || !form.rtsp_url) {
      toast.error('Name and RTSP URL are required');
      return;
    }
    setSaving(true);
    try {
      await api.post('/cameras/', form);
      toast.success('Camera added');
      setShowModal(false);
      setForm({ name: '', rtsp_url: '' });
      load();
    } catch (err) {
      const msg = Object.values(err.response?.data || {})[0]?.[0] || 'Failed to add camera';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>Cameras</h2>
        <button onClick={() => setShowModal(true)}>+ Add Camera</button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : cameras.length === 0 ? (
        <p>No cameras yet. Add one to get started.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid #2a2b31' }}>
              <th style={{ padding: 8 }}>Status</th>
              <th style={{ padding: 8 }}>Name</th>
              <th style={{ padding: 8 }}>Last Frame</th>
              <th style={{ padding: 8 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {cameras.map(cam => (
              <tr key={cam.id} style={{ borderBottom: '1px solid #2a2b31' }}>
                <td style={{ padding: 8 }}>
                  <span style={{
                    display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
                    background: statusColor(cam.status, cam.last_frame_at),
                  }} />
                </td>
                <td style={{ padding: 8 }}>{cam.name}</td>
                <td style={{ padding: 8 }}>{cam.last_frame_at ? new Date(cam.last_frame_at).toLocaleString() : 'Never'}</td>
                <td style={{ padding: 8 }}>
                  <a href={`/cameras/${cam.id}`}>View</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <form onSubmit={addCamera} style={{
            background: '#1a1b20', padding: 24, borderRadius: 8, width: 320,
            display: 'flex', flexDirection: 'column', gap: 10,
          }}>
            <h3>Add Camera</h3>
            <input
              placeholder="Camera name"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
            />
            <input
              placeholder="rtsp://user:pass@ip:port/stream"
              value={form.rtsp_url}
              onChange={e => setForm({ ...form, rtsp_url: e.target.value })}
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button type="button" onClick={() => setShowModal(false)}>Cancel</button>
              <button disabled={saving}>{saving ? 'Adding...' : 'Add'}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}