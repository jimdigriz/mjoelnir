[Mjölnir](https://en.wikipedia.org/wiki/Mj%C3%B6lnir) is a contact/call centre load tester that uses [Twilio's Programmable Voice](https://www.twilio.com/docs/voice) to make calls through.

Project sponsored by [SOAS, University of London](https://www.soas.ac.uk/).

# Preflight

You need to be running either:

 * Debian 'buster' 10
 * Ubuntu 'focal' 20.04
 * Microsoft Windows 10 with [WSL 2](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

You will need to install the dependencies with:

    apt-get update
    apt-get -y install --no-install-recommends python3-virtualenv

Now set up the project with:

    virtualenv -p python3 venv
    . venv/bin/activate
    pip3 install -r requirements.txt

# Usage

    export TWILIO_ACCOUNT_SID=AC093e3266663b9b4e5a244367e49724f5
    export TWILIO_AUTH_TOKEN=bd38098ea50a99d7d0d0ebaeb89aa938
    
    python3 mjolnir.py --from +15005550006 --to +44....
