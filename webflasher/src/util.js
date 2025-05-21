export const HELPER_CODE = `import os
import json
os.chdir('/')

def is_directory(path):
  return True if os.stat(path)[0] == 0x4000 else False

def get_all_files(path, array_of_files = []):
  files = os.ilistdir(path)
  for file in files:
    is_folder = file[1] == 16384
    p = path + '/' + file[0]
    array_of_files.append({
        "path": p,
        "type": "folder" if is_folder else "file"
    })
    if is_folder:
        array_of_files = get_all_files(p, array_of_files)
  return array_of_files


def ilist_all(path):
  print(json.dumps(get_all_files(path)))

def delete_folder(path):
  files = get_all_files(path)
  for file in files:
    if file['type'] == 'file':
        os.remove(file['path'])
  for file in reversed(files):
    if file['type'] == 'folder':
        os.rmdir(file['path'])
  os.rmdir(path)

def b2a_base64(data):
  base64_chars = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
  encoded = bytearray()
  i = 0
  while i < len(data):
    chunk = data[i:i+3]
    bin_string = ''
    for byte in chunk:
      bin_string += f'{byte:08b}'
    while len(bin_string) < 24:
      bin_string += '00000000'
    for j in range(0, 24, 6):
      segment = bin_string[j:j+6]
      index = int(segment, 2)
      encoded.append(base64_chars[index])
    if len(chunk) < 3:
      for _ in range(3 - len(chunk)):
        encoded[-1] = ord(b'=')
    i += 3
  # Convert the bytearray to bytes and add a newline
  return bytes(encoded)
`

export function sleep(millis) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve()
    }, millis)
  })
}

export function generateHash() {
  return `${Date.now()}_${parseInt(Math.random()*1024)}`
}

export function base64ToUint8Array(base64) {
    const binaryString = atob(base64)
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
    }
    return bytes
}

export function extract(out) {
  const indexOk = out.indexOf('OK')
  const indexEnd = out.indexOf('\x04')

  if (indexOk == -1 || indexEnd == -1) {
    return []
  }
  return out.slice(indexOk+2, indexEnd)
}