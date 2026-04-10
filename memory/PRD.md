# Chinatown Board Game - PRD

## Original Problem Statement
Build a full-stack multiplayer Chinatown board game (3-5 players, 6 rounds). Players trade building spaces, shop tiles, and money to build businesses in 1960s NYC Chinatown. The richest player after 6 rounds wins.

## Architecture
- **Backend**: FastAPI + python-socketio + MongoDB
- **Frontend**: React + socket.io-client
- **Real-time**: Socket.IO at /api/socket.io path
- **Game State**: In-memory (Python dict) with MongoDB for user/room persistence

## User Personas
- Casual board gamers playing with friends online
- 3-5 players per game session, games last 1-2 hours

## Core Requirements (Static)
- Room-based multiplayer with sign up/login
- 85-tile board in 6 isolated sections with correct adjacency
- 12 shop types with varying max sizes (3-6)
- 6-round game flow: Deal Cards → Draw Tiles → Trade → Place Tiles → Income
- Trading system with independent deal windows
- Income calculation based on business size and completeness
- Reconnection support for disconnected players

## What's Been Implemented (Feb 2026)
- Full auth system (JWT, register/login)
- Room system (create/join/leave/list)
- Socket.IO real-time communication
- Complete game engine with all 6 phases
- Card dealing and selection with proper distribution tables
- Shop tile drawing (3 per player per round)
- Trading system (initiate, negotiate, confirm, cancel deals)
- Tile placement with undo (within same round)
- Income calculation with business detection (BFS)
- Business splitting for oversized groups
- Turn-based placement, simultaneous trading
- Game over scoring and winner determination
- Board UI with 85 tile overlays on BOARD.png
- Player panel with balances, tile inventory, deal buttons
- Phase-specific overlays (card selection, income, game over)

## P0 Features Remaining
- None (core game loop complete)

## P1 Features Remaining
- Drag-and-drop for deal window items
- Better tile images (user to provide real assets)
- Real BOARD.png background

## P2 Features Remaining
- Game replay/history
- Spectator mode
- Mobile-responsive layout
- Sound effects
- Chat system

## Next Tasks
1. User provides real BOARD.png and 12 tile images
2. Polish deal window UX (drag-and-drop)
3. Add game reconnection persistence to MongoDB
4. Mobile responsive layout
