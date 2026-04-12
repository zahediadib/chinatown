import random
from game_constants import (
    SHOP_TYPES, INCOME_TABLE, CARD_DISTRIBUTION,
    TILES_PER_ROUND, PLAYER_COLORS, PLAYER_COLOR_NAMES, ADJACENCY
)


class GameEngine:
    @staticmethod
    def create_game(room_id, players_info):
        player_order = [p[0] for p in players_info]
        random.shuffle(player_order)

        players = {}
        for i, user_id in enumerate(player_order):
            username = next(u for uid, u in players_info if uid == user_id)
            players[user_id] = {
                'username': username,
                'color': PLAYER_COLORS[i],
                'color_name': PLAYER_COLOR_NAMES[i],
                'money': 50000,
                'shop_tiles': [],
                'connected': True,
                'order': i,
            }

        board = {}
        for i in range(1, 86):
            board[str(i)] = {'owner': None, 'shop_tile': None}

        tile_bag = []
        tid = 0
        for shop_type, info in SHOP_TYPES.items():
            for _ in range(info['totalTiles']):
                tile_bag.append({'id': tid, 'type': shop_type})
                tid += 1
        random.shuffle(tile_bag)

        building_deck = list(range(1, 86))
        random.shuffle(building_deck)

        return {
            'room_id': room_id,
            'status': 'playing',
            'round': 1,
            'year': 1965,
            'phase': 'select_cards',
            'player_count': len(players_info),
            'player_order': player_order,
            'first_player_index': 0,
            'current_turn_index': 0,
            'players': players,
            'board': board,
            'tile_bag': tile_bag,
            'building_deck': building_deck,
            'cards_dealing': {},
            'n_keep': 0,
            'cards_selected': {},
            'cards_remaining_deck': [],
            'tiles_drawn': {},
            'trade_votes': [],
            'active_deals': {},
            'placements_this_round': [],
            'placement_done': [],
            'last_income': {},
        }

    @staticmethod
    def deal_building_cards(game):
        pc = game['player_count']
        rd = game['round']
        n_deal, n_keep = CARD_DISTRIBUTION[pc][rd]

        deck = list(game['building_deck'])
        random.shuffle(deck)

        dealing = {}
        for player_id in game['player_order']:
            count = min(n_deal, len(deck))
            dealing[player_id] = deck[:count]
            deck = deck[count:]

        game['cards_dealing'] = dealing
        game['cards_remaining_deck'] = deck
        game['n_keep'] = n_keep
        game['cards_selected'] = {}
        game['phase'] = 'select_cards'

    @staticmethod
    def process_card_selection(game, player_id, selected_cards):
        if player_id in game['cards_selected']:
            return False, 'Already selected cards'

        dealt = game['cards_dealing'].get(player_id, [])
        if not dealt:
            return False, 'No cards dealt'

        n_keep = game['n_keep']
        if len(selected_cards) != n_keep:
            return False, f'Must select exactly {n_keep} cards'

        for card in selected_cards:
            if card not in dealt:
                return False, f'Card {card} was not dealt to you'

        game['cards_selected'][player_id] = selected_cards
        return True, 'Cards selected'

    @staticmethod
    def check_all_cards_selected(game):
        return len(game['cards_selected']) >= len(game['players'])

    @staticmethod
    def reveal_selected_cards(game):
        all_unkept = []
        for player_id, selected in game['cards_selected'].items():
            dealt = game['cards_dealing'].get(player_id, [])
            unkept = [c for c in dealt if c not in selected]
            all_unkept.extend(unkept)
            for space_id in selected:
                space = game['board'].get(str(space_id))
                if space:
                    space['owner'] = player_id

        game['building_deck'] = game.get('cards_remaining_deck', []) + all_unkept
        game['cards_dealing'] = {}
        game['cards_selected'] = {}
        game.pop('cards_remaining_deck', None)

    @staticmethod
    def draw_shop_tiles(game):
        bag = game['tile_bag']
        drawn = {}
        for player_id in game['player_order']:
            player_tiles = []
            for _ in range(TILES_PER_ROUND):
                if bag:
                    player_tiles.append(bag.pop(0))
            drawn[player_id] = player_tiles
            game['players'][player_id]['shop_tiles'].extend(player_tiles)
        game['tiles_drawn'] = drawn

    @staticmethod
    def place_tile(game, player_id, tile_id, space_id):
        player = game['players'].get(player_id)
        if not player:
            return False, 'Player not found'

        space = game['board'].get(str(space_id))
        if not space:
            return False, 'Invalid space'
        if space['owner'] != player_id:
            return False, "You don't own this space"
        if space['shop_tile'] is not None:
            return False, 'Space already has a shop tile'

        tile_idx = next((i for i, t in enumerate(player['shop_tiles']) if t['id'] == tile_id), None)
        if tile_idx is None:
            return False, 'Tile not found in your hand'

        tile = player['shop_tiles'].pop(tile_idx)
        space['shop_tile'] = tile
        game['placements_this_round'].append({
            'player_id': player_id,
            'tile': tile,
            'space_id': space_id,
        })
        return True, 'Tile placed'

    @staticmethod
    def undo_placement(game, player_id, space_id):
        idx = next(
            (i for i, p in enumerate(game['placements_this_round'])
             if p['player_id'] == player_id and p['space_id'] == space_id),
            None
        )
        if idx is None:
            return False, 'No placement to undo at this space'

        placement = game['placements_this_round'].pop(idx)
        game['board'][str(space_id)]['shop_tile'] = None
        game['players'][player_id]['shop_tiles'].append(placement['tile'])
        return True, 'Placement undone'

    @staticmethod
    def find_businesses(game):
        businesses = []
        visited = set()
        for space_id_str, space in game['board'].items():
            sid = int(space_id_str)
            if sid in visited or not space['shop_tile']:
                continue
            owner = space['owner']
            shop_type = space['shop_tile']['type']
            group = []
            queue = [sid]
            while queue:
                cur = queue.pop(0)
                if cur in visited:
                    continue
                cs = game['board'].get(str(cur))
                if not cs or cs['owner'] != owner or not cs['shop_tile'] or cs['shop_tile']['type'] != shop_type:
                    continue
                visited.add(cur)
                group.append(cur)
                for nb in ADJACENCY.get(cur, []):
                    if nb not in visited:
                        queue.append(nb)
            if group:
                businesses.append({'owner': owner, 'type': shop_type, 'spaces': group, 'size': len(group)})
        return businesses

    @staticmethod
    def calculate_income(game):
        businesses = GameEngine.find_businesses(game)
        income_details = {pid: {'total': 0, 'businesses': []} for pid in game['players']}

        for biz in businesses:
            max_size = SHOP_TYPES[biz['type']]['maxSize']
            remaining = biz['size']
            biz_income = 0
            while remaining >= max_size:
                entry = INCOME_TABLE[max_size]
                biz_income += entry['complete'] if isinstance(entry, dict) else entry
                remaining -= max_size
            if remaining > 0:
                entry = INCOME_TABLE[remaining]
                biz_income += entry['incomplete'] if isinstance(entry, dict) else entry

            game['players'][biz['owner']]['money'] += biz_income
            income_details[biz['owner']]['total'] += biz_income
            income_details[biz['owner']]['businesses'].append({
                'type': biz['type'], 'spaces': biz['spaces'],
                'size': biz['size'], 'income': biz_income,
            })
        return income_details

    @staticmethod
    def execute_trade(game, deal):
        init_id = deal['initiator']
        tgt_id = deal['target']
        io = deal['initiator_offer']
        to = deal['target_offer']

        if io.get('money', 0) > game['players'][init_id]['money']:
            return False, 'Initiator does not have enough money'
        if to.get('money', 0) > game['players'][tgt_id]['money']:
            return False, 'Target does not have enough money'

        for sid in io.get('spaces', []):
            if game['board'][str(sid)]['owner'] != init_id:
                return False, f'Initiator does not own space {sid}'
        for sid in to.get('spaces', []):
            if game['board'][str(sid)]['owner'] != tgt_id:
                return False, f'Target does not own space {sid}'

        init_tile_ids = {t['id'] for t in game['players'][init_id]['shop_tiles']}
        for tid in io.get('tiles', []):
            if tid not in init_tile_ids:
                return False, f'Initiator does not have tile {tid}'
        tgt_tile_ids = {t['id'] for t in game['players'][tgt_id]['shop_tiles']}
        for tid in to.get('tiles', []):
            if tid not in tgt_tile_ids:
                return False, f'Target does not have tile {tid}'

        game['players'][init_id]['money'] -= io.get('money', 0)
        game['players'][tgt_id]['money'] += io.get('money', 0)
        game['players'][tgt_id]['money'] -= to.get('money', 0)
        game['players'][init_id]['money'] += to.get('money', 0)

        for sid in io.get('spaces', []):
            game['board'][str(sid)]['owner'] = tgt_id
        for sid in to.get('spaces', []):
            game['board'][str(sid)]['owner'] = init_id

        for tid in io.get('tiles', []):
            tile = next(t for t in game['players'][init_id]['shop_tiles'] if t['id'] == tid)
            game['players'][init_id]['shop_tiles'].remove(tile)
            game['players'][tgt_id]['shop_tiles'].append(tile)
        for tid in to.get('tiles', []):
            tile = next(t for t in game['players'][tgt_id]['shop_tiles'] if t['id'] == tid)
            game['players'][tgt_id]['shop_tiles'].remove(tile)
            game['players'][init_id]['shop_tiles'].append(tile)

        return True, 'Trade executed'

    @staticmethod
    def advance_round(game):
        game['round'] += 1
        game['year'] += 1
        game['first_player_index'] = (game['first_player_index'] + 1) % len(game['player_order'])
        game['current_turn_index'] = game['first_player_index']
        game['trade_votes'] = []
        game['active_deals'] = {}
        game['placements_this_round'] = []
        game['placement_done'] = []
        game['tiles_drawn'] = {}
        game['last_income'] = {}

    @staticmethod
    def get_player_view(game, player_id):
        def resolve_offer_tiles(owner_id, offer):
            owner_tiles = {tile['id']: tile.get('type') for tile in game['players'][owner_id].get('shop_tiles', [])}
            return [
                {'id': tile_id, 'type': owner_tiles.get(tile_id)}
                for tile_id in offer.get('tiles', [])
            ]

        view = {
            'room_id': game['room_id'],
            'status': game['status'],
            'round': game['round'],
            'year': game['year'],
            'phase': game['phase'],
            'player_count': game['player_count'],
            'player_order': game['player_order'],
            'first_player_index': game['first_player_index'],
            'current_turn_index': game['current_turn_index'],
            'players': {},
            'board': game['board'],
            'trade_votes': game['trade_votes'],
            'placement_done': game['placement_done'],
            'tiles_drawn': game.get('tiles_drawn', {}),
            'last_income': game.get('last_income', {}),
            'n_keep': game.get('n_keep', 0),
            'my_id': player_id,
            'active_deals': [],
        }

        for pid, pd in game['players'].items():
            view['players'][pid] = {
                'username': pd['username'],
                'color': pd['color'],
                'color_name': pd['color_name'],
                'money': pd['money'],
                'shop_tiles': pd['shop_tiles'] if pid == player_id else len(pd['shop_tiles']),
                'connected': pd['connected'],
                'order': pd['order'],
            }

        if game['phase'] == 'select_cards':
            view['my_dealt_cards'] = game['cards_dealing'].get(player_id, [])
            view['my_selected'] = player_id in game['cards_selected']
            view['players_selected'] = list(game['cards_selected'].keys())

        for did, deal in game['active_deals'].items():
            summary = {'deal_id': did, 'initiator': deal['initiator'], 'target': deal['target'], 'status': deal['status']}
            detail = dict(deal)
            detail['initiator_offer'] = dict(deal.get('initiator_offer', {}))
            detail['target_offer'] = dict(deal.get('target_offer', {}))
            detail['initiator_offer_tiles'] = resolve_offer_tiles(deal['initiator'], deal.get('initiator_offer', {}))
            detail['target_offer_tiles'] = resolve_offer_tiles(deal['target'], deal.get('target_offer', {}))
            summary['detail'] = detail
            view['active_deals'].append(summary)

        # Include this round's placements (for undo)
        view['placements_this_round'] = [
            p for p in game.get('placements_this_round', []) if p['player_id'] == player_id
        ]

        return view
