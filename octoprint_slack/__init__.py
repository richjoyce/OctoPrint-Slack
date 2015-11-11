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
                events=dict(
                    PrintStarted=True,
                    PrintFailed=True,
                    PrintCancelled=True,
                    PrintDone=True,
                    PrintPaused=False,
                    PrintResumed=False,
                )
            )

    def get_settings_version(self):
        return 1

    ## TemplatePlugin

    def get_template_configs(self):
        return [dict(type="settings", name="Slack", custom_bindings=False)]

    ## EventPlugin

    def on_event(self, event, payload):
        enabled_events = self._settings.get(['events'])
        if event in enabled_events and enabled_events[event]:
            pass
        else:
            self._logger.debug("Slack not configured for event.")
            return

        webhook_url = self._settings.get(['webhook_url'])
        if webhook_url == "":
            self._logger.exception("Slack Webhook URL not set!")
            return

        filename = os.path.basename(payload["file"])
        if payload['origin'] == 'local':
            origin = "Local"
        elif payload['origin'] == 'sdcard':
            origin = "SD Card"
        else:
            origin = payload['origin']

        username = self._settings.get(['username'])
        if username == "":
            self._logger.exception("Webhook Username not set!")
            return

        icon = self._settings.get(['icon'])
        if icon == "":
            self._logger.exception("Webhook Icon not set!")
            return

        message = {}
        message['username'] = username
        message['icon_url'] = icon
        message['attachments'] = [{}]
        attachment = message['attachments'][0]
        attachment['fields'] = []
        attachment['fields'].append( { "title": "Filename", "value": filename, "short": True } )
        attachment['fields'].append( { "title": "Origin", "value": origin, "short": True } )

        if event == "PrintStarted":
            attachment['fallback'] = "Print started! Filename: {}".format(filename)
            attachment['pretext'] = "A new print has started! :muscle:"
            attachment['color'] = "good"
        elif event == "PrintFailed":
            attachment['fallback'] = "Print failed! Filename: {}".format(filename)
            attachment['pretext'] = "Oh no! The print has failed... :rage2:"
            attachment['color'] = "danger"
        elif event == "PrintDone":
            import datetime
            import octoprint.util
            elapsed_time = octoprint.util.get_formatted_timedelta(datetime.timedelta(seconds=payload["time"]))

            attachment['fallback'] = "Print finished successfully! Filename: {}, Time: {}".format(filename, elapsed_time)
            attachment['pretext'] = "The print has finished successfully! :thumbsup:"
            attachment['color'] = "good"
            attachment['fields'].append( { "title": "Time", "value": elapsed_time, "short": True } )
        elif event == "PrintCancelled":
            attachment['fallback'] = "Print cancelled! Filename: {}".format(filename)
            attachment['pretext'] = "Uh oh... someone cancelled the print! :crying_cat_face:"
            attachment['color'] = "danger"
        elif event == "PrintPaused":
            attachment['fallback'] = "Print paused... Filename: {}".format(filename)
            attachment['pretext'] = "Printing has been paused... :sleeping:"
            attachment['color'] = "warning"
        elif event == "PrintResumed":
            attachment['fallback'] = "Print resumed! Filename: {}".format(filename)
            attachment['pretext'] = "Phew! Printing has been resumed! Back to work... :hammer:"
            attachment['color'] = "good"
        else:
            return

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

__plugin_name__ = "Slack"
__plugin_implementation__ = SlackPlugin()
