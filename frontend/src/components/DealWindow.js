import { useState, useEffect, useCallback } from 'react';
import { X } from 'lucide-react';
import { formatTileType, formatUsername } from '../lib/utils';

const SPECTATOR_WINDOW_OFFSET = 24;
const BASE_WINDOW_RIGHT = 300;
const BASE_WINDOW_BOTTOM = 80;
const MAX_STACKED_WINDOWS = 4;

export default function DealWindow({ deal, userId, gameState, updateOffer, confirmDeal, cancelDeal, canInteract = true, windowIndex = 0 }) {
  const isInitiator = deal.initiator === userId;
  const isParticipant = isInitiator || deal.target === userId;
  const canEdit = canInteract && isParticipant;
  const myOffer = isInitiator ? deal.initiator_offer : deal.target_offer;
  const theirOffer = isInitiator ? deal.target_offer : deal.initiator_offer;
  const myConfirmed = isInitiator ? deal.initiator_confirmed : deal.target_confirmed;
  const theirConfirmed = isInitiator ? deal.target_confirmed : deal.initiator_confirmed;
  const otherName = formatUsername(isInitiator ? deal.target_name : deal.initiator_name);
  const initiatorName = formatUsername(deal.initiator_name);
  const targetName = formatUsername(deal.target_name);
  const initiatorOfferTiles = Array.isArray(deal.initiator_offer_tiles) ? deal.initiator_offer_tiles : [];
  const targetOfferTiles = Array.isArray(deal.target_offer_tiles) ? deal.target_offer_tiles : [];
  const theirOfferTiles = isInitiator ? targetOfferTiles : initiatorOfferTiles;

  const [localSpaces, setLocalSpaces] = useState(isParticipant ? (myOffer?.spaces || []) : []);
  const [localTiles, setLocalTiles] = useState(isParticipant ? (myOffer?.tiles || []) : []);
  const [localMoney, setLocalMoney] = useState(isParticipant ? (myOffer?.money || 0) : 0);

  useEffect(() => {
    if (!isParticipant) return;
    setLocalSpaces(myOffer?.spaces || []);
    setLocalTiles(myOffer?.tiles || []);
    setLocalMoney(myOffer?.money || 0);
  }, [isParticipant, myOffer?.spaces?.length, myOffer?.tiles?.length, myOffer?.money]);

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
    if (!canEdit) return;
    const next = localSpaces.includes(sid) ? localSpaces.filter(s => s !== sid) : [...localSpaces, sid];
    setLocalSpaces(next);
    sendOffer(next, localTiles, localMoney);
  };

  const toggleTile = (tid) => {
    if (!canEdit) return;
    const next = localTiles.includes(tid) ? localTiles.filter(t => t !== tid) : [...localTiles, tid];
    setLocalTiles(next);
    sendOffer(localSpaces, next, localMoney);
  };

  const handleMoneyChange = (e) => {
    if (!canEdit) return;
    const val = parseInt(e.target.value) || 0;
    setLocalMoney(val);
  };

  const handleMoneyBlur = () => {
    if (!canEdit) return;
    sendOffer(localSpaces, localTiles, localMoney);
  };

  const getOfferedTileLabel = (tileId, offeredTiles) => {
    const tile = offeredTiles.find(t => t.id === tileId);
    return formatTileType(tile?.type) || 'Unknown tile type';
  };

  const spectatorOffset = (windowIndex % (MAX_STACKED_WINDOWS + 1)) * SPECTATOR_WINDOW_OFFSET;
  const windowStyle = {
    right: `${BASE_WINDOW_RIGHT + spectatorOffset}px`,
    bottom: `${BASE_WINDOW_BOTTOM + spectatorOffset}px`,
  };

  return (
    <div className="deal-window" data-testid="deal-window" style={windowStyle}>
      <div className="deal-header">
        <span className="deal-title">
          {isParticipant ? `Trade with ${otherName}` : `${initiatorName} ↔ ${targetName}`}
        </span>
        {isParticipant && (
          <button onClick={() => cancelDeal(deal.id)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }} data-testid="cancel-deal-btn">
            <X size={18} strokeWidth={1.5} />
          </button>
        )}
      </div>

      <div className="deal-offers">
        {/* My Offer */}
        <div className="offer-column" data-testid="my-offer">
          <h4>{isParticipant ? 'Your Offer' : `${initiatorName}'s Offer`}</h4>

          <div className="section-label">Spaces</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '0.5rem' }}>
            {(isParticipant ? mySpaces : (deal.initiator_offer?.spaces || [])).map(sid => (
              <div
                key={sid}
                onClick={() => toggleSpace(sid)}
                style={{
                  width: 28, height: 24, borderRadius: 3, fontSize: '0.65rem',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: canEdit ? 'pointer' : 'default',
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
            {(isParticipant ? myTiles : initiatorOfferTiles).map(tile => (
              <div
                key={tile.id}
                onClick={() => toggleTile(tile.id)}
                style={{
                  padding: '2px 6px', borderRadius: 3, fontSize: '0.6rem', cursor: canEdit ? 'pointer' : 'default',
                  border: localTiles.includes(tile.id) ? '2px solid var(--gold)' : '1px solid var(--border-subtle)',
                  background: localTiles.includes(tile.id) ? 'rgba(245,158,11,0.2)' : 'var(--bg-surface)',
                  fontFamily: 'JetBrains Mono', color: 'var(--text-primary)',
                }}
                data-testid={`deal-tile-${tile.id}`}
              >
                {formatTileType(tile.type)}
              </div>
            ))}
          </div>

          {isParticipant ? (
            <>
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
                disabled={!canEdit}
              />
            </>
          ) : (
            (deal.initiator_offer?.money || 0) > 0 && (
              <>
                <div className="section-label">Money</div>
                <div className="offer-item">
                  <span className="font-mono" style={{ color: 'var(--jade-light)' }}>${deal.initiator_offer.money?.toLocaleString()}</span>
                </div>
              </>
            )
          )}
        </div>

        {/* Their Offer */}
        <div className="offer-column" data-testid="their-offer">
          <h4>{isParticipant ? `${otherName}'s Offer` : `${targetName}'s Offer`}</h4>
          {(isParticipant ? theirOffer?.spaces : deal.target_offer?.spaces)?.length > 0 && (
            <>
              <div className="section-label">Spaces</div>
              {(isParticipant ? theirOffer.spaces : deal.target_offer.spaces).map(sid => (
                <div key={sid} className="offer-item"><span>Space {sid}</span></div>
              ))}
            </>
          )}
          {(isParticipant ? theirOffer?.tiles : deal.target_offer?.tiles)?.length > 0 && (
            <>
              <div className="section-label">Tiles</div>
              {(isParticipant ? theirOffer.tiles : deal.target_offer.tiles).map(tid => (
                <div key={tid} className="offer-item"><span>{getOfferedTileLabel(tid, isParticipant ? theirOfferTiles : targetOfferTiles)}</span></div>
              ))}
            </>
          )}
          {((isParticipant ? theirOffer?.money : deal.target_offer?.money) || 0) > 0 && (
            <>
              <div className="section-label">Money</div>
              <div className="offer-item">
                <span className="font-mono" style={{ color: 'var(--jade-light)' }}>${(isParticipant ? theirOffer.money : deal.target_offer.money)?.toLocaleString()}</span>
              </div>
            </>
          )}
          {(!(isParticipant ? theirOffer?.spaces?.length : deal.target_offer?.spaces?.length) &&
            !(isParticipant ? theirOffer?.tiles?.length : deal.target_offer?.tiles?.length) &&
            !((isParticipant ? theirOffer?.money : deal.target_offer?.money) > 0)) && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '1rem' }}>No items offered yet</p>
          )}
          {isParticipant && theirConfirmed && (
            <div style={{ marginTop: '0.5rem', color: 'var(--jade-light)', fontSize: '0.75rem', fontWeight: 600 }}>
              Confirmed
            </div>
          )}
        </div>
      </div>

      {canEdit && (
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
      )}
    </div>
  );
}
