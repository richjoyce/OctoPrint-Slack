# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import json
import requests

class SlackPlugin(octoprint.plugin.SettingsPlugin,
                  octoprint.plugin.TemplatePlugin,
                  octoprint.plugin.EventHandlerPlugin):

    ## SettingsPlugin

    def get_settings_defaults(self):
        return dict(
                enabled=False,
                webhook_url="",
                events=dict(
                    PrintStarted=True,
                    PrintDone=True,
                    PrintFailed=True,
                    PrintPaused=False,
                    PrintResumed=False,
                    PrintCancelled=True
                )
            )

    def get_settings_version(self):
        return 1

    ## TemplatePlugin
    def get_template_configs(self):
        return [dict(type="settings", name="Slack", custom_bindings=False)]

    ## EventPlugin

    def on_event(self, event, payload):
        if not self._settings.get(['enabled']):
            return

        enabled_events = self._settings.get(['events'])
        if event in enabled_events and enabled_events[event]:
            pass
        else:
            return

        webhook_url = self._settings.get(['webhook_url'])
        if webhook_url = "":
            self._logger.exception("Slack Webhook URL not set!")

        filename = os.path.basename(payload["file"])
        if payload['origin'] == 'local':
            origin = "Local"
        elif payload['origin'] == 'sdcard':
            origin = "SD Card"
        else:
            origin = payload['origin']

        message = {}
        message['username'] = "OctoPrint"
        message['icon_url'] = "http://octoprint.org/assets/img/logo.png"
        message['attachments'] = [{}]
        attachment = message['attachments'][0]
        attachment['fields'] = []
        attachment['fields'].append( { "title": "Filename", "value": filename, "short": True } )
        attachment['fields'].append( { "title": "Origin", "value": origin, "short": True } )

        if event == "PrintStarted":
            attachment['fallback'] = "Print started! Filename: {}".format(filename)
            attachment['text'] = "Print started!"
            attachment['color'] = "good"
        elif event == "PrintFailed":
            attachment['fallback'] = "Print failed! Filename: {}".format(filename)
            attachment['text'] = "Print failed!"
            attachment['color'] = "danger"
        elif event == "PrintDone":
            attachment['fallback'] = "Print finished successfully! Filename: {}".format(filename)
            attachment['text'] = "Print finished!"
            attachment['color'] = "good"

            import datetime
            import octoprint.util
            elapsed_time = octoprint.util.get_formatted_timedelta(datetime.timedelta(seconds=payload["time"]))

            attachment['fields'].append( { "title": "Time", "value": elapsed_time, "short": True } )
        elif event == "PrintCancelled":
            attachment['fallback'] = "Print cancelled! Filename: {}".format(filename)
            attachment['text'] = "Print cancelled!"
            attachment['color'] = "danger"
        elif event == "PrintPaused":
            attachment['fallback'] = "Print paused... Filename: {}".format(filename)
            attachment['text'] = "Print paused..."
            attachment['color'] = "warning"
        elif event == "PrintResumed":
            attachment['fallback'] = "Print resumed! Filename: {}".format(filename)
            attachment['text'] = "Print resumed!"
            attachment['color'] = "good"
        else:
            return

        try:
            res = requests.post(webhook_url, data=json.dumps(message))
        except Exception, e:
            self._logger.exception("An error occurred connecting to Slack:\n {}".format(e.message))
            return

        if not res.ok:
            self._logger.exception("An error occurred posting to Slack:\n {}".format(res.text))
            return

        self._logger.info("Posted event to Slack!")

