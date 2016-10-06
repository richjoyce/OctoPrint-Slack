# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import os
import json
import requests

class SlackPlugin(octoprint.plugin.SettingsPlugin,
                  octoprint.plugin.TemplatePlugin,
                  octoprint.plugin.EventHandlerPlugin):

    ## SettingsPlugin

    def get_settings_defaults(self):
        return dict(
                webhook_url="",
                print_events=dict(
                    PrintStarted=dict(
                        Enabled=True,
                        Message="A new print has started! :muscle:",
                        Fallback="Print started! Filename: {filename}",
                        Color="good",
                        ),
                    PrintFailed=dict(
                        Enabled=True,
                        Message="Oh no! The print has failed... :rage2:",
                        Fallback="Print failed! Filename: {filename}",
                        Color="danger",
                        ),
                    PrintCancelled=dict(
                        Enabled=True,
                        Message="Uh oh... someone cancelled the print! :crying_cat_face:",
                        Fallback="Print cancelled! Filename: {filename}",
                        Color="danger",
                        ),
                    PrintDone=dict(
                        Enabled=True,
                        Message="Print finished successfully! :thumbsup:",
                        Fallback="Print finished! Filename: {filename}, Time: {time}",
                        Color="good",
                        ),
                    PrintPaused=dict(
                        Enabled=True,
                        Message="Printing has been paused... :sleeping:",
                        Fallback="Print paused... Filename: {filename}",
                        Color="warning",
                        ),
                    PrintResumed=dict(
                        Enabled=True,
                        Message="Phew! Printing has been resumed! Back to work... :hammer:",
                        Fallback="Print resumed! Filename: {filename}",
                        Color="good",
                        ),
                    ),
                )

    def get_settings_version(self):
        return 3

    def on_settings_migrate(self, target, current):
        if current == 1 or current == 2:
            events = self._settings.get(['events'])
            # migrate events
            print_events = self._settings.get(['print_events'])
            if events:
                for event in events:
                    if not events[event]:
                        self._settings.set_boolean(['print_events',event,'Enabled'], False)
            # remove old settings if there
            self._settings.set(['enabled'], None)
            self._settings.set(['events'], None)
            # clean up old fallback messages from <1.2.7 oversaving
            for event in print_events:
                try:
                    self._settings.remove(['print_events',event,'Fallback'])
                except ValueError:
                    # Remove fallback for bug in 1.2.8 and earlier
                    self._settings.settings.remove(self._settings._prefix_path(['print_events', event, 'Fallback']))

    ## TemplatePlugin

    def get_template_configs(self):
        return [dict(type="settings", name="Slack", custom_bindings=False)]

    ## EventPlugin

    def on_event(self, event, payload):
        events = self._settings.get(['print_events'], merged=True)

        if event in events and events[event] and events[event]['Enabled']:

            webhook_url = self._settings.get(['webhook_url'])
            if not webhook_url:
                self._logger.exception("Slack Webhook URL not set!")
                return

            filename = os.path.basename(payload["file"])
            if payload['origin'] == 'local':
                origin = "Local"
            elif payload['origin'] == 'sdcard':
                origin = "SD Card"
            else:
                origin = payload['origin']

            message = {}

            ## bot display settings

            ## if no username is set, it will default to the webhook username
            username = self._settings.get(['bot_username'])
            if username:
                message['username'] = username

            ## if an icon is set, use that. if not, use the emoji.
            ## if neither are set, it will default to the webhook icon/emoji
            icon_url = self._settings.get(['bot_icon_url'])
            icon_emoji = self._settings.get(['bot_icon_emoji'])
            if icon_url:
                message['icon_url'] = icon_url
            elif icon_emoji:
                message['icon_emoji'] = icon_emoji

            ## if a channel is set, use that. if not, just don't send any
            bot_channel = self._settings.get(['bot_channel'])
            if bot_channel:
                if bot_channel[0] != '#'
                    bot_channel = '#' + bot_channel
                message['channel'] = bot_channel

            ## message settings
            message['attachments'] = [{}]
            attachment = message['attachments'][0]
            attachment['fields'] = []
            attachment['fields'].append( { "title": "Filename", "value": filename, "short": True } )
            attachment['fields'].append( { "title": "Origin", "value": origin, "short": True } )

            ## event settings
            event = self._settings.get(['print_events', event], merged=True)

            import datetime
            import octoprint.util
            if "time" in payload and payload["time"]:
                elapsed_time = octoprint.util.get_formatted_timedelta(datetime.timedelta(seconds=payload["time"]))
            else:
                elapsed_time = ""

            attachment['fallback'] = event['Fallback'].format(**{'filename': filename, 'time':elapsed_time})
            attachment['pretext'] = event['Message']
            attachment['color'] = event['Color']
            if elapsed_time != "":
                attachment['fields'].append( { "title": "Time", "value": elapsed_time, "short": True } )

            self._logger.debug("Attempting post of Slack message: {}".format(message))
            try:
                res = requests.post(webhook_url, data=json.dumps(message))
            except Exception, e:
                self._logger.exception("An error occurred connecting to Slack:\n {}".format(e.message))
                return

            if not res.ok:
                self._logger.exception("An error occurred posting to Slack:\n {}".format(res.text))
                return

            self._logger.debug("Posted event successfully to Slack!")

        else:
            self._logger.debug("Slack not configured for event.")
            return

__plugin_name__ = "Slack"
__plugin_implementation__ = SlackPlugin()
