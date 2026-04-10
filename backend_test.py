#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Chinatown Board Game
Tests all REST APIs and Socket.IO functionality
"""

import requests
import socketio
import asyncio
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configuration
BACKEND_URL = "https://shop-mogul-game.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

# Test credentials
TEST_USERS = [
    {"username": "testplayer1", "password": "pass123"},
    {"username": "testplayer2", "password": "pass123"},
    {"username": "testplayer3", "password": "pass123"}
]

class ChinatownAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.tokens = {}
        self.users = {}
        self.room_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.socket_clients = {}
        self.game_states = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_test(self, name: str, test_func, *args, **kwargs) -> Tuple[bool, any]:
        """Run a single test and track results"""
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            result = test_func(*args, **kwargs)
            if result is True or (isinstance(result, tuple) and result[0] is True):
                self.tests_passed += 1
                self.log(f"✅ {name} - PASSED", "SUCCESS")
                return True, result[1] if isinstance(result, tuple) else None
            else:
                self.log(f"❌ {name} - FAILED: {result}", "ERROR")
                return False, result
        except Exception as e:
            self.log(f"❌ {name} - ERROR: {str(e)}", "ERROR")
            return False, str(e)
    
    async def run_async_test(self, name: str, test_func, *args, **kwargs) -> Tuple[bool, any]:
        """Run a single async test and track results"""
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            result = await test_func(*args, **kwargs)
            if result is True or (isinstance(result, tuple) and result[0] is True):
                self.tests_passed += 1
                self.log(f"✅ {name} - PASSED", "SUCCESS")
                return True, result[1] if isinstance(result, tuple) else None
            else:
                self.log(f"❌ {name} - FAILED: {result}", "ERROR")
                return False, result
        except Exception as e:
            self.log(f"❌ {name} - ERROR: {str(e)}", "ERROR")
            return False, str(e)
    
    def test_auth_register(self, username: str, password: str) -> Tuple[bool, dict]:
        """Test user registration"""
        url = f"{self.base_url}/api/auth/register"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                self.tokens[username] = user_data.get('token')
                self.users[username] = user_data
                return True, user_data
            else:
                return False, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def test_auth_login(self, username: str, password: str) -> Tuple[bool, dict]:
        """Test user login"""
        url = f"{self.base_url}/api/auth/login"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                self.tokens[username] = user_data.get('token')
                self.users[username] = user_data
                return True, user_data
            else:
                return False, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def test_auth_me(self, username: str) -> Tuple[bool, dict]:
        """Test get current user info"""
        url = f"{self.base_url}/api/auth/me"
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def test_rooms_create(self, username: str) -> Tuple[bool, dict]:
        """Test room creation"""
        url = f"{self.base_url}/api/rooms/create"
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        
        try:
            response = requests.post(url, headers=headers, timeout=10)
            if response.status_code == 200:
                room_data = response.json()
                self.room_id = room_data.get('room_id')
                return True, room_data
            else:
                return False, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def test_rooms_list(self, username: str) -> Tuple[bool, list]:
        """Test listing rooms"""
        url = f"{self.base_url}/api/rooms"
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def test_rooms_join(self, username: str, room_id: str) -> Tuple[bool, dict]:
        """Test joining a room"""
        url = f"{self.base_url}/api/rooms/{room_id}/join"
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        
        try:
            response = requests.post(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def test_rooms_leave(self, username: str, room_id: str) -> Tuple[bool, dict]:
        """Test leaving a room"""
        url = f"{self.base_url}/api/rooms/{room_id}/leave"
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        
        try:
            response = requests.post(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)

    async def test_socket_connection(self, username: str) -> Tuple[bool, str]:
        """Test Socket.IO connection with JWT auth"""
        try:
            sio = socketio.AsyncClient()
            self.socket_clients[username] = sio
            
            # Set up event handlers
            @sio.event
            async def connect():
                self.log(f"Socket connected for {username}")
            
            @sio.event
            async def disconnect():
                self.log(f"Socket disconnected for {username}")
            
            @sio.event
            async def game_state(data):
                self.game_states[username] = data
                self.log(f"Game state received for {username}: phase={data.get('phase')}")
            
            @sio.event
            async def room_info(data):
                self.log(f"Room info received for {username}: {data.get('room_id')}")
            
            @sio.event
            async def error(data):
                self.log(f"Socket error for {username}: {data.get('message')}", "ERROR")
            
            # Connect with JWT token
            await sio.connect(
                self.base_url,
                socketio_path=SOCKET_PATH,
                auth={"token": self.tokens[username]},
                transports=['polling', 'websocket']
            )
            
            # Wait a bit for connection to establish
            await asyncio.sleep(1)
            
            if sio.connected:
                return True, "Connected successfully"
            else:
                return False, "Failed to connect"
                
        except Exception as e:
            return False, str(e)
    
    async def test_socket_join_room(self, username: str, room_id: str) -> Tuple[bool, str]:
        """Test Socket.IO join_room event"""
        try:
            sio = self.socket_clients.get(username)
            if not sio or not sio.connected:
                return False, "Socket not connected"
            
            await sio.emit('join_room', {'room_id': room_id})
            await asyncio.sleep(1)  # Wait for response
            
            return True, "Join room event sent"
        except Exception as e:
            return False, str(e)
    
    async def test_socket_start_game(self, username: str, room_id: str) -> Tuple[bool, str]:
        """Test Socket.IO start_game event"""
        try:
            sio = self.socket_clients.get(username)
            if not sio or not sio.connected:
                return False, "Socket not connected"
            
            await sio.emit('start_game', {'room_id': room_id})
            await asyncio.sleep(2)  # Wait for game to start
            
            # Check if we received game state
            if username in self.game_states:
                game_state = self.game_states[username]
                if game_state.get('phase') == 'select_cards':
                    return True, "Game started successfully"
                else:
                    return False, f"Unexpected phase: {game_state.get('phase')}"
            else:
                return False, "No game state received"
                
        except Exception as e:
            return False, str(e)
    
    async def test_socket_select_cards(self, username: str) -> Tuple[bool, str]:
        """Test Socket.IO select_cards event"""
        try:
            sio = self.socket_clients.get(username)
            if not sio or not sio.connected:
                return False, "Socket not connected"
            
            game_state = self.game_states.get(username)
            if not game_state:
                return False, "No game state available"
            
            dealt_cards = game_state.get('my_dealt_cards', [])
            n_keep = game_state.get('n_keep', 0)
            
            if len(dealt_cards) < n_keep:
                return False, f"Not enough cards dealt: {len(dealt_cards)} < {n_keep}"
            
            # Select the first n_keep cards
            selected_cards = dealt_cards[:n_keep]
            await sio.emit('select_cards', {'cards': selected_cards})
            await asyncio.sleep(1)
            
            return True, f"Selected {len(selected_cards)} cards"
        except Exception as e:
            return False, str(e)
    
    async def cleanup_sockets(self):
        """Clean up all socket connections"""
        for username, sio in self.socket_clients.items():
            try:
                if sio.connected:
                    await sio.disconnect()
            except Exception as e:
                self.log(f"Error disconnecting {username}: {e}", "ERROR")
    
    def print_summary(self):
        """Print test summary"""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"{'='*60}")
        
        return success_rate >= 80  # Consider 80%+ as overall success

async def run_backend_tests():
    """Run all backend tests"""
    tester = ChinatownAPITester()
    
    print("🎮 Starting Chinatown Backend API Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Socket.IO Path: {SOCKET_PATH}")
    print("="*60)
    
    try:
        # Test 1: User Registration
        for i, user in enumerate(TEST_USERS):
            success, result = tester.run_test(
                f"Register User {i+1} ({user['username']})",
                tester.test_auth_register,
                user['username'], user['password']
            )
            if not success and "already taken" in str(result):
                # Try login instead if user already exists
                success, result = tester.run_test(
                    f"Login User {i+1} ({user['username']})",
                    tester.test_auth_login,
                    user['username'], user['password']
                )
        
        # Test 2: Get user info and leave existing rooms
        for user in TEST_USERS:
            if user['username'] in tester.tokens:
                success, user_info = tester.run_test(
                    f"Get User Info ({user['username']})",
                    tester.test_auth_me,
                    user['username']
                )
                # If user is in a room, try to leave it
                if success and user_info and user_info.get('active_room'):
                    tester.run_test(
                        f"Leave Existing Room ({user['username']})",
                        tester.test_rooms_leave,
                        user['username'],
                        user_info['active_room']
                    )
        
        # Test 3: Room creation
        if TEST_USERS[0]['username'] in tester.tokens:
            tester.run_test(
                "Create Room",
                tester.test_rooms_create,
                TEST_USERS[0]['username']
            )
        
        # Test 4: List rooms
        if TEST_USERS[1]['username'] in tester.tokens:
            tester.run_test(
                "List Rooms",
                tester.test_rooms_list,
                TEST_USERS[1]['username']
            )
        
        # Test 5: Join room
        if tester.room_id and TEST_USERS[1]['username'] in tester.tokens:
            tester.run_test(
                "Join Room",
                tester.test_rooms_join,
                TEST_USERS[1]['username'],
                tester.room_id
            )
        
        # Test 6: Socket.IO connections
        for user in TEST_USERS:
            if user['username'] in tester.tokens:
                success, result = await tester.run_async_test(
                    f"Socket Connection ({user['username']})",
                    tester.test_socket_connection,
                    user['username']
                )
        
        # Test 7: Socket.IO join room
        for user in TEST_USERS:
            if user['username'] in tester.socket_clients and tester.room_id:
                await tester.run_async_test(
                    f"Socket Join Room ({user['username']})",
                    tester.test_socket_join_room,
                    user['username'],
                    tester.room_id
                )
        
        # Test 8: Start game (need 3+ players)
        if len(tester.socket_clients) >= 3 and tester.room_id:
            # Add third player to room first
            if TEST_USERS[2]['username'] in tester.tokens:
                tester.run_test(
                    "Join Room (Player 3)",
                    tester.test_rooms_join,
                    TEST_USERS[2]['username'],
                    tester.room_id
                )
                
                # Connect third player socket
                await tester.run_async_test(
                    f"Socket Connection (Player 3)",
                    tester.test_socket_connection,
                    TEST_USERS[2]['username']
                )
                
                await tester.run_async_test(
                    f"Socket Join Room (Player 3)",
                    tester.test_socket_join_room,
                    TEST_USERS[2]['username'],
                    tester.room_id
                )
            
            # Now try to start the game
            await tester.run_async_test(
                "Start Game",
                tester.test_socket_start_game,
                TEST_USERS[0]['username'],
                tester.room_id
            )
            
            # Test 9: Card selection
            await asyncio.sleep(2)  # Wait for game state to propagate
            for user in TEST_USERS:
                if user['username'] in tester.game_states:
                    await tester.run_async_test(
                        f"Select Cards ({user['username']})",
                        tester.test_socket_select_cards,
                        user['username']
                    )
        
        # Cleanup
        await tester.cleanup_sockets()
        
        # Print results
        overall_success = tester.print_summary()
        return overall_success
        
    except Exception as e:
        tester.log(f"Critical error during testing: {e}", "CRITICAL")
        await tester.cleanup_sockets()
        return False

def main():
    """Main entry point"""
    try:
        success = asyncio.run(run_backend_tests())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())