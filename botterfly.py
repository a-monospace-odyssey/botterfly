import discord
from discord.ext import commands
from python_mpv_jsonipc import MPV
from dotenv import load_dotenv
import os
import random
import glob
import re
from fuzzywuzzy import fuzz, process

def get_random_file(directory, extensions):
    found_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in extensions:
                found_files.append(os.path.join(root, file))
    if not found_files:
        return None
    return random.choice(found_files)

def fuzzy_search_directory(query, directory, extensions):
    found_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in extensions:
                found_files.append(os.path.join(root, file))
    results = process.extract(query, found_files, limit=1)
    best_match = results[0]
    return best_match[0] if best_match[1] >= 50 else None

# Function for making shows watched log
def log_last_played(directory, show_name, season_episode):
    filepath = os.path.join(directory, 'last_played.txt')
    data = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as fr:
            for line in fr.readlines():
                show, ep = line.strip().split(',')
                data[show] = ep

    with open(filepath, 'w') as fw:
        sanitized_show_name = show_name.replace(',', '') if ',' in show_name else show_name
        sanitized_season_episode = season_episode.replace(',', '') if ',' in season_episode else season_episode

        data[sanitized_show_name] = sanitized_season_episode

        for show, ep in data.items():
            fw.write(f'{show},{ep}\n')

# Fuzzy search for show log
def get_best_match(search_string, candidates, threshold=80):
    best_ratio = threshold
    best_match = None
    for candidate in candidates:
        ratio = fuzz.partial_ratio(search_string.lower(), candidate.lower())
        if ratio > best_ratio:
            best_match = candidate
            best_ratio = ratio
    return best_match

# reading shows watched log
def get_next_episode(directory, show_to_search):
    filepath = os.path.join(directory, 'last_played.txt')
    if not os.path.exists(filepath):
        return None, None
    with open(filepath, 'r') as f:
        lines = f.readlines()
        stored_shows = [line.strip().split(',')[0] for line in lines]
        show_name = get_best_match(show_to_search, stored_shows)
        if show_name is None:
            return None, None
        for line in lines:
            show, season_episode = line.strip().split(',')
            if show == show_name:
                break
        season, episode = re.match(r'S(\d+)E(\d+)', season_episode.upper()).groups()
        next_episode = f'S{int(season):02d}E{int(episode)+1:02d}'
    return show_name, next_episode

# loading next episode in list
async def play_media(ctx, show_name, season_episode, directory):
    show_name_with_periods = '.'.join(show_name.split())
    search_text = f'{show_name_with_periods}.{season_episode}'
    media_files = glob.glob(os.path.join(directory, '**', '*.*'), recursive=True)
    found_media = ''
    highest_similarity = 0

    for media in media_files:
        base_media_name = os.path.splitext(os.path.basename(media))[0]
        similarity = fuzz.token_set_ratio(search_text.lower(), base_media_name.lower())
        if similarity > highest_similarity:
            highest_similarity = similarity
            found_media = media

    if found_media:
        # Check if the player is idle, if it is, start playback. Otherwise, enqueue the media.
        if player.command("get_property", "idle-active"):
            player.loadfile(found_media)
        else:
            player.command("loadfile", found_media, "append-play")

        sanitized_show_name = show_name.replace(',', '')
        log_last_played(directory, sanitized_show_name, season_episode)
        await ctx.send(f'Media added to queue: {found_media}')
    else:
        await ctx.send(f'No media file found for search text: {search_text}')


load_dotenv()
player = MPV()
TOKEN = os.getenv('DISCORD_TOKEN')

# Declare intents
intents = discord.Intents.all()
intents.members = True
intents.guilds = True
intents.messages = True

# Initialize the bot
bot = commands.Bot(command_prefix='$', intents=intents)



@bot.command()
async def recentlyadded(ctx):
    with open('Z:\\CYM\\recently-added.txt', 'rb') as f:
        file = discord.File(f)
        await ctx.send(file=file)

@bot.command()
async def listmovies(ctx):
    with open('Z:\\CYM\\movie-list.txt', 'rb') as f:
        file = discord.File(f)
        await ctx.send(file=file)

@bot.command()
async def listshows(ctx):
    with open('Z:\\CYM\\show-list.txt', 'rb') as f:
        file = discord.File(f)
        await ctx.send(file=file)

@bot.command()
async def pause(ctx):
    player.pause = True
    await ctx.send("Paused MPV.")

@bot.command()
async def unpause(ctx):
    player.pause = False
    await ctx.send("Unpaused MPV.")

@bot.command()
async def resume(ctx):
    player.pause = False
    await ctx.send("Resumed MPV.")

@bot.command()
async def skip(ctx):
    player.playlist_next()
    await ctx.send("Skipped to the next loaded media.")

@bot.command()
async def ffw(ctx, seconds: int):
    player.seek(player.time_pos + seconds)
    await ctx.send(f"Skipped forward {seconds} seconds.")

@bot.command()
async def rew(ctx, seconds: int):
    player.seek(player.time_pos - seconds)
    await ctx.send(f"Skipped backward {seconds} seconds.")

@bot.command()
async def time(ctx):
    try:
        current_time = player.playback_time
        time_left = player.duration - current_time
        total_time = player.duration

        current_time_formatted = f"{int(current_time // 60)}:{int(current_time % 60):02d}"
        total_time_formatted = f"{int(total_time // 60)}:{int(total_time % 60):02d}"
        time_left_formatted = f"{int(time_left // 60)}:{int(time_left % 60):02d}"

        response = f"{current_time_formatted}/{total_time_formatted} ({time_left_formatted})"
    except Exception as e:
        response = f"Error: {e}"
    await ctx.send(response)




@bot.command()
async def playmusicvideo(ctx, *, search_query: str = None):
    extensions = ['.mp4', '.webm', '.avi']
    directory_path = 'Z:\CYM\Music Videos'
    if search_query:
        media_file_path = fuzzy_search_directory(search_query, directory_path, extensions)
        print(f"Searching for query: {search_query}")  # Debug line to see the searched query
    else:
        media_file_path = get_random_file(directory_path, extensions)

    print(f"Selected media file path: {media_file_path}")  # Debug line to see the selected media file path

    if media_file_path:
        player.command("loadfile", media_file_path, "append-play")
        await ctx.send(f'Loaded and added to queue: {media_file_path}')
    else:
        await ctx.send('No matching file found.')

@bot.command()
async def playintermission(ctx, *, search_query: str = None):
    directory_path = 'Z:\CYM\Intermissions'
    intermission_extensions = {'.mp4', '.mkv', '.avi'}

    if search_query:
        media_file_path = fuzzy_search_directory(search_query, directory_path, intermission_extensions)
    else:
        media_file_path = get_random_file(directory_path, intermission_extensions)

    if media_file_path:
        player.command("loadfile", media_file_path, "append-play")
        await ctx.send(f'Loaded and added to queue: {media_file_path}')
    else:
        await ctx.send('No matching file found.')

@bot.command()
async def playmovie(ctx, *, search_query: str):
    directory_path = 'Z:\CYM\Movies'
    movie_extensions = {'.mp4', '.mkv', '.avi'}
    media_file_path = fuzzy_search_directory(search_query, directory_path, movie_extensions)

    if media_file_path:
        player.command("loadfile", media_file_path, "append-play")
        await ctx.send(f'Loaded and added to queue: {media_file_path}')
    else:
        await ctx.send('No matching file found.')

@bot.command()
async def playshow(ctx, *args: str):
    directory = 'Z:\\CYM\\Shows\\'
    show_name = ' '.join(args[:-1])
    season_episode = args[-1]

    match = re.match(r'S(\d+)E(\d+)', season_episode.upper())
    if match:
        season, episode = match.groups()
        formatted_season_episode = f'S{int(season):02d}E{int(episode):02d}'
    else:
        await ctx.send('Invalid season and episode format. Use S##E## format.')
        return

    await play_media(ctx, show_name, formatted_season_episode, directory)

@bot.command()
async def next(ctx, *args: str):
    show_to_search = ' '.join(args)
    directory = 'Z:\\CYM\\Shows\\'
    show_name, next_episode = get_next_episode(directory, show_to_search)

    if show_name and next_episode:
        await play_media(ctx, show_name, next_episode, directory)
    else:
        await ctx.send(
            f'No information found for the "{show_to_search}". Make sure you have played an episode of this show before.')


# Run the bot
bot.run(TOKEN)