export default function GameHeader({ gameState, phase, isMyTurn, endTrading, cancelEndTrading, donePlacing, continueGame }) {
  const year = gameState?.year || 1965;
  const round = gameState?.round || 1;
  const tradeVotes = gameState?.trade_votes || [];
  const playerCount = gameState?.player_count || 0;
  const iVoted = tradeVotes.includes(gameState?.my_id);

  const phaseLabels = {
    select_cards: 'Selecting Building Cards',
    trade: 'Trading Phase',
    place_tiles: 'Placing Shop Tiles',
    income: 'Collecting Income',
    game_over: 'Game Over',
  };

  return (
    <div className="game-header" data-testid="game-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <div className="game-year" data-testid="game-year">{year}</div>
        <div className="game-round" data-testid="game-round">Round {round}/6</div>
        <div className="game-phase" data-testid="game-phase">{phaseLabels[phase] || phase}</div>
      </div>

      <div className="phase-actions">
        {phase === 'trade' && (
          <>
            <span className="phase-info-text">
              {tradeVotes.length}/{playerCount} ready to end trading
            </span>
            {!iVoted ? (
              <button className="btn-small gold" onClick={endTrading} data-testid="end-trading-btn">
                End Trading
              </button>
            ) : (
              <button className="btn-small red" onClick={cancelEndTrading} data-testid="cancel-end-trading-btn">
                Cancel (Voted)
              </button>
            )}
          </>
        )}

        {phase === 'place_tiles' && isMyTurn && (
          <button className="btn-small green" onClick={donePlacing} data-testid="done-placing-btn">
            Done Placing
          </button>
        )}

        {phase === 'place_tiles' && !isMyTurn && (
          <span className="phase-info-text">
            Waiting for {gameState?.players?.[gameState?.player_order?.[gameState?.current_turn_index]]?.username} to place...
          </span>
        )}
      </div>
    </div>
  );
}
