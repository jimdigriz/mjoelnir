[Mjölnir](https://en.wikipedia.org/wiki/Mj%C3%B6lnir) is a contact/call centre load tester that uses [Twilio's Programmable Voice](https://www.twilio.com/docs/voice) to make calls through.

Project sponsored by [SOAS, University of London](https://www.soas.ac.uk/).

# Preflight

You need to be running either:

 * Debian 'buster' 10
 * Ubuntu 'focal' 20.04
 * Microsoft Windows 10 with [WSL 2](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

You will need to install the dependencies with:

    sudo apt-get update
    sudo apt-get -y install --no-install-recommends ca-certificates git python3-virtualenv

Now set up the project with:

    git clone https://gitlab.com/jimdigriz/mjoelnir.git
    cd mjoelnir
    virtualenv -p python3 venv
    . venv/bin/activate
    pip3 install -r requirements.txt

# Usage

From inside the project directory run:

    export TWILIO_ACCOUNT_SID=AC093e3266663b9b4e5a244367e49724f5
    export TWILIO_AUTH_TOKEN=bd38098ea50a99d7d0d0ebaeb89aa938
    
    . venv/bin/activate
    python3 mjolnir.py --from +15005550006 --to +44....

Statistics are regularly printed (default is every 5 seconds, changeable with `--stats-interval`) and you can quit the tool by pressing `Ctrl-C` at any time.

You can use the following to see a description of all the arguments you can use to control the tool.

    python3 mjolnir.py --help

Some of the options are described here:

 * Credentials:
     * **`--twilio-account-sid` [required]:** Twilio Account SID
         * will use the environment variable `TWILIO_ACCOUNT_SID` if set
     * **`--twilio-auth-token` [required]:** Twilio Auth Token
         * will use the environment variable `TWILIO_AUTH_TOKEN` if set
     * recommended you supply [credentials securely via environment variables](https://www.twilio.com/docs/usage/secure-credentials)
 * Telephone numbers:
     * **`--from` [required]:** number you are claiming to call from
     * **`--to` [required]:** number you are dialling
 * Calls:
     * **`--calls-max` (default: `10`):** maximum hard limit of simultaneous calls
     * **`--call-duration` (default: `120`):** call duration before hanging up in seconds
     * **`--call-duration-fuzz` (default: `20`):** percentage of random fuzz to add to call duration
 * Rate limiting:
     * uses a [Token Bucket](https://www.tutorialandexample.com/congestion-control-algorithm/) to rate limit calling
     * **`--rate-limit` (default: `10.0`):** calls per second
         * can be set to values less than `1.0` (for example `0.2` means one every five seconds)
     * **`--rate-limit-burst` (default: `1`):** burstable calls allowed before rate limiting takes effect
