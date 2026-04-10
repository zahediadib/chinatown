import { useMemo } from 'react';
import { BOARD_TILES } from '../gameData';

export default function Board({ gameState, onTileClick, onTileUndo, selectedTile, phase, userId, isMyTurn, dealSpaces, setDealSpaces, iAmInDeal, activeDeal }) {
  const board = gameState?.board || {};

  const undoableSpaces = useMemo(() => {
    if (phase !== 'place_tiles') return new Set();
    const placements = gameState?.placements_this_round || [];
    return new Set(placements.filter(p => p.player_id === userId).map(p => p.space_id));
  }, [phase, gameState?.placements_this_round, userId]);

  const handleClick = (tileId) => {
    const space = board[String(tileId)];
    if (!space) return;

    if (phase === 'place_tiles' && isMyTurn) {
      if (undoableSpaces.has(tileId)) {
        onTileUndo(tileId);
        return;
      }
      if (selectedTile && space.owner === userId && !space.shop_tile) {
        onTileClick(tileId);
        return;
      }
    }

    if (phase === 'trade' && iAmInDeal && space.owner === userId) {
      setDealSpaces(prev => prev.includes(tileId) ? prev.filter(s => s !== tileId) : [...prev, tileId]);
    }
  };

  return (
    <div className="board-wrapper" data-testid="game-board">
      <img
        className="board-image"
        src="/BOARD.png"
        alt="Chinatown Board"
        onError={(e) => { e.target.style.background = '#44403c'; e.target.style.border = '1px solid var(--border-subtle)'; }}
        draggable={false}
      />
      {BOARD_TILES.map(tile => {
        const space = board[String(tile.id)];
        const isOwned = !!space?.owner;
        const isMine = space?.owner === userId;
        const hasShop = !!space?.shop_tile;
        const canUndo = undoableSpaces.has(tile.id);
        const isInDeal = dealSpaces?.includes(tile.id);
        const ownerColor = isOwned ? gameState?.players?.[space.owner]?.color : null;

        let bgColor = 'rgba(0,0,0,0.3)';
        if (isOwned) bgColor = ownerColor + '55';
        if (canUndo) bgColor = 'rgba(239,68,68,0.3)';
        if (isInDeal) bgColor = 'rgba(245,158,11,0.4)';

        return (
          <div
            key={tile.id}
            className={`board-tile-overlay ${isOwned ? 'owned' : ''} ${canUndo ? 'can-undo' : ''} ${isInDeal ? 'selected' : ''}`}
            style={{
              left: tile.x,
              top: tile.y,
              backgroundColor: bgColor,
              borderColor: isOwned ? ownerColor : 'rgba(255,255,255,0.15)',
            }}
            onClick={() => handleClick(tile.id)}
            title={`Space ${tile.id}${isOwned ? ` - ${gameState?.players?.[space.owner]?.username}` : ''}${hasShop ? ` (${space.shop_tile.type})` : ''}`}
            data-testid={`board-tile-${tile.id}`}
          >
            {hasShop && (
              <img
                className="tile-shop-img"
                src={`/tiles/${space.shop_tile.type}.png`}
                alt={space.shop_tile.type}
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            )}
            <span className="tile-number">{tile.id}</span>
          </div>
        );
      })}
    </div>
  );
}
