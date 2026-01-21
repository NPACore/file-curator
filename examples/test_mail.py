#!/usr/bin/env python3
import os
import re
from subprocess import run
from shim_notify import send_email, load_toml_config

## test account
# settings = load_toml_config("shim_settings.toml")["emails"][1]
host = "128.147.59.133"
sender = "noreply@mrctr.upmc.edu"
to = "mrtechs@mrctr.upmc.edu"

## report on who we are
ip = run(["hostname", "-i"], capture_output=True,text=True).stdout.strip()
if m := re.search(r'[.0-9]{7,}', ip):
    ip = m.group(0)
msg = f"Email from {os.environ.get('HOSTNAME')} ({ip}) to {host}"

## send
print(f"Sending to {to} via {host}:\n\t{msg}")
send_email(subject="Test of email notification software",
           body=msg, sender=sender, recipient=to, host=host)

## fetch
# first try telnet, then full imap sync into ~/Maildir/mrrc/Inbox
# use config mbsync file, not tracked
print("####\nTesting IMAP connection")
run('(echo "a001 CAPABILITY"; sleep 1; echo "a002 login mrtechs `pass mrrc-email`"; sleep 10) | telnet 128.147.59.133 143', shell=True)

print("# Fetching all IMAP Mail")
run(["guix","shell", "isync", "--", "mbsync", "-c", "mbsyncrc_mrrc", "-a", "-V"])
