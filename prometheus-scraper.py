from prometheus_client import start_http_server, Gauge
import time
import json
import tinytuya
import os

d = tinytuya.Device(
    os.environ['TUYA_DEVID'],
    os.environ['TUYA_IPADDR'],
    local_key=os.environ['TUYA_LOCALKEY'],
    version=3.5
)

# {'dps': {
#   '16': True,
#   '101': 2364,
#   '102': 5284,
#   '103': 12289,
#   '104': 107,
#   '105': 2134,
#   '106': 98,
#   '107': 60,
#   '108': 11,
#   '109': 180,
#   '110': 250,
#   '111': 0,
#   '113': 0,
#   '114': 0,
#   '115': 50,
#   '116': '2',
#   '119': 0,
#   '123': 2133}}

on_off = Gauge('switch_state', 'power on/off')
voltage = Gauge('voltage', 'detected voltage')
current = Gauge('current', 'detected current')
power = Gauge('power', 'detected power in kW')
run_time = Gauge('run_time', 'run time in minutes')
energy = Gauge('energy', 'energy in kWh')
power_factor = Gauge('power_factor', 'power factor')
frequency = Gauge('frequency', 'frequency in Hz')
ac_temp = Gauge('ac_temp', 'temperature in C')
state_flag = Gauge('state_flag', 'state flag')
amiel_user = Gauge('amiel_user', 'current users')
ethan_user = Gauge('ethan_user', 'current users')
iggy_user = Gauge('iggy_user', 'current users')

def zero_get(dict, key):
    if key in dict:
        return dict[key]
    else:
        return 0


def update_metrics():
    status = d.status()
    print(status)

    if ('protocol' in status.keys()) or ('Error' in status.keys()):
        return

    ptr = status['dps']

    on_off.set(int(zero_get(ptr, '16')))

    voltage.set(zero_get(ptr, '101')/10)

    current.set(zero_get(ptr, '102')/1000)

    power.set(zero_get(ptr, '103')/10)

    run_time.set(zero_get(ptr, '104'))

    energy.set(zero_get(ptr, '105')/1000)

    power_factor.set(zero_get(ptr, '106'))

    frequency.set(zero_get(ptr, '107'))

    ac_temp.set(zero_get(ptr, '108'))

    state_flag.set(zero_get(ptr, '116'))

    with open("aircon_info.json", 'r') as f:
        db = json.load(f)
        users = db['current_users']
        try:
            if int(ptr['16']) == 0:
                iggy_user.set(0)
                ethan_user.set(0)
                amiel_user.set(0)
            else:
                iggy_user.set(int((users >> 2) & 1))
                amiel_user.set(int((users >> 1) & 1))
                ethan_user.set(int((users >> 0) & 1))
        except KeyError:
            pass


if __name__ == '__main__':
    start_http_server(6060)
    while True:
        update_metrics()
        time.sleep(5)