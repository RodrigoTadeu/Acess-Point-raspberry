from flask import Flask, render_template, request
import subprocess
import os
import time
from threading import Thread
import fileinput
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.debug = True
UPLOAD_FOLDER = os.path.join(os.getcwd(), '/home/debian/beagleboneble/BeagleBoneProject/AP-BeagleBone/data')

@app.route('/')
def index():
    os.system('sudo ip link set dev wlan0 up')
    time.sleep(2)
    wifi_ap_array = scan_wifi_networks()
    return render_template('app.html', wifi_ap_array = wifi_ap_array, ip ="")

@app.route('/ipFixo', methods= ['GET','POST'])
def ipFixo():
    address = request.form.get('address')
    broadcast = request.form.get('broadcast')
    netmask = request.form.get('netmask')
    gateway = request.form.get('gateway')
    dns = request.form.get('dns')

    wifi_ap_array = scan_wifi_networks()
    fixar_ip(address, broadcast, netmask, gateway, dns)
    return render_template('app.html', wifi_ap_array = wifi_ap_array, ip='Agora seu IP é '+ address)

@app.route('/config_ap')
def config_ap():
    return render_template('config_ap.html')

@app.route('/setar_ap', methods=['GET', 'POST'])
def setar_ap():
    ap='yes'
    nameAp = request.form.get('nameAp')
    senhaAp=request.form.get('senhaAp')
    info_ap(ap,nameAp,senhaAp)

    def sleep_and_start_ap():
        time.sleep(2)
        set_ap_client_mode()
    t = Thread(target=sleep_and_start_ap)
    t.start()
    return render_template('save_wpa_credentials.html', ssid= nameAp, wpa_key = senhaAp)


@app.route('/alias_bluetooth')
def alias_bluetooth():
    return render_template('alias_bluetooth.html')

@app.route('/nomeBluetooth', methods=['GET', 'POST'])
def setar_nome():
    bluetooth = request.form.get('bluetooth')
    mudar_nome_bluetooth(bluetooth)
    return render_template('informacao.html', informacao='Álias do Bluetooth Alterado')

@app.route('/save_credentials', methods = ['GET', 'POST'])
def save_credentials():
    ssid = request.form['ssid']
    wifi_key = request.form['wifi_key']
    create_wpa_supplicant(ssid, wifi_key)
    
    def sleep_and_start_ap():
        ap='no'
        nameAp='xxxxxx'
        senhaAp='xxxxxxxx'
        info_ap(ap,nameAp,senhaAp)
        time.sleep(2)
        set_ap_client_mode()
    t = Thread(target=sleep_and_start_ap)
    t.start()
    return render_template('save_credentials.html', ssid = ssid)

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/upload_arquivo', methods=['GET',"POST"])
def upload_arquivo():
    file = request.files['file']
    if file:
        savePath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(savePath)
        return render_template('informacao.html', informacao='Upload de arquivo concluído')
    else:
        return 'Nenhum arquivo enviado!'

######## FUNCTIONS ##########

def scan_wifi_networks():
    iwlist_raw = subprocess.Popen(['iwlist', 'scan'], stdout=subprocess.PIPE)
    ap_list, err = iwlist_raw.communicate()
    ap_array = []

    for line in ap_list.decode('utf-8').rsplit('\n'):
        if 'ESSID' in line:
            ap_ssid = line[27:-1]
            if ap_ssid != '':
                ap_array.append(ap_ssid)

    return ap_array

def create_wpa_supplicant(ssid, wifi_key):
    if not os.path.exists('/etc/wpa_supplicant/wpa_supplicant.conf.original'):
        os.system('mv /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.original')
    with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as arquivo:
        arquivo.write('ctrl_interface=/var/run/wpa_supplicant\nctrl_interface_group=0\nupdate_config=1\n\nnetwork={\n ssid="'+ssid+'"\n psk="'+wifi_key+'"\n}')

def fixar_ip(address, broadcast, netmask, gateway, dns):
    if not os.path.exists('/etc/network/interfaces.original'):
        os.system('mv /etc/network/interfaces /etc/network/interfaces.original')
    with open('/etc/network/interfaces', 'w') as arquivo:
        arquivo.write('auto lo\niface lo inet loopback\n\nauto wlan0\niface wlan0 inet static\naddress ' +address +'\nbroadcast ' +broadcast +'\nnetmask ' +netmask +'\ngateway ' +gateway +'\ndns-nameservers ' +dns +'\n wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf') 

    if not os.path.exists('/etc/resolv.conf.original'):
        os.system('mv /etc/resolv.conf /etc/resolv.conf.original')
    with open('/etc/resolv.conf', 'w') as arquivo:
        arquivo.write('nameserver 192.168.1.1\nnameserver ' + dns)

def info_ap(ap,nome,senha):
    if not os.path.exists('/etc/default/bb-wl18xx.original'):
        os.system('mv /etc/default/bb-wl18xx /etc/default/bb-wl18xx.original')
    with open('/etc/default/bb-wl18xx', 'w') as arquivo:
        arquivo.write('TETHER_ENABLED='+ap+'\nUSE_CONNMAN_TETHER=no\nUSE_WL18XX_IP_PREFIX="192.168.8"\nUSE_INTERNAL_WL18XX_MAC_ADDRESS=yes\nUSE_WL18XX_POWER_MANAGMENT=off\nUSE_PERSONAL_SSID="'+nome+'"\nUSE_PERSONAL_PASSWORD="'+senha+'"\nUSE_GENERATED_DNSMASQ=yes\nUSE_GENERATED_HOSTAPD=yes\nUSE_APPENDED_SSID=no')

def mudar_nome_bluetooth(alias):
    os.system('bluetoothctl system-alias ' +alias)

def set_ap_client_mode():
    os.system('reboot')

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port='5000')
