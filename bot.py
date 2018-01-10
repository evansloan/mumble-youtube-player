import audioop
import configparser
import os
import subprocess
import time
from datetime import datetime

import youtube
from pymumble import pymumble


class MumbleBot:
    def __init__(self):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config/config.ini'))

        self.host = self.config.get('server-info', 'host')
        self.port = self.config.getint('server-info', 'port')
        self.name = self.config.get('bot-info', 'name')
        self.cert = self.config.get('bot-info', 'cert')
        self.channel = self.config.get('bot-info', 'channel')

        self.thread = None
        self.playing = False
        self.queue = []
        self.volume = 0.5
        self.votes = 0

        self.mumble = pymumble.Mumble(self.host, user=self.name, port=self.port, certfile=self.cert, reconnect=True)
        self.mumble.callbacks.set_callback('text_received', self.message_recieved)

        self.mumble.set_codec_profile('audio')
        self.mumble.start()
        self.mumble.is_ready()
        self.me = self.mumble.users.myself

        if self.channel:
            self.mumble.channels.find_by_name(self.channel).move()

        self.mumble.set_bandwidth(200000)
        self.loop()

    def message_recieved(self, text):
        message = text.message
        sender = self.mumble.users[text.actor]

        if message[0] == '!':
            message = message[1:].split(' ', 1)
            command = message[0].lower().strip()
            command_args = ''
            if len(message) > 1:
                command_args = ' '.join(message[1:]).strip()
        else:
            return

        timestamp = datetime.now()
        print(f'{timestamp}: {command} {command_args} - {sender.name}')
        self.parse_message(command, command_args, sender)

    def parse_message(self, command, command_args, sender):
        if command == 'move':
            self.move_users(sender, command_args)
        elif command == 'play':
            self.load_youtube_audio(sender, video_id=command_args)
        elif command == 'request':
            self.load_youtube_audio(sender, video_title=command_args)
        elif command == 'queue':
            self.show_queue()
        elif command == 'stop':
            self.stop()
        elif command == 'skip':
            self.skip()
        elif command == 'volume':
            self.set_volume(command_args)

    def send(self, message, channel=None):
        if channel is None:
            channel = self.mumble.channels[self.me.channel_id]
        channel.send_text_message(message)

    def set_comment(self, song):
        header = f'<h1 style="color: red; font-size: 16px;">Now playing: {song}</h1><br>'
        self.me.comment(header)

    def load_youtube_audio(self, sender, video_id=None, video_title=None):
        if video_title:
            video_id = youtube.get_video_id(video_title)

        if self.playing:
            self.add_to_queue(video_id, sender)
        elif not self.playing and self.queue:
            self.add_to_queue(video_id, sender)
            self.play_from_queue()
        else:
            self.play_music(youtube.get_audio_stream(video_id))
            song_title = youtube.get_video_title(video_id)
            self.set_comment(song_title)
            self.send(f'<br>Now playing: {song_title}')

    def add_to_queue(self, video_id, sender):
        for name, link in self.queue:
            if sender.name == name:
                self.send(f'You already have a song in the queue')
                return

        self.queue.append((sender.name, video_id))
        song_title = youtube.get_video_title(video_id)
        self.send(f'<br>{song_title} added to queue!<br>There are {len(self.queue) - 1} songs ahead of yours')

    def play_from_queue(self):
        user = self.queue[0][0]
        link = self.queue[0][1]

        self.play_music(youtube.play_youtube_audio(link))
        song_title = youtube.get_video_title(link)
        self.set_comment(song=song_title)
        self.send(f'<br>Now playing {song_title}<br>Requested by: {user}')
        del self.queue[0]

    def play_music(self, command):
        self.thread = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=480)
        self.playing = True

    def show_queue(self):
        if self.queue:
            message = '<br>Songs coming up:<br>'
            for name, link in self.queue:
                song_name = youtube.get_video_title(link)
                message += f'{song_name}<br>'
        else:
            message = '<br>Song queue is currently empty'

        self.send(message)

    def stop(self):
        self.playing = False
        self.thread.kill()
        self.thread = None
        self.set_comment('')

    def skip(self):
        if self.queue:
            self.play_from_queue()
        else:
            self.send('<br>Queue is empty...')
            self.stop()

    def set_volume(self, arg):
        if arg.lower() == 'up':
            self.volume += 0.1
        elif arg.lower() == 'down' and self.volume > 0:
            self.volume -= 0.1

        self.send(f'Volume is at {self.volume:{.2}}')

    def move_users(self, sender, args):
        if args:
            if args.split()[0] == 'all':
                # move all users in a channel to a specific channel
                channel = args.split(' ', 1)[1].strip()
                current_channel = self.mumble.channels[self.me.channel_id]
                new_channel = self.mumble.channels.find_by_name(channel)
                for user in current_channel.users:
                    user.move(channel_id=new_channel.channel_id)
            else:
                # move the bot to a specific channel
                self.mumble.channels.find_by_name(args).move()
        else:
            # move the bot to the channel of the sender
            self.mumble.channels[sender.channel_id].move()

    # this is a mess
    def loop(self):
        while self.mumble.isAlive():
            if self.playing:
                while self.mumble.sound_output.get_buffer_size() > 0.5 and self.playing:
                    time.sleep(0.01)
                try:
                    raw_music = self.thread.stdout.read(480)
                    if raw_music:
                        self.mumble.sound_output.add_sound(audioop.mul(raw_music, 2, self.volume))
                    else:
                        if len(self.queue) > 0:
                            self.play_from_queue()
                        else:
                            self.playing = False
                            self.set_comment('')
                        time.sleep(0.01)
                except AttributeError:
                    self.playing = False
                    self.set_comment('')
            else:
                time.sleep(1)

        while self.mumble.sound_output.get_buffer_size() > 0:
            time.sleep(0.01)
        time.sleep(0.5)
