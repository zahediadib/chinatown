import { Handshake } from 'lucide-react';
import { formatTileType, formatUsername } from '../lib/utils';

export default function PlayerPanel({ players, userId, phase, initiateDeal, gameState, isOpen }) {
  const canDeal = phase === 'trade';
  const myDeals = gameState?.active_deals || [];
  const iAmInDeal = myDeals.some(d => d.status !== 'cancelled' && (d.initiator === userId || d.target === userId));

  return (
    <div className={`side-panel ${isOpen ? 'mobile-open' : ''}`} data-testid="player-panel">
      <div className="section-label">Players</div>
      {players.map(player => {
        const isMe = player.id === userId;
        const tilesCount = typeof player.shop_tiles === 'number' ? player.shop_tiles : (player.shop_tiles?.length || 0);
        const inDeal = myDeals.some(d => d.status !== 'cancelled' && (d.initiator === player.id || d.target === player.id));
        const currentTurnPlayer = gameState?.player_order?.[gameState?.current_turn_index];
        const isCurrentTurn = phase === 'place_tiles' && currentTurnPlayer === player.id;
        const hasVotedEnd = gameState?.trade_votes?.includes(player.id);
        const isDonePlacing = gameState?.placement_done?.includes(player.id);

        return (
          <div
            key={player.id}
            className={`player-card ${isMe ? 'is-me' : ''} ${!player.connected ? 'disconnected' : ''}`}
            data-testid={`player-card-${player.id}`}
            style={isCurrentTurn ? { borderColor: player.color, boxShadow: `0 0 8px ${player.color}44` } : {}}
          >
            <div className="player-name">
              <div className="player-color-dot" style={{ background: player.color }} />
              <span>{formatUsername(player.username)} {isMe ? '(You)' : ''}</span>
              {!player.connected && <span style={{ fontSize: '0.65rem', color: '#ef4444' }}>OFFLINE</span>}
            </div>
            <div className="player-money" data-testid={`player-money-${player.id}`}>
              ${player.money?.toLocaleString()}
            </div>
            <div className="player-tiles-count">
              {tilesCount} tile{tilesCount !== 1 ? 's' : ''} in hand
              {hasVotedEnd && <span style={{ color: 'var(--jade-light)', marginLeft: '0.5rem' }}>Ready</span>}
              {isDonePlacing && <span style={{ color: 'var(--jade-light)', marginLeft: '0.5rem' }}>Done</span>}
              {isCurrentTurn && <span style={{ color: 'var(--gold)', marginLeft: '0.5rem' }}>Placing...</span>}
            </div>
            {!isMe && canDeal && (
              <button
                className="deal-btn"
                onClick={() => initiateDeal(player.id)}
                disabled={iAmInDeal || inDeal || !player.connected}
                data-testid={`deal-btn-${player.id}`}
              >
                <Handshake size={12} strokeWidth={1.5} style={{ display: 'inline', marginRight: 4 }} />
                Deal
              </button>
            )}
          </div>
        );
      })}

      {gameState?.tiles_drawn && Object.keys(gameState.tiles_drawn).length > 0 && phase === 'trade' && (
        <div className="tiles-drawn-section">
          <div className="section-label">Tiles Drawn This Round</div>
          {Object.entries(gameState.tiles_drawn).map(([pid, tiles], rowIndex) => (
            <div key={pid} className="tiles-drawn-row" style={{ animationDelay: `${rowIndex * 70}ms` }}>
              <span className="tiles-drawn-player" style={{ color: gameState.players[pid]?.color }}>
                {formatUsername(gameState.players[pid]?.username)}
              </span>
              <span className="tiles-drawn-separator">:</span>
              <span className="tiles-drawn-tiles">
                {tiles.map(t => (
                  <span key={`${pid}-${t.id}`} className="tile-name-chip">
                    {formatTileType(t.type)}
                  </span>
                ))}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
