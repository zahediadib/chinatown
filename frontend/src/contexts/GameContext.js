import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const GameContext = createContext(null);

export function GameProvider({ roomId, children }) {
  const { user } = useAuth();
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [gameState, setGameState] = useState(null);
  const [roomInfo, setRoomInfo] = useState(null);
  const [dealRequest, setDealRequest] = useState(null);
  const [activeDeal, setActiveDeal] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user?.token || !roomId) return;

    const s = io(BACKEND_URL, {
      path: '/api/socket.io',
      auth: { token: user.token },
      transports: ['polling', 'websocket'],
      reconnection: true,
      reconnectionAttempts: 50,
      reconnectionDelay: 1000,
    });
    socketRef.current = s;

    s.on('connect', () => {
      setConnected(true);
      s.emit('join_room', { room_id: roomId });
    });
    s.on('disconnect', () => setConnected(false));
    s.on('reconnect', () => {
      s.emit('join_room', { room_id: roomId });
    });

    s.on('game_state', (data) => {
      setGameState({ ...data });
    });
    s.on('room_info', (data) => {
      setRoomInfo({ ...data });
    });
    s.on('deal_request', (data) => {
      setDealRequest({ ...data });
    });
    s.on('deal_update', (data) => {
      setActiveDeal({ ...data });
      setDealRequest(null);
    });
    s.on('deal_completed', () => {
      setActiveDeal(null);
      setDealRequest(null);
    });
    s.on('deal_cancelled', () => {
      setActiveDeal(null);
      setDealRequest(null);
    });
    s.on('error', (data) => {
      setError(data?.message || 'Unknown error');
      setTimeout(() => setError(null), 4000);
    });

    return () => {
      s.disconnect();
      socketRef.current = null;
    };
  }, [roomId, user?.token]);

  const emit = useCallback((event, data = {}) => {
    socketRef.current?.emit(event, { room_id: roomId, ...data });
  }, [roomId]);

  const value = {
    connected,
    gameState,
    roomInfo,
    dealRequest,
    activeDeal,
    error,
    userId: user?.user_id,
    emit,
    startGame: () => emit('start_game'),
    selectCards: (cards) => emit('select_cards', { cards }),
    endTrading: () => emit('end_trading'),
    cancelEndTrading: () => emit('cancel_end_trading'),
    placeTile: (tileId, spaceId) => emit('place_tile', { tile_id: tileId, space_id: spaceId }),
    undoPlacement: (spaceId) => emit('undo_placement', { space_id: spaceId }),
    donePlacing: () => emit('done_placing'),
    continueGame: () => emit('continue_game'),
    initiateDeal: (targetId) => emit('initiate_deal', { target_id: targetId }),
    respondDeal: (dealId, accept) => emit('respond_deal', { deal_id: dealId, accept }),
    updateOffer: (dealId, offer) => emit('update_offer', { deal_id: dealId, offer }),
    confirmDeal: (dealId) => emit('confirm_deal', { deal_id: dealId }),
    cancelDeal: (dealId) => emit('cancel_deal', { deal_id: dealId }),
  };

  return (
    <GameContext.Provider value={value}>
      {children}
    </GameContext.Provider>
  );
}

export function useGame() {
  const ctx = useContext(GameContext);
  if (!ctx) throw new Error('useGame must be inside GameProvider');
  return ctx;
}
