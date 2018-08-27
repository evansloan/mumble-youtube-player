import sqlite3

from bot import utils, youtube
from bot.mumblebot import MumbleBot


conn = sqlite3.connect('users.db', check_same_thread=False)


@MumbleBot.command('request')
def request_song(ctx):
    video_id = youtube.get_video_id(ctx.args)
    stream = youtube.YTStream(video_id)
    bot = ctx.bot

    if bot.playing:
        bot.add_to_queue(stream, ctx.sender.name)
    elif not bot.playing and bot.queue:
        bot.add_to_queue(stream, ctx.sender.name)
        bot.play_from_queue()
    else:
        bot.play_music(stream, ctx.sender.name)
        bot.set_comment()


@MumbleBot.command('queue')
def show_queue(ctx):
    if ctx.bot.queue:
        message = 'Songs coming up:<br>'
        for i, (name, stream) in enumerate(ctx.bot.queue):
            message += f'{i + 1}: {stream.title} - {name}<br>'
    else:
        message = 'Song queue is currently empty'
    ctx.bot.send(message)


@MumbleBot.command('stop')
def stop(ctx):
    ctx.bot.playing = False
    ctx.bot.thread.kill()
    ctx.bot.thread = None
    ctx.bot.song = None
    ctx.bot.set_comment()


@MumbleBot.command('skip')
def skip(ctx):
    if ctx.bot.queue:
        ctx.bot.play_from_queue()
    else:
        ctx.bot.send('Queue is empty...')
        stop()


@MumbleBot.command('volume')
def set_volume(ctx):
    error = ('Use a number between 1 and 10 to set volume<br>'
             'ex: <span style="font-family: Courier;">!volume 5</span>')
    try:
        if int(ctx.args) >= 0 and int(ctx.args) <= 10:
            ctx.bot.volume = int(ctx.args) / 10
        else:
            ctx.bot.send(error)
            return
    except ValueError:
        ctx.bot.send(error)
        return
    ctx.bot.send(f'Volume is at {ctx.bot.volume * 10}')
    ctx.bot.set_comment()


@MumbleBot.command('move')
def move_users(ctx):
    if ctx.bot.locked:
        ctx.sender.send_message('<br>I am currently locked to this channel')
        ctx.bot.send('I am currently locked to this channel')
        return
    if ctx.args:
        if ctx.args.split()[0].lower() == 'all':
            # move all users in a channel to a specific channel
            channel = ctx.args.split(' ', 1)[1].strip()
            current_channel = ctx.bot.mumble.channels[ctx.bot.me.channel_id]
            new_channel = ctx.bot.mumble.channels.find_by_name(channel)
            for user in current_channel.users:
                user.move(channel_id=new_channel.channel_id)
        else:
            # move the bot to a specific channel
            ctx.bot.mumble.channels.find_by_name(ctx.args).move()
    else:
        # move the bot to the channel of the sender
        ctx.bot.mumble.channels[ctx.sender.channel_id].move()


@MumbleBot.command('lock', restricted=True)
def lock(ctx):
    is_locked = not ctx.bot.locked
    if is_locked:
        ctx.bot.send('I am now locked to this channel')
    else:
        ctx.bot.send('I am now unlocked')

    ctx.bot.locked = is_locked


@MumbleBot.command('mod', restricted=True)
def mod(ctx):
    c = conn.cursor()
    if utils.is_mod(ctx.args):
        ctx.bot.send(f'{ctx.args} is already a mod')
    else:
        if utils.user_exists(ctx.args, ctx.bot):
            c.execute('INSERT INTO mods VALUES (?)', (ctx.args,))
            conn.commit()
            ctx.bot.send(f'{ctx.args} added as a mod')
        else:
            ctx.bot.send(f'Cannot find user {ctx.args}')


@MumbleBot.command('ignore', restricted=True)
def ignore(ctx):
    c = conn.cursor()
    if utils.user_exists(ctx.args, ctx.bot):
        if not utils.is_ignored(ctx.args):
            c.execute('INSERT INTO ignored VALUES (?)', (ctx.args,))
            conn.commit()
            ctx.bot.send(f'{ctx.args} ignored')
        else:
            ctx.bot.send(f'{ctx.args} is already ignored')
    else:
        ctx.bot.send(f'Cannot find user {ctx.args}')
