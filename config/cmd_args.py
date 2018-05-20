import argparse
import config

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--firmwares', required=False, type=str, help='Relative directory of firmwares')
parser.add_argument('-r', '--repositories', required=False, type=str, help='Relative directory of repositories')
parser.add_argument('-u', '--url', required=False, type=str, help='URL of server')
parser.add_argument('-ns', '--not_secure', required=False, action='store_true', help='Unsecure networking')

cmd_args = parser.parse_args()

if cmd_args.firmwares : config.Config.FIRMWARE_DIR = cmd_args.firmwares
if cmd_args.repositories : config.Config.REPOS_DIR = cmd_args.repositories
if cmd_args.url : config.Config.BASE_URL = cmd_args.url
if cmd_args.not_secure : config.Config.NOT_SECURE = True
