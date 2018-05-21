import platform

class CONFIG:
    BASE_URL = 'www.verboze.com'
    FIRMWARE_DIR = 'firmwares/'
    REPOS_DIR = 'repositories/'
    NOT_SECURE = False

    OS = platform.system()

    DISKS_CHECK_INTERVAL = 15
    FIRMWARES_CHECK_INTERVAL = 15
