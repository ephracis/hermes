Hermes
======
Tool for downloading and analyzing communication security of apps on
the Google Play Store.

===============================

# Requirements

You need to install some packages for Hermes to function properly:

* Androguard

 Tool for reverse engineering Android app files. 

 URL: https://code.google.com/p/androguard/

* Mallodroid

 An Androguard module which examines SSL certificate validation.

 URL: https://github.com/sfahl/mallodroid

* GooglePlayAPI

 Python module which uses an unofficial API for searching for and downloading apps on the Google Play Store.

 URL: https://github.com/egirault/googleplay-api

You need to specify the location of Mallodroid and GooglePlayAPI. You
do this by setting the PYTHONPATH environment variable:

`$ export PYTHONPATH=$PYTHONPATH:/path/to/mallodroid:/path/to/googleplayapi`

===============================

# Usage

In order to download apps from the Google Play Store you need
to provide your android id number.

Type *#*#8255#*#* on your phone to start GTalk Monitor.
Your Android ID is the hexadecimal string shown as 'aid'.

You will also need to specify your credentials to log in
to the Google Play Store. You can either specify your
email and password, or an access token. Nothing will be saved
anywhere or sent to anyone other than Google.

## Examples:

Use mail and password:
`$ hermes.py -u EMAIL -p PASS`

Use token:
`$ hermes.py -t TOKEN`

Generate statistic files:
`$ hermes.py -D -P`

Print statistics:
`$ hermes.py -D -G`

For more information:
`$ hermes.py -h`

===============================

# Support

You can email me at my gmail where my username is: ephracis

===============================

# Contribute

You are free to contribute to the project. Extend it, refactor it, fix bugs you find, etc.
Send me a pull request and I'll look into it.

You can support my work by sending a contribution to the following bitcoin address:
14xHJbs8hCxXzxe9Facv162AZmWyYEeWb1

===============================

# License

This code is released under the MIT license. See http://opensource.org/licenses/MIT
