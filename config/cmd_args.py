import argparse
import config

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--firmwares', required=False, type=str, help='Relative directory of firmwares')
parser.add_argument('-r', '--repositories', required=False, type=str, help='Relative directory of repositories')
parser.add_argument('-u', '--url', required=False, type=str, help='URL of server')
parser.add_argument('-ns', '--not_secure', required=False, action='store_true', help='Unsecure networking')

parser.add_argument('-un', '--username', required=False, type=str, help='Authentication username')
parser.add_argument('-pw', '--password', required=False, type=str, help='Authentication password')

cmd_args = parser.parse_args()

if cmd_args.firmwares : config.CONFIG.FIRMWARE_DIR = cmd_args.firmwares
if cmd_args.repositories : config.CONFIG.REPOS_DIR = cmd_args.repositories
if cmd_args.url : config.CONFIG.BASE_URL = cmd_args.url
if cmd_args.not_secure : config.CONFIG.NOT_SECURE = True

if cmd_args.username : config.AUTH_CONFIG.USERNAME = cmd_args.username
if cmd_args.password : config.AUTH_CONFIG.PASSWORD = cmd_args.password
