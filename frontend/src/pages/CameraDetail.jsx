import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function CameraDetail() {
  const { id } = useParams();
  const [camera, setCamera] = useState(null);
  const [tab, setTab] = useState('overview');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [detections, setDetections] = useState([]);
  const [detectionsLoading, setDetectionsLoading] = useState(false);
  const [models, setModels] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const load = () => {
    api.get(`/cameras/${id}/`)
      .then(res => setCamera(res.data))
      .catch(() => toast.error('Failed to load camera'));
  };

  useEffect(() => { load(); }, [id]);

  useEffect(() => {
    if (tab === 'detections') {
      setDetectionsLoading(true);
      api.get(`/detections/?camera=${id}`)
        .then(res => setDetections(res.data.results || res.data))
        .catch(() => toast.error('Failed to load detections'))
        .finally(() => setDetectionsLoading(false));
    }
  }, [tab, id]);

  useEffect(() => {
    if (tab === 'models') {
      api.get('/models/').then(res => setModels(res.data.results || res.data)).catch(err => console.error('models err', err.response?.data));
      api.get(`/assignments/?camera=${id}`).then(res => setAssignments(res.data.results || res.data)).catch(err => console.error('assign err', err.response?.data));
    }
  }, [tab, id]);

  const toggleModel = async (modelId) => {
    const existing = assignments.find(a => a.model === modelId);
    try {
      if (existing) {
        await api.patch(`/assignments/${existing.id}/`, { enabled: !existing.enabled });
      } else {
        await api.post('/assignments/', { camera: id, model: modelId, enabled: true });
      }
      const res = await api.get(`/assignments/?camera=${id}`);
      setAssignments(res.data.results || res.data);
    } catch {
      toast.error('Failed to update assignment');
    }
  };



  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.post(`/cameras/${id}/test_connection/`);
      setTestResult(res.data);
      load();
    } catch (err) {
      setTestResult({ success: false, error: err.response?.data?.error || 'Connection failed' });
    } finally {
      setTesting(false);
    }
  };

  if (!camera) return <p>Loading...</p>;

  return (
    <div>
      <p><Link to="/cameras">← Back to Cameras</Link></p>
      <h2>{camera.name}</h2>
      <p style={{ color: '#888' }}>{camera.rtsp_url}</p>
      <p>Status: <strong>{camera.status}</strong></p>

      <div style={{ display: 'flex', gap: 16, marginBottom: 16, borderBottom: '1px solid #2a2b31' }}>
        <button onClick={() => setTab('overview')} style={{ fontWeight: tab === 'overview' ? 'bold' : 'normal' }}>Overview</button>
        <button onClick={() => setTab('detections')} style={{ fontWeight: tab === 'detections' ? 'bold' : 'normal' }}>Detections</button>
        <button onClick={() => setTab('models')} style={{ fontWeight: tab === 'models' ? 'bold' : 'normal' }}>Models</button>     
      </div>

      {tab === 'overview' && (
        <div>
          <button onClick={testConnection} disabled={testing}>
            {testing ? 'Testing...' : 'Test Connection'}
          </button>

          {testResult?.success && (
            <div style={{ marginTop: 12 }}>
              <img src={testResult.frame} alt="preview" style={{ maxWidth: 400, borderRadius: 4 }} />
              <p style={{ color: '#3dd68c' }}>Connected successfully</p>
            </div>
          )}
          {testResult && !testResult.success && (
            <p style={{ color: '#e5484d', marginTop: 12 }}>{testResult.error}</p>
          )}

          <p style={{ marginTop: 16 }}>Last frame: {camera.last_frame_at ? new Date(camera.last_frame_at).toLocaleString() : 'Never'}</p>
        </div>
      )}

      {tab === 'models' && (
        <div>
          {models.map(m => {
            const assignment = assignments.find(a => a.model === m.id);
            return (
              <label key={m.id} style={{ display: 'block', marginBottom: 8 }}>
                <input
                  type="checkbox"
                  checked={assignment?.enabled || false}
                  onChange={() => toggleModel(m.id)}
                />
                {' '}{m.name} (v{m.version})
              </label>
            );
    })}
  </div>
)}

 
      {tab === 'detections' && (
        <div>
          {detectionsLoading ? (
            <p>Loading...</p>
          ) : detections.length === 0 ? (
            <p>No detections yet for this camera.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid #2a2b31' }}>
                  <th style={{ padding: 8 }}>Time</th>
                  <th style={{ padding: 8 }}>Event</th>
                  <th style={{ padding: 8 }}>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {detections.map(d => (
                  <tr key={d.id} style={{ borderBottom: '1px solid #2a2b31' }}>
                    <td style={{ padding: 8 }}>{new Date(d.timestamp).toLocaleString()}</td>
                    <td style={{ padding: 8 }}>{d.event_type}</td>
                    <td style={{ padding: 8 }}>{(d.confidence * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

