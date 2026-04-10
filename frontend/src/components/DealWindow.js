import { useState, useEffect, useCallback } from 'react';
import { X } from 'lucide-react';

export default function DealWindow({ deal, userId, gameState, updateOffer, confirmDeal, cancelDeal }) {
  const isInitiator = deal.initiator === userId;
  const myOffer = isInitiator ? deal.initiator_offer : deal.target_offer;
  const theirOffer = isInitiator ? deal.target_offer : deal.initiator_offer;
  const myConfirmed = isInitiator ? deal.initiator_confirmed : deal.target_confirmed;
  const theirConfirmed = isInitiator ? deal.target_confirmed : deal.initiator_confirmed;
  const otherName = isInitiator ? deal.target_name : deal.initiator_name;

  const [localSpaces, setLocalSpaces] = useState(myOffer?.spaces || []);
  const [localTiles, setLocalTiles] = useState(myOffer?.tiles || []);
  const [localMoney, setLocalMoney] = useState(myOffer?.money || 0);

  useEffect(() => {
    setLocalSpaces(myOffer?.spaces || []);
    setLocalTiles(myOffer?.tiles || []);
    setLocalMoney(myOffer?.money || 0);
  }, [myOffer?.spaces?.length, myOffer?.tiles?.length, myOffer?.money]);

  const sendOffer = useCallback((spaces, tiles, money) => {
    updateOffer(deal.id, { spaces, tiles, money: Math.max(0, parseInt(money) || 0) });
  }, [deal.id, updateOffer]);

  const mySpaces = [];
  if (gameState?.board) {
    Object.entries(gameState.board).forEach(([sid, space]) => {
      if (space.owner === userId) mySpaces.push(parseInt(sid));
    });
  }
  mySpaces.sort((a, b) => a - b);

  const myTiles = Array.isArray(gameState?.players?.[userId]?.shop_tiles) ? gameState.players[userId].shop_tiles : [];

  const toggleSpace = (sid) => {
    const next = localSpaces.includes(sid) ? localSpaces.filter(s => s !== sid) : [...localSpaces, sid];
    setLocalSpaces(next);
    sendOffer(next, localTiles, localMoney);
  };

  const toggleTile = (tid) => {
    const next = localTiles.includes(tid) ? localTiles.filter(t => t !== tid) : [...localTiles, tid];
    setLocalTiles(next);
    sendOffer(localSpaces, next, localMoney);
  };

  const handleMoneyChange = (e) => {
    const val = parseInt(e.target.value) || 0;
    setLocalMoney(val);
  };

  const handleMoneyBlur = () => {
    sendOffer(localSpaces, localTiles, localMoney);
  };

  return (
    <div className="deal-window" data-testid="deal-window">
      <div className="deal-header">
        <span className="deal-title">Trade with {otherName}</span>
        <button onClick={() => cancelDeal(deal.id)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }} data-testid="cancel-deal-btn">
          <X size={18} strokeWidth={1.5} />
        </button>
      </div>

      <div className="deal-offers">
        {/* My Offer */}
        <div className="offer-column" data-testid="my-offer">
          <h4>Your Offer</h4>

          <div className="section-label">Spaces</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '0.5rem' }}>
            {mySpaces.map(sid => (
              <div
                key={sid}
                onClick={() => toggleSpace(sid)}
                style={{
                  width: 28, height: 24, borderRadius: 3, fontSize: '0.65rem',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
                  border: localSpaces.includes(sid) ? '2px solid var(--gold)' : '1px solid var(--border-subtle)',
                  background: localSpaces.includes(sid) ? 'rgba(245,158,11,0.2)' : 'var(--bg-surface)',
                  fontFamily: 'JetBrains Mono', color: 'var(--text-primary)',
                }}
                data-testid={`deal-space-${sid}`}
              >
                {sid}
              </div>
            ))}
          </div>

          <div className="section-label">Tiles</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '0.5rem' }}>
            {myTiles.map(tile => (
              <div
                key={tile.id}
                onClick={() => toggleTile(tile.id)}
                style={{
                  padding: '2px 6px', borderRadius: 3, fontSize: '0.6rem', cursor: 'pointer',
                  border: localTiles.includes(tile.id) ? '2px solid var(--gold)' : '1px solid var(--border-subtle)',
                  background: localTiles.includes(tile.id) ? 'rgba(245,158,11,0.2)' : 'var(--bg-surface)',
                  fontFamily: 'JetBrains Mono', color: 'var(--text-primary)',
                }}
                data-testid={`deal-tile-${tile.id}`}
              >
                {tile.type.slice(0, 4)}
              </div>
            ))}
          </div>

          <div className="section-label">Money</div>
          <input
            className="money-input"
            type="number"
            value={localMoney}
            onChange={handleMoneyChange}
            onBlur={handleMoneyBlur}
            min={0}
            max={gameState?.players?.[userId]?.money || 0}
            data-testid="deal-money-input"
          />
        </div>

        {/* Their Offer */}
        <div className="offer-column" data-testid="their-offer">
          <h4>{otherName}'s Offer</h4>
          {theirOffer?.spaces?.length > 0 && (
            <>
              <div className="section-label">Spaces</div>
              {theirOffer.spaces.map(sid => (
                <div key={sid} className="offer-item"><span>Space {sid}</span></div>
              ))}
            </>
          )}
          {theirOffer?.tiles?.length > 0 && (
            <>
              <div className="section-label">Tiles</div>
              {theirOffer.tiles.map(tid => (
                <div key={tid} className="offer-item"><span>Tile #{tid}</span></div>
              ))}
            </>
          )}
          {(theirOffer?.money || 0) > 0 && (
            <>
              <div className="section-label">Money</div>
              <div className="offer-item">
                <span className="font-mono" style={{ color: 'var(--jade-light)' }}>${theirOffer.money?.toLocaleString()}</span>
              </div>
            </>
          )}
          {(!theirOffer?.spaces?.length && !theirOffer?.tiles?.length && !(theirOffer?.money > 0)) && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '1rem' }}>No items offered yet</p>
          )}
          {theirConfirmed && (
            <div style={{ marginTop: '0.5rem', color: 'var(--jade-light)', fontSize: '0.75rem', fontWeight: 600 }}>
              Confirmed
            </div>
          )}
        </div>
      </div>

      <div className="deal-actions">
        <button
          className={`btn-confirm ${myConfirmed ? 'confirmed' : ''}`}
          onClick={() => confirmDeal(deal.id)}
          disabled={myConfirmed}
          data-testid="confirm-deal-btn"
        >
          {myConfirmed ? 'Confirmed' : 'Confirm Deal'}
        </button>
        <button className="btn-cancel" onClick={() => cancelDeal(deal.id)} data-testid="cancel-deal-action-btn">
          Cancel
        </button>
      </div>
    </div>
  );
}
