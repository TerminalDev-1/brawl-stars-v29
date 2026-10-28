"""/dev commands typed in team chat. Private server only: every player may use them."""
from dataclasses import dataclass

import brawlers

HELP = ('/gems N, /coins N, /t N (total trophies), /bt N (selected brawler trophies), '
        '/unlock <brawler|all>, /max [brawler|all], /tokens N, /help')


@dataclass
class Result:
    reply: str
    changed: bool = False


def _number(text):
    try:
        value = int(text)
    except (TypeError, ValueError):
        return None
    return value if 0 <= value <= 1_000_000_000 else None


def _brawler_arg(player, words):
    """Brawler named by the remaining words, or the selected one when none is given."""
    if not words:
        return player.get('brawler', 0)
    return brawlers.find(' '.join(words))


def run(player, text):
    """Apply a command. Returns a Result, or None if text isn't a command."""
    if not text.startswith('/'):
        return None
    words = text[1:].split()
    if not words:
        return Result(HELP)
    command, args = words[0].lower(), words[1:]
    value = _number(args[0] if args else None)

    if command == 'help':
        return Result(HELP)
    if command in ('gems', 'coins', 'tokens'):
        if value is None:
            return Result(f'Usage: /{command} N')
        if command == 'gems':
            player['gems'] = value
        elif command == 'coins':
            player['gold'] = value
            return Result(f'Coins set to {value}. Shows after a battle or reopening the game.', True)
        else:
            player.setdefault('brawl_pass', {})['tokens'] = value
        return Result(f'{command.capitalize()} set to {value}. Shows after a battle or reopening the game.', True)
    if command == 't':
        if value is None:
            return Result('Usage: /t N')
        player['trophies'] = value
        player['highest_trophies'] = value
        return Result(f'Total trophies set to {value}. Shows after a battle or reopening the game.', True)
    if command == 'bt':
        brawler = player.get('brawler', 0)
        if value is None:
            return Result('Usage: /bt N')
        per = player.get('brawler_trophies') or {'0': player.get('trophies', 0)}
        per[str(brawler)] = value
        player['brawler_trophies'] = per
        return Result(f"{brawlers.NAMES.get(brawler, 'Brawler')} trophies set to {value}. "
                      'Shows after a battle or reopening the game.', True)
    if command in ('unlock', 'max'):
        if args and args[0].lower() == 'all':
            targets = list(brawlers.NAMES)
        else:
            brawler = _brawler_arg(player, args)
            if brawler is None:
                return Result('Unknown brawler. Try a name like Colt or El Primo.')
            targets = [brawler]
        for brawler in targets:
            if command == 'max':
                brawlers.max_out(player, brawler)
            elif brawler not in brawlers.owned(player):
                brawlers.owned(player).append(brawler)
        what = 'Every brawler' if len(targets) > 1 else brawlers.NAMES[targets[0]]
        done = 'maxed (power 9, star powers, gadget)' if command == 'max' else 'unlocked'
        return Result(f'{what} {done}. Shows after a battle or reopening the game.', True)
    return Result(f'Unknown command /{command}. {HELP}')
