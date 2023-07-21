import discord
from discord.ext import commands
from python_mpv_jsonipc import MPV
from dotenv import load_dotenv
import os
import random
import glob
import re
from fuzzywuzzy import fuzz, process
import asyncio
import json

# Get the absolute directory path of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Load config file from the script's directory
config_path = os.path.join(script_directory, 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Load config variables (directory locations)
tv_show_directory = config["tv_show_directory"]
movie_directory = config["movie_directory"]
music_video_directory = config["music_video_directory"]
bumper_directory = config["bumper_directory"]
intermission_directory = config["intermission_directory"]
movie_list = config["movie_list"]
tv_show_list = config["tv_show_list"]
recently_added_list = config["recently_added_list"]


# Function for loading media URLs into mpv queue
def add_media_url(mpv, url):
    # Use regular expressions to check if the URL is in a valid format
    url_pattern = re.compile(r'^https?://')
    if not url_pattern.match(url):
        return False  # Invalid URL format, return False

    # Use mpv's `loadfile` command to append the URL to the queue
    mpv.command('loadfile', url, 'append-play')
    return True


# function for loading media files into mpv queue
def add_bumpers(mpv, directory, extensions):
    bumpers = glob.glob(os.path.join(directory, '*'))
    bumpers = [bumper for bumper in bumpers if os.path.splitext(bumper)[1].lower() in extensions]
    random.shuffle(bumpers)
    selected_bumpers = bumpers[:1]  # Select the first bumper from the shuffled list
    for bumper in selected_bumpers:
        mpv.command('loadfile', bumper, 'append-play')

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
        # Load bumpers
        add_bumpers(player, bumper_directory, ['.mp4', '.mkv', '.avi'])
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
async def test(ctx):
    response = "Fly, fly fly."
    await ctx.send(response)


@bot.command()
async def recentlyadded(ctx):
    with open(recently_added_list, 'rb') as f:
        file = discord.File(f)
        await ctx.send(file=file)


@bot.command()
async def listmovies(ctx):
    with open(movie_list, 'rb') as f:
        file = discord.File(f)
        await ctx.send(file=file)


@bot.command()
async def listshows(ctx):
    with open(tv_show_list, 'rb') as f:
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


@bot.command(aliases=['clear', 'c'])
async def clearplaylist(ctx):
    player.playlist_clear()
    await ctx.send("Cleared the media player's playlist.")


@bot.command(aliases=['timeleft', 't'])
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
async def http(ctx, *, url: str):
    # Call the function to load the URL into the MPV queue
    success = add_media_url(player, url)
    if success:
        await ctx.send(f'Successfully added URL to the queue: {url}')
    else:
        await ctx.send('Invalid URL format. Please provide a valid URL starting with "http://" or "https://".')



@bot.command(aliases=['pmv', 'playmv', 'musicvideo'])
async def playmusicvideo(ctx, *, search_query: str = None):
    extensions = ['.mp4', '.webm', '.avi']
    if search_query:
        media_file_path = fuzzy_search_directory(search_query, music_video_directory, extensions)
        print(f"Searching for query: {search_query}")  # Debug line to see the searched query
    else:
        media_file_path = get_random_file(music_video_directory, extensions)

    print(f"Selected media file path: {media_file_path}")  # Debug line to see the selected media file path

    if media_file_path:
        player.command("loadfile", media_file_path, "append-play")
        await ctx.send(f'Loaded and added to queue: {media_file_path}')
    else:
        await ctx.send('No matching file found.')


@bot.command(aliases=['pi'])
async def playintermission(ctx, *, search_query: str = None):
    intermission_extensions = {'.mp4', '.mkv', '.avi'}

    if search_query:
        media_file_path = fuzzy_search_directory(search_query, intermission_directory, intermission_extensions)
    else:
        media_file_path = get_random_file(intermission_directory, intermission_extensions)

    if media_file_path:
        player.command("loadfile", media_file_path, "append-play")
        await ctx.send(f'Loaded and added to queue: {media_file_path}')
    else:
        await ctx.send('No matching file found.')


@bot.command(aliases=['pm'])
async def playmovie(ctx, *, search_query: str):
    movie_extensions = {'.mp4', '.mkv', '.avi'}
    media_file_path = fuzzy_search_directory(search_query, movie_directory, movie_extensions)

    if media_file_path:
        player.command("loadfile", media_file_path, "append-play")
        await ctx.send(f'Loaded and added to queue: {media_file_path}')
    else:
        await ctx.send('No matching file found.')


@bot.command(aliases=['ps', 'show'])
async def playshow(ctx, *args: str):
    '''
    This command plays a specific episode of a show. It expects the show name and specific episode 
    format (in the form S##E##) as arguments. The episode is then searched in the local media directory 
    and played if found.

    :param ctx: The context in which the command was called.
    :param args: The arguments given to the command. The first to penultimate are joined together to form 
    the show name, while the last represents the season and episode number.
    '''
    show_name = ' '.join(args[:-1])
    season_episode = args[-1] 

    match = re.match(r'S(\d+)E(\d+)', season_episode.upper())
    if match:
        season, episode = match.groups()
        formatted_season_episode = f'S{int(season):02d}E{int(episode):02d}'
    else:
        await ctx.send('Invalid season and episode format, use S##E## format (e.g. S02E07)')
        return
     
    # Add show name error checking here
    # For example:
    # if show_name not in tv_show_directory:
    #     await ctx.send('Show not found.')
    #     return

    print(f'Receiving command to play {show_name} {formatted_season_episode}')
    await play_media(ctx, show_name, formatted_season_episode, tv_show_directory)
    print('Command executed successfully.')


@bot.command()
async def next(ctx, *args: str):
    if not args:
        # If no arguments are provided, execute the skip command
        await skip(ctx)
        return
    show_to_search = ' '.join(args)
    directory = 'Z:\\CYM\\Shows\\'
    show_name, next_episode = get_next_episode(directory, show_to_search)

    if show_name and next_episode:
        await play_media(ctx, show_name, next_episode, directory)
    else:
        await ctx.send(
            f'No information found for the "{show_to_search}". Make sure you have played an episode of this show before.')

# Global flag variable to track if the intro file has played
intro_played = False

# watch mpv player for if it runs out of files to play
# if it does, then play a random file from specified directory
async def watch_mpv_player():
    global intro_played  # Access the global flag variable

    while True:
        # Check if the MPV player is idle
        if player.command("get_property", "idle-active"):
            # Check if the intro file has played
            if intro_played:
                # Get a random file from the specified directory
                directory = 'Z:/CYM/Shows/Ambient.Swim.S01.1080p.WEBRip.DD5.1.x264-KOGi[rartv]'
                extensions = ['.mp4', '.mkv', '.avi']
                random_file = get_random_file(directory, extensions)

                # Load the random file into the MPV player
                if random_file:
                    player.loadfile(random_file)
                    print(f"Loaded random file: {random_file}")
            else:
                # Play the intro file
                intro_file = 'Z:/CYM/tokyo-intermissions/burushiti-please-wait-1.mp4'
                player.loadfile(intro_file)
                print(f"Loaded intro file: {intro_file}")

                # Set the intro played flag to True
                intro_played = True

        # Delay between each check (adjust the duration as per your preference)
        await asyncio.sleep(10)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    # Start watching the MPV player
    bot.loop.create_task(watch_mpv_player())


# Run the bot
bot.run(TOKEN)