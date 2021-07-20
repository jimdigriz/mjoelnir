#!/usr/bin/env python3

import argparse
import logging
import os
import pathlib
import random
import sched
import socket
import sys
import time
import token_bucket
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# using 'required' ignores 'default'
arg_account_sid = {'default': os.getenv('TWILIO_ACCOUNT_SID')} if 'TWILIO_ACCOUNT_SID' in os.environ else {'required': True}
arg_auth_token = {'default': os.getenv('TWILIO_AUTH_TOKEN')} if 'TWILIO_AUTH_TOKEN' in os.environ else {'required': True}

parser = argparse.ArgumentParser(description='Mjölnir, a contact/call centre load tester that uses Twilio.')
parser.add_argument('--debug', dest='log_level', default=logging.INFO, action='store_const', const=logging.DEBUG, help='enable verbose debugging')
parser.add_argument('--twilio-account-sid', type=str, help='Twilio Account SID (default: env TWILIO_ACCOUNT_SID)', **arg_account_sid)
parser.add_argument('--twilio-auth-token', type=str, help='Twilio Auth Token (default: env TWILIO_AUTH_TOKEN', **arg_auth_token)
parser.add_argument('--from', type=str, dest='from_', required=True, help='Number you want to state you are calling from.')
parser.add_argument('--to', type=str, required=True, help='Number you want to dial.')
parser.add_argument('--calls-max', type=int, default=10, help='ceiling limit of simulateous calls')
parser.add_argument('--call-duration', type=int, default=120, help='call duration before hanging up in seconds')
parser.add_argument('--call-duration-fuzz', type=int, default=20, help='call duration fuzz percentage')
parser.add_argument('--rate-limit', type=float, default=10.0, help='rate limit (calls per second)')
parser.add_argument('--rate-limit-burst', type=int, default=1, help='rate limit burst')
parser.add_argument('--stats-interval', type=float, default=5.0, help='interval in seconds to print statistics')

args = parser.parse_args()

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=args.log_level)
logger = logging.getLogger()

if not (args.calls_max >= 1 and args.calls_max <= 5000):
    logger.critical("calls-max must be between 1 and 5000 inclusive")
    sys.exit(1)
if args.call_duration < 1:
    logger.critical("calls-duration must be greater than zero")
    sys.exit(1)
elif args.call_duration < 30:
    logger.warning("calls-duration should be greater than 30 seconds")
if not (args.call_duration_fuzz >= 0 and args.call_duration_fuzz <= 100):
    logger.critical("calls-duration-fuzz must be a percentage between 0 and 100 inclusive")
    sys.exit(1)
if args.call_duration_fuzz >= 30 or (args.call_duration - args.call_duration * (args.call_duration_fuzz / 100)) < 30:
    logger.warning("calls-duration-fuzz is large and possibly impacting the lower end of call-duration")
if not (args.rate_limit >= 0.00):
    logger.critical("rate-limit must be greater than 0.0")
    sys.exit(1)
if args.rate_limit_burst < 1:
    logger.critical("rate-limit-burst must be greater or equal to 1")
    sys.exit(1)

csids = set()
call_scheduled = False;
stats_dropped = 0
stats_completed = 0

scheduler = sched.scheduler(time.time, time.sleep)

key = 'key'
storage = token_bucket.MemoryStorage()
limiter = token_bucket.Limiter(args.rate_limit, args.rate_limit_burst, storage)

client = Client(args.twilio_account_sid, args.twilio_auth_token)
client.http_client.logger.setLevel(logging.WARNING)

running = True

program = pathlib.Path(__file__).stem
hostname = socket.gethostname()
username = os.getlogin()
pid = os.getpid()
queue_name = ':'.join([program,hostname,username,str(pid)])
queue = client.queues.create(friendly_name=queue_name, max_size=int(args.calls_max * 1.1))
logger.info(f"created call queue '{queue_name}'")

def call_complete(csid):
    global stats_completed

    # simpler than tracking and cancelling events
    if not csid in csids:
        return

    logger.debug(f'call completed {csid}')

    client.calls(csid).update(status='completed')
    csids.remove(csid)

    if call_scheduled == False:
        call_schedule()

    stats_completed += 1

def call_create():
    resp = VoiceResponse()
    resp.enqueue(queue_name)

    call = client.calls.create(to = args.to, from_ = args.from_, twiml = resp)
    csids.add(call.sid)

    delta = args.call_duration * (args.call_duration_fuzz / 100.0);
    duration = random.uniform(args.call_duration - delta, args.call_duration + delta)
    logger.info(f'call {call.sid} created, scheduling hangup for {duration:.2f}s')

    scheduler.enter(duration, 1, call_complete, argument=(call.sid,))

def call_schedule():
    global call_scheduled

    call_scheduled = False

    if not running:
        return

    if len(csids) < args.calls_max:
        if limiter.consume(key):
            delay = 0.0
            call_create()
        else:
            delay = 1.0 / args.rate_limit
            logger.debug(f'call rate limited (sleeping for {delay:.2f}s)')
        scheduler.enter(delay, 1, call_schedule)
        call_scheduled = True
    else:
        logger.debug('reached maximum call ceiling, skipping scheduling')
call_schedule()

def stats_schedule():
    global stats_dropped

    members = queue.members.list()
    queued = set(map(lambda r: r.call_sid, members))
    diff = csids - queued

    for csid in diff:
        call = client.calls(csid).fetch()
        if not call.status in ['queued','ringing','in-progress']:
            csids.remove(csid)
            stats_dropped += 1
            if call_scheduled == False:
                call_schedule()

    logger.info(f'statistics active={len(csids)} completed={stats_completed} dropped={stats_dropped}')

    scheduler.enter(args.stats_interval, 1, stats_schedule)
stats_schedule()

while running:
    try:
        delay = scheduler.run(blocking=False)
        time.sleep(delay)
    except KeyboardInterrupt:
        logger.warning('Keyboard interupt')
        running = False

logger.info(f'ending {len(csids)} calls')
csids_orig = csids.copy()
for csid in csids_orig:
    call_complete(csid)
logger.info('waiting for calls to complete')
for csid in csids_orig:
    while True:
        call = client.calls(csid).fetch()
        if not call.status in ['queued','ringing','in-progress']:
            break
        logger.debug('sleeping...')
        time.sleep(1)
logger.info('deleting queue')
queue.delete()

logger.info(f'statistics active={len(csids)} completed={stats_completed} dropped={stats_dropped}')

sys.exit(0)
