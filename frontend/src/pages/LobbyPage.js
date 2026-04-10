import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, Plus, RefreshCw } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function LobbyPage() {
  const { user, logout, updateUser } = useAuth();
  const navigate = useNavigate();
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [joinCode, setJoinCode] = useState('');

  const fetchRooms = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/rooms`, {
        headers: { Authorization: `Bearer ${user?.token}` },
      });
      setRooms(data);
    } catch { /* ignore */ }
  }, [user?.token]);

  useEffect(() => {
    if (user?.active_room) {
      navigate(`/game/${user.active_room}`);
      return;
    }
    fetchRooms();
    const interval = setInterval(fetchRooms, 5000);
    return () => clearInterval(interval);
  }, [user?.active_room, fetchRooms, navigate]);

  const authHeaders = { Authorization: `Bearer ${user?.token}` };

  const createRoom = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/rooms/create`, {}, { headers: authHeaders });
      updateUser({ active_room: data.room_id });
      navigate(`/game/${data.room_id}`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create room');
    } finally {
      setLoading(false);
    }
  };

  const joinRoom = async (roomId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/rooms/${roomId}/join`, {}, { headers: authHeaders });
      updateUser({ active_room: roomId });
      navigate(`/game/${roomId}`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to join room');
    } finally {
      setLoading(false);
    }
  };

  const handleJoinByCode = (e) => {
    e.preventDefault();
    if (joinCode.trim()) joinRoom(joinCode.trim());
  };

  return (
    <div className="lobby-page">
      <div className="lobby-header">
        <h1 className="lobby-title">Chinatown Lobby</h1>
        <div className="lobby-actions">
          <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {user?.username}
          </span>
          <button className="btn-outline" onClick={fetchRooms} data-testid="refresh-rooms">
            <RefreshCw size={14} strokeWidth={1.5} />
          </button>
          <button className="btn-outline" onClick={logout} data-testid="logout-btn">
            <LogOut size={14} strokeWidth={1.5} />
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <button className="btn-gold" onClick={createRoom} disabled={loading} data-testid="create-room-btn">
          <Plus size={14} strokeWidth={1.5} style={{ display: 'inline', marginRight: 4 }} />
          Create Room
        </button>
        <form onSubmit={handleJoinByCode} style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            className="auth-input"
            style={{ width: 160, marginBottom: 0 }}
            placeholder="Room code..."
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value)}
            data-testid="join-code-input"
          />
          <button className="btn-outline" type="submit" disabled={loading} data-testid="join-by-code-btn">
            Join
          </button>
        </form>
      </div>

      <div className="section-label">Available Rooms</div>
      {rooms.length === 0 ? (
        <div className="empty-rooms">No rooms available. Create one to start playing!</div>
      ) : (
        rooms.map((room) => (
          <div key={room.room_id} className="room-card" data-testid={`room-${room.room_id}`}>
            <div className="room-info">
              <h3>Room {room.room_id}</h3>
              <p>Host: {room.host_name} | Players: {room.players?.length || 0}/5</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className={`room-status ${room.status}`}>{room.status}</span>
              {room.status === 'waiting' && (
                <button
                  className="btn-gold"
                  onClick={() => joinRoom(room.room_id)}
                  disabled={loading}
                  data-testid={`join-room-${room.room_id}`}
                >
                  Join
                </button>
              )}
              {room.status === 'playing' && room.players?.some(p => p.user_id === user?.user_id) && (
                <button
                  className="btn-gold"
                  onClick={() => { updateUser({ active_room: room.room_id }); navigate(`/game/${room.room_id}`); }}
                  data-testid={`rejoin-room-${room.room_id}`}
                >
                  Rejoin
                </button>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
