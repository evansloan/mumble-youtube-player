import audioop
import configparser
import logging
import os
import subprocess
import time

from pymumble import mumble

from bot import utils


class MumbleBot:
    commands = {}

    def __init__(self):
        self._base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

        self.logger = logging.getLogger('mumble-music')
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(os.path.join(self._base_dir, 'logs/error.log'))
        fh.setLevel(logging.ERROR)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(module)s.py - line %(lineno)d: %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(os.path.join(self._base_dir, 'config/config.ini'))

        self.host = self.config.get('server-info', 'host')
        self.port = self.config.getint('server-info', 'port')
        self.name = self.config.get('bot-info', 'name')
        self.cert = self.config.get('bot-info', 'cert')
        self.channel = self.config.get('bot-info', 'channel')

        self.thread = None
        self.playing = False
        self.song = None
        self.queue = []
        self.volume = 0.5
        self.locked = False

        self.mumble = mumble.Mumble(self.host, user=self.name, port=self.port, certfile=self.cert, reconnect=True)
        self.mumble.callbacks.set_callback('text_received', self.message_recieved)

        self.mumble.set_codec_profile('audio')
        self.mumble.start()
        self.mumble.is_ready()
        self.me = self.mumble.users.myself

        if self.channel:
            self.mumble.channels.find_by_name(self.channel).move()

        self.mumble.set_bandwidth(200000)
        self.loop()

    @classmethod
    def command(cls, name, restricted=False):
        def wrapper(func):
            cls.commands[name.lower()] = {
                'func': func,
                'restricted': restricted,
            }
            return func
        return wrapper

    def message_recieved(self, text):
        message = utils.remove_html_markup(text.message)
        sender = self.mumble.users[text.actor]

        if message[0] == '!':
            message = message[1:].split(' ', 1)
            command = message[0].lower().strip()
            command_args = None
            if len(message) > 1:
                command_args = ' '.join(message[1:]).strip()

            ctx = Context(command_args, sender, self)
            self.logger.info(f'{command} {command_args} - {sender.name}')

            try:
                if utils.is_ignored(sender.name):
                    sender.send_message('<br>You are currently ignored and cannot use commands')
                    return

                if self.commands[command]['restricted'] and not utils.is_mod(sender.name):
                    self.send('You must be a moderator to use this command')
                    return

                self.commands[command]['func'](ctx)
            except KeyError:
                self.send(f'Command {command} does not exist')

    def send(self, message, channel=None):
        if channel is None:
            channel = self.mumble.channels[self.me.channel_id]
        channel.send_text_message(f'<br>{message}')

    def set_comment(self):
        comment = f'<h1 style="color: red; font-size: 18px;">Now playing: {self.song}</h1>'
        comment += f'<h2 style="color: yellow; font-size: 16px;">Volume: {self.volume * 10}</h2>'
        with open(os.path.join(self._base_dir, 'config/comment.html'), 'r') as f:
            comment += f.read()
        self.me.comment(comment)

    def add_to_queue(self, stream, user):
        for name, link in self.queue:
            if user == name:
                self.send(f'You already have a song in the queue')
                return

        self.queue.append((user, stream))
        self.send(f'{stream.title} added to the queue!'
                  f'<br>There are {len(self.queue) - 1} songs ahead of yours')

    def play_from_queue(self):
        user = self.queue[0][0]
        stream = self.queue[0][1]

        self.play_music(stream, user)
        self.set_comment()
        del self.queue[0]

    def play_music(self, stream, user):
        self.thread = subprocess.Popen(stream.audio, stdout=subprocess.PIPE, bufsize=480)
        self.playing = True
        self.send(f'Now playing: <a href="{stream.video_url}">{stream.title}</a><br>'
                  f'Requested by: {user}<br>'
                  f'Duration: {stream.duration}')
        self.song = stream.title

    # this is a mess
    def loop(self):
        while self.mumble.is_alive():
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
                            self.song = None
                            self.set_comment()
                        time.sleep(0.01)
                except AttributeError:
                    self.playing = False
                    self.song = None
                    self.set_comment()
            else:
                time.sleep(1)

        while self.mumble.sound_output.get_buffer_size() > 0:
            time.sleep(0.01)
        time.sleep(0.5)


class Context:
    def __init__(self, args, sender, bot):
        self.args = args
        self.sender = sender
        self.bot = bot
