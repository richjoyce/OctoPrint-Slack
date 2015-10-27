# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import json
import requests

class SlackPlugin(octoprint.plugin.EventHandlerPlugin):

    def on_event(self, event, payload):
        if not self._settings.get(['enabled']):
            return

        if not event.startswith("Print"):
            return

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
            sys.stderr.write("An error occurred connecting to Slack:\n {}".format(e.message))

        if not res.ok:
            sys.stderr.write("An error occurred posting to Slack:\n {}".format(res.text))

