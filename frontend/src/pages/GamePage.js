import { useState, useMemo } from 'react';
import { useGame } from '../contexts/GameContext';
import { useAuth } from '../contexts/AuthContext';
import Board from '../components/Board';
import PlayerPanel from '../components/PlayerPanel';
import GameHeader from '../components/GameHeader';
import DealWindow from '../components/DealWindow';
import { formatTileType, formatUsername } from '../lib/utils';

export default function GamePage() {
  const { gameState, roomInfo, connected, error, dealRequest, activeDeal, userId,
    startGame, selectCards, endTrading, cancelEndTrading, placeTile, undoPlacement,
    donePlacing, continueGame, initiateDeal, respondDeal, updateOffer, confirmDeal, cancelDeal
  } = useGame();
  const { updateUser } = useAuth();

  const [selectedCards, setSelectedCards] = useState([]);
  const [selectedTile, setSelectedTile] = useState(null);
  const [dealSpaces, setDealSpaces] = useState([]);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);

  const isHost = roomInfo?.host === userId;
  const phase = gameState?.phase;
  const myPlayer = gameState?.players?.[userId];
  const isMyTurn = phase === 'place_tiles' && gameState?.player_order?.[gameState?.current_turn_index] === userId;
  const myDealtCards = gameState?.my_dealt_cards || [];
  const nKeep = gameState?.n_keep || 0;
  const negotiatingDeals = (gameState?.active_deals || [])
    .filter(d => d?.status === 'negotiating' && d?.detail)
    .map(d => d.detail);
  const iAmInDeal = negotiatingDeals.some(d => d.initiator === userId || d.target === userId);
  const cardSelectionMode = phase === 'select_cards' && !gameState?.my_selected;

  const handleCardToggle = (cardId) => {
    setSelectedCards(prev => {
      if (prev.includes(cardId)) return prev.filter(c => c !== cardId);
      if (prev.length >= nKeep) return prev;
      return [...prev, cardId];
    });
  };

  const handleCardSubmit = () => {
    if (selectedCards.length === nKeep) {
      selectCards(selectedCards);
      setSelectedCards([]);
    }
  };

  const handleTileSelect = (tile) => {
    setSelectedTile(prev => prev?.id === tile.id ? null : tile);
  };

  const handleBoardClick = (spaceId) => {
    if (phase === 'place_tiles' && isMyTurn && selectedTile) {
      placeTile(selectedTile.id, spaceId);
      setSelectedTile(null);
    }
  };

  const handleBoardUndo = (spaceId) => {
    undoPlacement(spaceId);
  };

  const handleLeave = () => {
    updateUser({ active_room: null });
    window.location.href = '/lobby';
  };

  // Waiting room
  if (!gameState && roomInfo) {
    return (
      <div className="waiting-room">
        <div className="waiting-card" data-testid="waiting-room">
          <h2>Waiting for Players</h2>
          <div className="room-code" data-testid="room-code">{roomInfo.room_id}</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
            Share this code with friends
          </p>
          <div className="waiting-players">
            {roomInfo.players?.map((p, i) => (
                <div key={p.user_id} className="waiting-player" data-testid={`waiting-player-${i}`}>
                  <div className="player-color-dot" style={{ background: ['#E53E3E','#3182CE','#38A169','#D69E2E','#805AD5'][i] }} />
                  <span>{formatUsername(p.username)} {p.user_id === roomInfo.host ? '(Host)' : ''}</span>
                </div>
              ))}
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1rem' }}>
            {roomInfo.players?.length || 0}/5 players {roomInfo.players?.length < 3 ? '(need at least 3)' : ''}
          </p>
          {isHost && (
            <button className="btn-gold" style={{ width: '100%', padding: '0.75rem' }} onClick={startGame} disabled={!roomInfo.players || roomInfo.players.length < 3} data-testid="start-game-btn">
              Start Game
            </button>
          )}
          {!isHost && <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Waiting for host to start...</p>}
          <button className="btn-outline" style={{ width: '100%', marginTop: '0.75rem' }} onClick={handleLeave} data-testid="leave-room-btn">Leave Room</button>
        </div>
        {!connected && <div className="connection-toast">Connecting...</div>}
      </div>
    );
  }

  if (!gameState) {
    return <div className="loading-screen">{connected ? 'Loading game...' : 'Connecting...'}</div>;
  }

  const sortedPlayers = gameState.player_order.map(pid => ({ id: pid, ...gameState.players[pid] }));
  const myTiles = Array.isArray(myPlayer?.shop_tiles) ? myPlayer.shop_tiles : [];

  return (
    <div className="game-container" data-testid="game-container">
      {error && <div className="error-toast" data-testid="error-toast">{error}</div>}

      <GameHeader
        gameState={gameState}
        phase={phase}
        isMyTurn={isMyTurn}
        endTrading={endTrading}
        cancelEndTrading={cancelEndTrading}
        donePlacing={donePlacing}
        continueGame={continueGame}
      />

      {/* Card selection banner — replaces the old popup */}
      {cardSelectionMode && (
        <div className="card-selection-bar" data-testid="card-selection-bar">
          <span className="card-sel-text">
            Click the highlighted spaces to claim them. Pick
            <strong> {nKeep} </strong>
            of {myDealtCards.length}.
            <span className="card-sel-count"> ({selectedCards.length}/{nKeep})</span>
          </span>
          <button
            className="btn-gold"
            onClick={handleCardSubmit}
            disabled={selectedCards.length !== nKeep}
            data-testid="confirm-cards-btn"
          >
            Confirm Selection
          </button>
        </div>
      )}

      {phase === 'select_cards' && gameState?.my_selected && (
        <div className="card-selection-bar waiting" data-testid="waiting-selection-bar">
          <span className="card-sel-text">
            Waiting for others... {gameState.players_selected?.length || 0}/{gameState.player_count} ready
          </span>
        </div>
      )}

      {/* Mobile toggle button for side panel */}
      <button
        className="mobile-panel-toggle"
        onClick={() => setSidePanelOpen(p => !p)}
        data-testid="toggle-panel-btn"
      >
        {sidePanelOpen ? 'Hide Players' : 'Players'}
      </button>

      <div className="game-main">
        <div className="board-area">
          <Board
            gameState={gameState}
            onTileClick={handleBoardClick}
            onTileUndo={handleBoardUndo}
            selectedTile={selectedTile}
            phase={phase}
            userId={userId}
            isMyTurn={isMyTurn}
            dealSpaces={dealSpaces}
            setDealSpaces={setDealSpaces}
            iAmInDeal={iAmInDeal}
            activeDeal={activeDeal}
            cardSelectionMode={cardSelectionMode}
            dealtCards={myDealtCards}
            selectedCards={selectedCards}
            onCardToggle={handleCardToggle}
          />
        </div>

        <PlayerPanel
          players={sortedPlayers}
          userId={userId}
          phase={phase}
          initiateDeal={initiateDeal}
          gameState={gameState}
          isOpen={sidePanelOpen}
        />
      </div>

      {/* Bottom panel — tiles in hand */}
      <div className="bottom-panel" data-testid="hand-panel">
        <span className="section-label" style={{ marginTop: 0, whiteSpace: 'nowrap' }}>Your Tiles:</span>
        {myTiles.map(tile => (
            <div
              key={tile.id}
              className={`hand-tile ${selectedTile?.id === tile.id ? 'selected' : ''}`}
              onClick={() => handleTileSelect(tile)}
              data-testid={`hand-tile-${tile.id}`}
            >
            <img src={`/tiles/${tile.type}.png`} alt={formatTileType(tile.type)} onError={(e) => { e.target.style.display = 'none'; }} />
            <div className="tile-label">{formatTileType(tile.type)}</div>
            </div>
        ))}
        {myTiles.length === 0 && <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No tiles in hand</span>}
      </div>

      {/* Income Overlay */}
      {phase === 'income' && (
        <div className="phase-overlay" data-testid="income-overlay">
          <div className="phase-modal">
            <h2>Income - Year {gameState.year}</h2>
            {gameState.last_income && Object.entries(gameState.last_income).map(([pid, data]) => (
              <div key={pid} style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <div className="player-color-dot" style={{ background: gameState.players[pid]?.color }} />
                  <span style={{ fontWeight: 600 }}>{formatUsername(gameState.players[pid]?.username)}</span>
                  <span className="font-mono" style={{ color: 'var(--jade-light)', marginLeft: 'auto' }}>+${data.total?.toLocaleString()}</span>
                </div>
                {data.businesses?.map((biz, i) => (
                  <div key={i} className="income-item">
                    <span>{formatTileType(biz.type)} (size {biz.size})</span>
                    <span className="amount">${biz.income?.toLocaleString()}</span>
                  </div>
                ))}
                {data.businesses?.length === 0 && <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', paddingLeft: '1.25rem' }}>No businesses</div>}
              </div>
            ))}
            <button className="btn-gold" style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }} onClick={continueGame} data-testid="continue-game-btn">
              {gameState.round >= 6 ? 'See Final Results' : 'Continue to Next Round'}
            </button>
          </div>
        </div>
      )}

      {/* Game Over */}
      {phase === 'game_over' && (
        <div className="phase-overlay" data-testid="game-over-overlay">
          <div className="phase-modal">
            <h2>Game Over - Final Scores</h2>
            <div className="scoreboard">
              {[...sortedPlayers].sort((a, b) => b.money - a.money).map((p, i) => (
                <div key={p.id} className={`score-row ${i === 0 ? 'winner' : ''}`} data-testid={`score-${p.id}`}>
                  <div className="score-name">
                    <div className="player-color-dot" style={{ background: p.color }} />
                    <span>{formatUsername(p.username)} {i === 0 ? ' - WINNER!' : ''}</span>
                  </div>
                  <div className="score-money">${p.money?.toLocaleString()}</div>
                </div>
              ))}
            </div>
            <button className="btn-gold" style={{ width: '100%', marginTop: '1rem' }} onClick={handleLeave} data-testid="back-to-lobby-btn">Back to Lobby</button>
          </div>
        </div>
      )}

      {/* Deal Request Popup */}
      {dealRequest && dealRequest.status === 'pending' && dealRequest.target === userId && (
        <div className="deal-request-popup" data-testid="deal-request-popup">
          <h3>Deal Request</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            <strong style={{ color: 'var(--gold)' }}>{formatUsername(dealRequest.initiator_name)}</strong> wants to trade with you
          </p>
          <div className="actions">
            <button className="btn-gold" onClick={() => respondDeal(dealRequest.id, true)} data-testid="accept-deal-btn">Accept</button>
            <button className="btn-cancel" onClick={() => respondDeal(dealRequest.id, false)} data-testid="decline-deal-btn">Decline</button>
          </div>
        </div>
      )}

      {/* Active Deal Window */}
      {negotiatingDeals.map((deal, index) => (
        <DealWindow
          key={deal.id}
          deal={deal}
          userId={userId}
          gameState={gameState}
          updateOffer={updateOffer}
          confirmDeal={confirmDeal}
          cancelDeal={cancelDeal}
          canInteract={deal.initiator === userId || deal.target === userId}
          windowIndex={index}
        />
      )}
    </div>
  );
}
