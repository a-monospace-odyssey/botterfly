# Introduction

Botterfly is a Python-based bot that allows you to queue and play media files, such as movies, TV shows, music videos, and intermission files, in MPV media player and using text commands from a Discord server to control it. This bot is designed to be simple to use and can be easily set up on your own Discord server.

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Commands](#commands)
- [Contributing](#contributing)
- [License](#license)

## Getting Started

### Prerequisites

- Python 3.7 or higher installed on your system.
- FFmpeg/mpv installed on your system. (For playing local media files)
- Discord bot token obtained from the Discord Developer Portal. (See https://discordpy.readthedocs.io/en/stable/discord.html for more details)

### Installation

Clone this repository to your local machine.

`git clone https://github.com/a-monospace-odyssey/botterfly.git`

And change directory `cd` into the botterfly directory.

`cd botterfly`

Install the required dependencies using `pip`.

`pip install -r requirements.txt`

Make sure you have FFmpeg installed on your system. If not, you can download it from the official website (https://www.ffmpeg.org/) and add it to your system's PATH.

# Configuration

Alter the example configuration file `config.json` to your liking and save it.

Set your Discord bot token in the environment variable DISCORD_TOKEN. You can create a .env file in the root directory and add the token there.

`echo "DISCORD_TOKEN=your_discord_bot_token_here" > .env`
    
Run the bot using the following command.

`python botterfly.py`

# Commands

Use the command prefix $ to interact with the bot. 

For example: $playshow Game of Thrones S01E01. 

Use $help to view the available commands and their descriptions.

# Contributing

Contributions are welcome! If you find any issues or have suggestions for improvement, feel free to open an issue or submit a pull request.