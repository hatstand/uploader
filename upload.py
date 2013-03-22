#!/usr/bin/python

import json
import os
import requests
import subprocess
import sys

CLIENT_ID='833751105344.apps.googleusercontent.com'
CLIENT_SECRET='hJ5YATel0Vq2Kxudqp-UqY5H'

SCOPES='https://www.googleapis.com/auth/drive'

AUTH_URL='https://accounts.google.com/o/oauth2/auth'
TOKEN_URL='https://accounts.google.com/o/oauth2/token'

UPLOAD_URL='https://www.googleapis.com/upload/drive/v2/files'

def GetRefreshTokenLocation():
  config_directory = os.environ.get('XDG_CONFIG_HOME')
  if config_directory is None:
    config_directory = os.path.join(os.environ.get('HOME'), '.config')
  if not os.path.exists(config_directory):
    os.mkdir(config_directory)
  return os.path.join(config_directory, 'google_drive_upload_token')

def LoadRefreshToken():
  path = GetRefreshTokenLocation()
  try:
    with open(path, 'r') as f:
      return f.readline().rstrip()
  except:
    return None

def SaveRefreshToken(token):
  path = GetRefreshTokenLocation()
  with open(path, 'w+') as f:
    f.write(token)
    f.write('\n')

def GetMimeTypeForFile(path):
  try:
    mime_type = subprocess.check_output(['file', '--mime-type', '-b', path])
    if mime_type is None:
      return 'application/octet-stream'
    return mime_type.rstrip()
  except:
    return 'application/octet-stream'

def GetAccessToken():
  refresh_token = LoadRefreshToken()
  print '===%s===' % refresh_token
  if refresh_token is None:
    auth_request = requests.Request(
        url=AUTH_URL,
        params = {
          'response_type': 'code',
          'client_id': CLIENT_ID,
          'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
          'scope': SCOPES,
        })
    auth_request = auth_request.prepare()
    print 'Open this url and paste the code back here:\n%s' % auth_request.url
    code = sys.stdin.readline()

    token_response = requests.post(
        TOKEN_URL,
        data = {
          'code': code,
          'client_id': CLIENT_ID,
          'client_secret': CLIENT_SECRET,
          'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
          'grant_type': 'authorization_code',
        })
    refresh_token = token_response.json()['refresh_token']
  else:
    token_response = requests.post(
        TOKEN_URL,
        data = {
          'refresh_token': refresh_token,
          'client_id': CLIENT_ID,
          'client_secret': CLIENT_SECRET,
          'grant_type': 'refresh_token',
        })
    print token_response
    print token_response.text

  data = token_response.json()
  access_token = data['access_token']
  if refresh_token is not None:
    SaveRefreshToken(refresh_token)
  return access_token


def Upload(path, access_token):
  file_size = os.stat(path).st_size
  mime_type = GetMimeTypeForFile(path)
  print 'Uploading %s (%d) %s' % (os.path.basename(path), file_size, mime_type)
  session_start = requests.post(
      UPLOAD_URL,
      params = {
        'uploadType': 'resumable',
      },
      data = json.dumps({
        'title': os.path.basename(path),
      }),
      headers = {
        'X-Upload-Content-Type': mime_type,
        'X-Upload-Content-Length': file_size,
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % access_token,
      })
  print session_start
  print session_start.text

  location = session_start.headers['Location']
  with open(path) as f:
    for start in xrange(0, file_size - 1, 1024*512):
      end = min(start + 1024*512, file_size) - 1
      f.seek(start)
      print 'Uploading %d-%d of %d' % (start, end, file_size)
      put = requests.put(
          location,
          headers = {
            'Content-Length': end - start,
            'Content-Type': mime_type,
            'Content-Range': 'bytes %d-%d/%d' % (start, end, file_size),
            'Authorization': 'Bearer %s' % access_token,
          },
          data = f.read(end - start + 1))

def main():
  if len(sys.argv) < 2:
    print 'Usage: %s <file> [file...]' % sys.argv[0]
    return

  paths = sys.argv[1:]
  for path in paths:
    if not os.path.exists(path):
      print 'File does not exist: %s' % path
      return

  access_token = GetAccessToken()
  for path in paths:
    Upload(path, access_token)

if __name__ == '__main__':
  main()
