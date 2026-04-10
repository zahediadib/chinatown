"""
Chinatown Board Game API Tests
Tests authentication, room management, and Socket.IO game functionality
"""
import pytest
import requests
import os
import socketio
import time
import asyncio

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_PLAYERS = [
    {"username": "testplayer1", "password": "pass123"},
    {"username": "testplayer2", "password": "pass123"},
    {"username": "testplayer3", "password": "pass123"},
]


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_testplayer1(self):
        """Test login with testplayer1 credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer1",
            "password": "pass123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user_id" in data, "No user_id in response"
        assert data["username"] == "testplayer1"
        print(f"✅ testplayer1 login successful, user_id: {data['user_id']}")
    
    def test_login_testplayer2(self):
        """Test login with testplayer2 credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer2",
            "password": "pass123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["username"] == "testplayer2"
        print(f"✅ testplayer2 login successful")
    
    def test_login_testplayer3(self):
        """Test login with testplayer3 credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer3",
            "password": "pass123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["username"] == "testplayer3"
        print(f"✅ testplayer3 login successful")
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer1",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Invalid credentials correctly rejected")
    
    def test_auth_me_endpoint(self):
        """Test /auth/me endpoint with valid token"""
        # First login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer1",
            "password": "pass123"
        })
        token = login_resp.json()["token"]
        
        # Then check /me
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert me_resp.status_code == 200, f"Auth/me failed: {me_resp.text}"
        data = me_resp.json()
        assert data["username"] == "testplayer1"
        assert "user_id" in data
        print(f"✅ /auth/me endpoint working, active_room: {data.get('active_room')}")
    
    def test_auth_me_without_token(self):
        """Test /auth/me without authorization header"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ /auth/me correctly rejects unauthenticated requests")


class TestRoomManagement:
    """Room creation and management tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for testplayer1"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer1",
            "password": "pass123"
        })
        return response.json()["token"]
    
    def test_list_rooms(self, auth_token):
        """Test listing available rooms"""
        response = requests.get(f"{BASE_URL}/api/rooms", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"List rooms failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Rooms should be a list"
        print(f"✅ Listed {len(data)} rooms")
    
    def test_create_room(self, auth_token):
        """Test room creation"""
        # First leave any existing room
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        active_room = me_resp.json().get("active_room")
        if active_room:
            requests.post(f"{BASE_URL}/api/rooms/{active_room}/leave", headers={
                "Authorization": f"Bearer {auth_token}"
            })
        
        response = requests.post(f"{BASE_URL}/api/rooms/create", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Create room failed: {response.text}"
        data = response.json()
        assert "room_id" in data, "No room_id in response"
        assert data["status"] == "waiting"
        assert len(data["players"]) == 1
        print(f"✅ Room created: {data['room_id']}")
        
        # Cleanup - leave the room
        requests.post(f"{BASE_URL}/api/rooms/{data['room_id']}/leave", headers={
            "Authorization": f"Bearer {auth_token}"
        })
    
    def test_join_room(self):
        """Test joining a room"""
        # Login as player1 and create room
        p1_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer1", "password": "pass123"
        })
        p1_token = p1_resp.json()["token"]
        
        # Leave any existing room first
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {p1_token}"
        })
        if me_resp.json().get("active_room"):
            requests.post(f"{BASE_URL}/api/rooms/{me_resp.json()['active_room']}/leave", headers={
                "Authorization": f"Bearer {p1_token}"
            })
        
        create_resp = requests.post(f"{BASE_URL}/api/rooms/create", headers={
            "Authorization": f"Bearer {p1_token}"
        })
        room_id = create_resp.json()["room_id"]
        
        # Login as player2 and join
        p2_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer2", "password": "pass123"
        })
        p2_token = p2_resp.json()["token"]
        
        # Leave any existing room first
        me_resp2 = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {p2_token}"
        })
        if me_resp2.json().get("active_room"):
            requests.post(f"{BASE_URL}/api/rooms/{me_resp2.json()['active_room']}/leave", headers={
                "Authorization": f"Bearer {p2_token}"
            })
        
        join_resp = requests.post(f"{BASE_URL}/api/rooms/{room_id}/join", headers={
            "Authorization": f"Bearer {p2_token}"
        })
        assert join_resp.status_code == 200, f"Join room failed: {join_resp.text}"
        data = join_resp.json()
        assert len(data["players"]) == 2
        print(f"✅ Player2 joined room {room_id}")
        
        # Cleanup
        requests.post(f"{BASE_URL}/api/rooms/{room_id}/leave", headers={
            "Authorization": f"Bearer {p2_token}"
        })
        requests.post(f"{BASE_URL}/api/rooms/{room_id}/leave", headers={
            "Authorization": f"Bearer {p1_token}"
        })
    
    def test_leave_room(self):
        """Test leaving a room"""
        # Login and create room
        p1_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer1", "password": "pass123"
        })
        p1_token = p1_resp.json()["token"]
        
        # Leave any existing room first
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {p1_token}"
        })
        if me_resp.json().get("active_room"):
            requests.post(f"{BASE_URL}/api/rooms/{me_resp.json()['active_room']}/leave", headers={
                "Authorization": f"Bearer {p1_token}"
            })
        
        create_resp = requests.post(f"{BASE_URL}/api/rooms/create", headers={
            "Authorization": f"Bearer {p1_token}"
        })
        room_id = create_resp.json()["room_id"]
        
        # Leave the room
        leave_resp = requests.post(f"{BASE_URL}/api/rooms/{room_id}/leave", headers={
            "Authorization": f"Bearer {p1_token}"
        })
        assert leave_resp.status_code == 200, f"Leave room failed: {leave_resp.text}"
        print(f"✅ Successfully left room {room_id}")


class TestSocketIOConnection:
    """Socket.IO connection and game flow tests"""
    
    def test_socket_connection_with_auth(self):
        """Test Socket.IO connection with JWT authentication"""
        # Get token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testplayer1", "password": "pass123"
        })
        token = login_resp.json()["token"]
        
        connected = False
        error_msg = None
        
        sio = socketio.Client()
        
        @sio.event
        def connect():
            nonlocal connected
            connected = True
            print("✅ Socket.IO connected successfully")
        
        @sio.event
        def connect_error(data):
            nonlocal error_msg
            error_msg = str(data)
        
        try:
            sio.connect(
                BASE_URL,
                socketio_path='/api/socket.io',
                auth={'token': token},
                transports=['polling', 'websocket'],
                wait_timeout=10
            )
            time.sleep(1)
            assert connected, f"Socket connection failed: {error_msg}"
        finally:
            if sio.connected:
                sio.disconnect()
    
    def test_socket_connection_without_auth(self):
        """Test Socket.IO connection without token should fail"""
        sio = socketio.Client()
        connection_refused = False
        
        @sio.event
        def connect_error(data):
            nonlocal connection_refused
            connection_refused = True
        
        try:
            sio.connect(
                BASE_URL,
                socketio_path='/api/socket.io',
                transports=['polling'],
                wait_timeout=5
            )
        except Exception as e:
            connection_refused = True
        finally:
            if sio.connected:
                sio.disconnect()
        
        assert connection_refused, "Connection should be refused without auth"
        print("✅ Socket.IO correctly rejects unauthenticated connections")


class TestGameFlow:
    """Full game flow tests with 3 players"""
    
    def test_full_game_setup_and_card_selection(self):
        """Test complete game setup: create room, join 3 players, start game, card selection"""
        tokens = []
        user_ids = []
        
        # Login all 3 players
        for player in TEST_PLAYERS:
            resp = requests.post(f"{BASE_URL}/api/auth/login", json=player)
            assert resp.status_code == 200, f"Login failed for {player['username']}"
            data = resp.json()
            tokens.append(data["token"])
            user_ids.append(data["user_id"])
        
        # Leave any existing rooms
        for token in tokens:
            me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
                "Authorization": f"Bearer {token}"
            })
            active_room = me_resp.json().get("active_room")
            if active_room:
                requests.post(f"{BASE_URL}/api/rooms/{active_room}/leave", headers={
                    "Authorization": f"Bearer {token}"
                })
        
        # Player 1 creates room
        create_resp = requests.post(f"{BASE_URL}/api/rooms/create", headers={
            "Authorization": f"Bearer {tokens[0]}"
        })
        assert create_resp.status_code == 200, f"Create room failed: {create_resp.text}"
        room_id = create_resp.json()["room_id"]
        print(f"✅ Room created: {room_id}")
        
        # Players 2 and 3 join
        for i in [1, 2]:
            join_resp = requests.post(f"{BASE_URL}/api/rooms/{room_id}/join", headers={
                "Authorization": f"Bearer {tokens[i]}"
            })
            assert join_resp.status_code == 200, f"Player {i+1} join failed: {join_resp.text}"
            print(f"✅ Player {i+1} joined room")
        
        # Connect all players via Socket.IO
        sockets = []
        game_states = {}
        room_infos = {}
        
        for i, token in enumerate(tokens):
            sio = socketio.Client()
            player_id = user_ids[i]
            
            def make_handlers(pid):
                def on_game_state(data):
                    game_states[pid] = data
                def on_room_info(data):
                    room_infos[pid] = data
                return on_game_state, on_room_info
            
            gs_handler, ri_handler = make_handlers(player_id)
            sio.on('game_state', gs_handler)
            sio.on('room_info', ri_handler)
            
            sio.connect(
                BASE_URL,
                socketio_path='/api/socket.io',
                auth={'token': token},
                transports=['polling', 'websocket'],
                wait_timeout=10
            )
            sio.emit('join_room', {'room_id': room_id})
            sockets.append(sio)
        
        time.sleep(1)
        print("✅ All 3 players connected via Socket.IO")
        
        # Host starts the game
        sockets[0].emit('start_game', {'room_id': room_id})
        time.sleep(2)
        
        # Check game state received
        assert len(game_states) > 0, "No game state received after start"
        
        # Verify game is in select_cards phase
        for pid, state in game_states.items():
            assert state.get('phase') == 'select_cards', f"Expected select_cards phase, got {state.get('phase')}"
            assert 'my_dealt_cards' in state, "No dealt cards in game state"
            assert 'n_keep' in state, "No n_keep in game state"
            print(f"✅ Player {pid[:8]}... received {len(state['my_dealt_cards'])} dealt cards, must keep {state['n_keep']}")
        
        # Each player selects cards
        for i, sio in enumerate(sockets):
            pid = user_ids[i]
            state = game_states.get(pid)
            if state:
                dealt = state['my_dealt_cards']
                n_keep = state['n_keep']
                selected = dealt[:n_keep]  # Select first n_keep cards
                sio.emit('select_cards', {'cards': selected})
                print(f"✅ Player {i+1} selected {len(selected)} cards: {selected}")
        
        time.sleep(2)
        
        # Check if game progressed to trade phase
        for pid, state in game_states.items():
            if state.get('phase') == 'trade':
                print(f"✅ Game progressed to trade phase")
                break
        
        # Cleanup - disconnect all sockets
        for sio in sockets:
            if sio.connected:
                sio.disconnect()
        
        # Leave room
        for token in tokens:
            requests.post(f"{BASE_URL}/api/rooms/{room_id}/leave", headers={
                "Authorization": f"Bearer {token}"
            })
        
        print("✅ Full game flow test completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
