#!/bin/bash
# Make sure we're not confused by old, incompletely-shutdown httpd
# context after restarting the container. httpd won't start correctly
# if it thinks it is already running.

/usr/bin/supervisord -n -c /etc/supervisord.conf
