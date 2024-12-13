import os

_this_directory = os.path.dirname(os.path.realpath(__file__))
_proxies_csv = os.path.join(_this_directory, "proxies.csv")
_used_proxies_csv = os.path.join(_this_directory, "used_proxies.csv")

for file in [_proxies_csv, _used_proxies_csv]:
    if not os.path.exists(file):
        os.mkdir(file)