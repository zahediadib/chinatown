from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import socketio
import os
import logging
import bcrypt
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from game_logic import GameEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', ping_timeout=60, ping_interval=25)
fastapi_app = FastAPI()
api = APIRouter(prefix="/api")

active_games = {}
sid_to_user = {}
user_to_sid = {}

JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback-secret-key')


def hash_password(pwd):
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(pwd, hashed):
    return bcrypt.checkpw(pwd.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id, username):
    return jwt.encode(
        {'sub': user_id, 'username': username, 'exp': datetime.now(timezone.utc) + timedelta(days=7)},
        JWT_SECRET, algorithm='HS256'
    )

def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return None

async def get_user_from_request(request):
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = decode_token(auth[7:])
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')
    return payload


class AuthInput(BaseModel):
    username: str
    password: str


@api.post("/auth/register")
async def register(data: AuthInput):
    if len(data.username) < 2:
        raise HTTPException(status_code=400, detail='Username must be at least 2 characters')
    existing = await db.users.find_one({'username': data.username})
    if existing:
        raise HTTPException(status_code=400, detail='Username already taken')
    user_id = str(uuid.uuid4())
    await db.users.insert_one({
        'user_id': user_id, 'username': data.username,
        'password_hash': hash_password(data.password),
        'created_at': datetime.now(timezone.utc).isoformat(),
    })
    token = create_token(user_id, data.username)
    return {'user_id': user_id, 'username': data.username, 'token': token}


@api.post("/auth/login")
async def login(data: AuthInput):
    user = await db.users.find_one({'username': data.username}, {'_id': 0})
    if not user or not verify_password(data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = create_token(user['user_id'], user['username'])
    return {'user_id': user['user_id'], 'username': user['username'], 'token': token}


@api.get("/auth/me")
async def me(request: Request):
    payload = await get_user_from_request(request)
    user = await db.users.find_one({'user_id': payload['sub']}, {'_id': 0, 'password_hash': 0})
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    room = await db.rooms.find_one(
        {'players.user_id': payload['sub'], 'status': {'$in': ['waiting', 'playing']}}, {'_id': 0}
    )
    return {
        'user_id': user['user_id'], 'username': user['username'],
        'active_room': room['room_id'] if room else None,
    }


@api.post("/rooms/create")
async def create_room(request: Request):
    payload = await get_user_from_request(request)
    existing = await db.rooms.find_one({'players.user_id': payload['sub'], 'status': {'$in': ['waiting', 'playing']}})
    if existing:
        raise HTTPException(status_code=400, detail='Already in a room')
    room_id = str(uuid.uuid4())[:8]
    room = {
        'room_id': room_id, 'host': payload['sub'], 'host_name': payload['username'],
        'status': 'waiting',
        'players': [{'user_id': payload['sub'], 'username': payload['username']}],
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    await db.rooms.insert_one(room)
    room.pop('_id', None)
    return room


@api.get("/rooms")
async def list_rooms(request: Request):
    await get_user_from_request(request)
    rooms = await db.rooms.find({'status': {'$in': ['waiting', 'playing']}}, {'_id': 0}).sort('created_at', -1).to_list(50)
    return rooms


@api.post("/rooms/{room_id}/join")
async def join_room(room_id: str, request: Request):
    payload = await get_user_from_request(request)
    room = await db.rooms.find_one({'room_id': room_id}, {'_id': 0})
    if not room:
        raise HTTPException(status_code=404, detail='Room not found')
    if room['status'] != 'waiting':
        if any(p['user_id'] == payload['sub'] for p in room['players']):
            return room
        raise HTTPException(status_code=400, detail='Game already started')
    if len(room['players']) >= 5:
        raise HTTPException(status_code=400, detail='Room is full')
    if any(p['user_id'] == payload['sub'] for p in room['players']):
        return room
    existing = await db.rooms.find_one({'players.user_id': payload['sub'], 'status': {'$in': ['waiting', 'playing']}, 'room_id': {'$ne': room_id}})
    if existing:
        raise HTTPException(status_code=400, detail='Already in another room')
    await db.rooms.update_one(
        {'room_id': room_id},
        {'$push': {'players': {'user_id': payload['sub'], 'username': payload['username']}}}
    )
    room = await db.rooms.find_one({'room_id': room_id}, {'_id': 0})
    return room


@api.post("/rooms/{room_id}/leave")
async def leave_room(room_id: str, request: Request):
    payload = await get_user_from_request(request)
    room = await db.rooms.find_one({'room_id': room_id})
    if not room:
        raise HTTPException(status_code=404, detail='Room not found')
    if room['status'] != 'waiting':
        raise HTTPException(status_code=400, detail='Cannot leave during game')
    await db.rooms.update_one({'room_id': room_id}, {'$pull': {'players': {'user_id': payload['sub']}}})
    if room['host'] == payload['sub']:
        updated = await db.rooms.find_one({'room_id': room_id})
        if updated and len(updated.get('players', [])) > 0:
            nh = updated['players'][0]
            await db.rooms.update_one({'room_id': room_id}, {'$set': {'host': nh['user_id'], 'host_name': nh['username']}})
        else:
            await db.rooms.delete_one({'room_id': room_id})
    return {'ok': True}


# --- Socket.IO Events ---

@sio.event
async def connect(sid, environ, auth):
    if not auth or 'token' not in auth:
        raise socketio.exceptions.ConnectionRefusedError('No token')
    payload = decode_token(auth['token'])
    if not payload:
        raise socketio.exceptions.ConnectionRefusedError('Invalid token')
    user_id = payload['sub']
    username = payload['username']
    old_sid = user_to_sid.get(user_id)
    if old_sid and old_sid != sid:
        old_session = sid_to_user.pop(old_sid, None)
        if old_session:
            try:
                await sio.disconnect(old_sid)
            except Exception:
                pass
    sid_to_user[sid] = {'user_id': user_id, 'username': username, 'room_id': None}
    user_to_sid[user_id] = sid
    logger.info(f"Connected: {username}")


@sio.event
async def disconnect(sid):
    session = sid_to_user.pop(sid, None)
    if not session:
        return
    user_id = session['user_id']
    if user_to_sid.get(user_id) == sid:
        user_to_sid.pop(user_id, None)
    room_id = session.get('room_id')
    if room_id and room_id in active_games:
        game = active_games[room_id]
        if user_id in game['players']:
            game['players'][user_id]['connected'] = False
            await broadcast_game_state(room_id)
    logger.info(f"Disconnected: {session['username']}")


@sio.on('join_room')
async def handle_join_room(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = data.get('room_id')
    if not room_id:
        return
    session['room_id'] = room_id
    await sio.enter_room(sid, room_id)
    if room_id in active_games:
        game = active_games[room_id]
        if session['user_id'] in game['players']:
            game['players'][session['user_id']]['connected'] = True
            await broadcast_game_state(room_id)
            return
    room = await db.rooms.find_one({'room_id': room_id}, {'_id': 0})
    if room:
        await sio.emit('room_info', room, room=room_id)


@sio.on('start_game')
async def handle_start_game(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = data.get('room_id') or session.get('room_id')
    room = await db.rooms.find_one({'room_id': room_id}, {'_id': 0})
    if not room:
        await sio.emit('error', {'message': 'Room not found'}, room=sid)
        return
    if room['host'] != session['user_id']:
        await sio.emit('error', {'message': 'Only host can start'}, room=sid)
        return
    pc = len(room['players'])
    if pc < 3 or pc > 5:
        await sio.emit('error', {'message': f'Need 3-5 players, currently {pc}'}, room=sid)
        return
    players_info = [(p['user_id'], p['username']) for p in room['players']]
    game = GameEngine.create_game(room_id, players_info)
    active_games[room_id] = game
    await db.rooms.update_one({'room_id': room_id}, {'$set': {'status': 'playing'}})
    GameEngine.deal_building_cards(game)
    await broadcast_game_state(room_id)


@sio.on('select_cards')
async def handle_select_cards(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game or game['phase'] != 'select_cards':
        await sio.emit('error', {'message': 'Not in card selection phase'}, room=sid)
        return
    ok, msg = GameEngine.process_card_selection(game, session['user_id'], data.get('cards', []))
    if not ok:
        await sio.emit('error', {'message': msg}, room=sid)
        return
    if GameEngine.check_all_cards_selected(game):
        GameEngine.reveal_selected_cards(game)
        GameEngine.draw_shop_tiles(game)
        game['phase'] = 'trade'
        game['trade_votes'] = []
    await broadcast_game_state(room_id)


@sio.on('initiate_deal')
async def handle_initiate_deal(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game or game['phase'] != 'trade':
        await sio.emit('error', {'message': 'Not in trading phase'}, room=sid)
        return
    uid = session['user_id']
    target_id = data.get('target_id')
    if not target_id or target_id not in game['players'] or uid == target_id:
        await sio.emit('error', {'message': 'Invalid target'}, room=sid)
        return
    for d in game['active_deals'].values():
        if d['status'] in ('pending', 'negotiating'):
            if uid in (d['initiator'], d['target']):
                await sio.emit('error', {'message': 'You are already in a deal'}, room=sid)
                return
            if target_id in (d['initiator'], d['target']):
                await sio.emit('error', {'message': 'Target is in a deal'}, room=sid)
                return
    deal_id = str(uuid.uuid4())[:8]
    deal = {
        'id': deal_id, 'initiator': uid, 'initiator_name': game['players'][uid]['username'],
        'target': target_id, 'target_name': game['players'][target_id]['username'],
        'status': 'pending',
        'initiator_offer': {'spaces': [], 'tiles': [], 'money': 0},
        'target_offer': {'spaces': [], 'tiles': [], 'money': 0},
        'initiator_confirmed': False, 'target_confirmed': False,
    }
    game['active_deals'][deal_id] = deal
    tsid = user_to_sid.get(target_id)
    if tsid:
        await sio.emit('deal_request', deal, room=tsid)
    await sio.emit('deal_update', deal, room=sid)
    await broadcast_game_state(room_id)


@sio.on('respond_deal')
async def handle_respond_deal(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game:
        return
    deal = game['active_deals'].get(data.get('deal_id'))
    if not deal or deal['target'] != session['user_id']:
        return
    if data.get('accept'):
        deal['status'] = 'negotiating'
        for pid in (deal['initiator'], deal['target']):
            psid = user_to_sid.get(pid)
            if psid:
                await sio.emit('deal_update', deal, room=psid)
    else:
        did = deal['id']
        del game['active_deals'][did]
        for pid in (deal['initiator'], deal['target']):
            psid = user_to_sid.get(pid)
            if psid:
                await sio.emit('deal_cancelled', {'deal_id': did}, room=psid)
    await broadcast_game_state(room_id)


@sio.on('update_offer')
async def handle_update_offer(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    game = active_games.get(session.get('room_id'))
    if not game:
        return
    deal = game['active_deals'].get(data.get('deal_id'))
    if not deal or deal['status'] != 'negotiating':
        return
    uid = session['user_id']
    offer = data.get('offer', {})
    if uid == deal['initiator']:
        deal['initiator_offer'] = offer
        deal['initiator_confirmed'] = False
    elif uid == deal['target']:
        deal['target_offer'] = offer
        deal['target_confirmed'] = False
    else:
        return
    for pid in (deal['initiator'], deal['target']):
        psid = user_to_sid.get(pid)
        if psid:
            await sio.emit('deal_update', deal, room=psid)
    await broadcast_game_state(session.get('room_id'))


@sio.on('confirm_deal')
async def handle_confirm_deal(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game:
        return
    deal = game['active_deals'].get(data.get('deal_id'))
    if not deal or deal['status'] != 'negotiating':
        return
    uid = session['user_id']
    if uid == deal['initiator']:
        deal['initiator_confirmed'] = True
    elif uid == deal['target']:
        deal['target_confirmed'] = True
    if deal['initiator_confirmed'] and deal['target_confirmed']:
        ok, msg = GameEngine.execute_trade(game, deal)
        if ok:
            did = deal['id']
            del game['active_deals'][did]
            for pid in (deal['initiator'], deal['target']):
                psid = user_to_sid.get(pid)
                if psid:
                    await sio.emit('deal_completed', {'deal_id': did}, room=psid)
            if uid in game['trade_votes']:
                game['trade_votes'].remove(uid)
            other = deal['initiator'] if uid == deal['target'] else deal['target']
            if other in game['trade_votes']:
                game['trade_votes'].remove(other)
        else:
            deal['initiator_confirmed'] = False
            deal['target_confirmed'] = False
            for pid in (deal['initiator'], deal['target']):
                psid = user_to_sid.get(pid)
                if psid:
                    await sio.emit('error', {'message': msg}, room=psid)
    else:
        for pid in (deal['initiator'], deal['target']):
            psid = user_to_sid.get(pid)
            if psid:
                await sio.emit('deal_update', deal, room=psid)
    await broadcast_game_state(room_id)


@sio.on('cancel_deal')
async def handle_cancel_deal(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game:
        return
    deal = game['active_deals'].get(data.get('deal_id'))
    if not deal:
        return
    uid = session['user_id']
    if uid not in (deal['initiator'], deal['target']):
        return
    did = deal['id']
    del game['active_deals'][did]
    for pid in (deal['initiator'], deal['target']):
        psid = user_to_sid.get(pid)
        if psid:
            await sio.emit('deal_cancelled', {'deal_id': did}, room=psid)
    await broadcast_game_state(room_id)


@sio.on('end_trading')
async def handle_end_trading(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game or game['phase'] != 'trade':
        return
    uid = session['user_id']
    if uid not in game['trade_votes']:
        game['trade_votes'].append(uid)
    if len(game['trade_votes']) >= len(game['players']):
        for did in list(game['active_deals'].keys()):
            deal = game['active_deals'].pop(did)
            for pid in (deal['initiator'], deal['target']):
                psid = user_to_sid.get(pid)
                if psid:
                    await sio.emit('deal_cancelled', {'deal_id': did}, room=psid)
        game['phase'] = 'place_tiles'
        game['current_turn_index'] = game['first_player_index']
        game['placement_done'] = []
    await broadcast_game_state(room_id)


@sio.on('cancel_end_trading')
async def handle_cancel_end_trading(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    game = active_games.get(session.get('room_id'))
    if not game or game['phase'] != 'trade':
        return
    uid = session['user_id']
    if uid in game['trade_votes']:
        game['trade_votes'].remove(uid)
    await broadcast_game_state(session.get('room_id'))


@sio.on('place_tile')
async def handle_place_tile(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game or game['phase'] != 'place_tiles':
        await sio.emit('error', {'message': 'Not in placement phase'}, room=sid)
        return
    uid = session['user_id']
    if uid != game['player_order'][game['current_turn_index']]:
        await sio.emit('error', {'message': 'Not your turn'}, room=sid)
        return
    ok, msg = GameEngine.place_tile(game, uid, data.get('tile_id'), data.get('space_id'))
    if not ok:
        await sio.emit('error', {'message': msg}, room=sid)
        return
    await broadcast_game_state(room_id)


@sio.on('undo_placement')
async def handle_undo_placement(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game or game['phase'] != 'place_tiles':
        return
    uid = session['user_id']
    ok, msg = GameEngine.undo_placement(game, uid, data.get('space_id'))
    if not ok:
        await sio.emit('error', {'message': msg}, room=sid)
        return
    await broadcast_game_state(room_id)


@sio.on('done_placing')
async def handle_done_placing(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game or game['phase'] != 'place_tiles':
        return
    uid = session['user_id']
    if uid != game['player_order'][game['current_turn_index']]:
        await sio.emit('error', {'message': 'Not your turn'}, room=sid)
        return
    if uid not in game['placement_done']:
        game['placement_done'].append(uid)
    if len(game['placement_done']) >= len(game['players']):
        game['placements_this_round'] = []
        income = GameEngine.calculate_income(game)
        game['last_income'] = income
        game['phase'] = 'income'
    else:
        game['current_turn_index'] = (game['current_turn_index'] + 1) % len(game['player_order'])
    await broadcast_game_state(room_id)


@sio.on('continue_game')
async def handle_continue_game(sid, data):
    session = sid_to_user.get(sid)
    if not session:
        return
    room_id = session.get('room_id')
    game = active_games.get(room_id)
    if not game or game['phase'] != 'income':
        return
    if game['round'] >= 6:
        game['phase'] = 'game_over'
        game['status'] = 'finished'
        await db.rooms.update_one({'room_id': room_id}, {'$set': {'status': 'finished'}})
    else:
        GameEngine.advance_round(game)
        GameEngine.deal_building_cards(game)
    await broadcast_game_state(room_id)


async def broadcast_game_state(room_id):
    game = active_games.get(room_id)
    if not game:
        return
    for player_id in game['players']:
        psid = user_to_sid.get(player_id)
        if psid:
            view = GameEngine.get_player_view(game, player_id)
            await sio.emit('game_state', view, room=psid)


fastapi_app.include_router(api)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.on_event("startup")
async def startup():
    await db.users.create_index('username', unique=True)
    await db.users.create_index('user_id', unique=True)
    await db.rooms.create_index('room_id', unique=True)
    logger.info("Chinatown Game Server started")


@fastapi_app.on_event("shutdown")
async def shutdown():
    client.close()


app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path='api/socket.io')
