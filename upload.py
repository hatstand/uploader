#!/usr/bin/python

import json
import os
import requests
import sys

CLIENT_ID='833751105344.apps.googleusercontent.com'
CLIENT_SECRET='hJ5YATel0Vq2Kxudqp-UqY5H'

SCOPES='https://www.googleapis.com/auth/drive'

AUTH_URL='https://accounts.google.com/o/oauth2/auth'
TOKEN_URL='https://accounts.google.com/o/oauth2/token'

UPLOAD_URL='https://www.googleapis.com/upload/drive/v2/files'

def GetAccessToken():
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

  data = token_response.json()
  access_token = data['access_token']
  return access_token


def Upload(path, access_token):
  file_size = os.stat(path).st_size
  print 'Uploading %s (%d)' % (os.path.basename(path), file_size)
  session_start = requests.post(
      UPLOAD_URL,
      params = {
        'uploadType': 'resumable',
      },
      data = json.dumps({
        'title': os.path.basename(path),
      }),
      headers = {
        'X-Upload-Content-Type': 'audio/mpeg',
        'X-Upload-Content-Length': file_size,
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % access_token,
      })
  print session_start
  print session_start.text

  location = session_start.headers['Location']
  with open(path) as f:
    for i, start in enumerate(xrange(0, file_size - 1, 1024*512)):
      end = min(start + 1024*512, file_size) - 1
      f.seek(start)
      print 'Uploading %d-%d of %d' % (start, end, file_size)
      put = requests.put(
          location,
          headers = {
            'Content-Length': end - start,
            'Content-Type': 'application/octet-stream',
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
