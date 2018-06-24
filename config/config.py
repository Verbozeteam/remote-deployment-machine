import platform

class CONFIG:
    BASE_URL = 'www.verboze.com'
    FIRMWARE_DIR = 'firmwares/'
    REPOS_DIR = 'repositories/'
    MOUNTING_DIR = 'mountings/'
    NOT_SECURE = False

    OS = platform.system()

    DISKS_CHECK_INTERVAL = 5
    FIRMWARES_CHECK_INTERVAL = 5
