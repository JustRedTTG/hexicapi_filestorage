import os
import time
import socket
from hashlib import sha256
from hexicapi import server

hostname = socket.gethostname()
server.ip = socket.gethostbyname(hostname)
server.port = 1234

def get_folder(C: server.Iden):
    folder = C.data
    for i in C.room:
        folder = folder[i]
    return folder

def get_path(C: server.Iden):
    folder = C.data
    path = [folder[0]['name']]
    for i in C.room:
        folder = folder[i]
        path.append(folder[0]['name'])
    return path

def fill_details(folder, index):
    keys = {'last_changed': time.time()}
    file_keys = folder[index].keys()
    for key in [key for key in keys.keys() if key not in file_keys]:
        folder[index][key] = keys[key]

sorting_methods = {}
def add_sorting_method(m):
    sorting_methods[m.__name__] = m

@add_sorting_method
def name(v):
    v = v[1]
    if type(v) == dict:
        return v['name']
    else:
        return '!!A00'+v[0]['name']


@server.app
def explorer(C: server.Iden, msg: str):
    if msg == 'init':
        if not C.data:
            C.data = [{"name": 'root', "type":'information', "realname": f'.'}, {"name": 'Getting started with explore.txt', 'type':'file','realname': 'gswe.txt'}]
            C.encrypted_file('gswe.txt', b"""Welcome to Explore, a little project that works with hexicapi
    Usage:
        Sync files between an encrypted server and client connection!
        Uses hexicapi!
        Enjoy!""")
            C.datasync()
        C.room = []
        C.send('ok')
    elif msg.startswith('prompt'):
        C.send(f"""Explorer {'Premium' if C.admin else 'Basic'} - {C.username} - {C.socket.getsockname()[0]}
[0] Upload
[1] New folder"""+ ('\n\n' if len(C.room) == 0 else
"\n[2] < Go back\n\n")+'\n'.join([
                f"[{i+2}] ★ {item['name']}" if type(item) == dict else
                f"[{i+2}] ✺ {item[0]['name']}" for i, item in
                sorted(
                    [
                        (i, item)
                        for i, item in enumerate(get_folder(C))
                        if i > 0
                    ],
                    key=sorting_methods[msg.split(':')[1]]
                )
            ]
        )+"""\n
[s] SYNC DIRECTORY
[m] CHANGE MODE [$current_mode]
[i] CHANGE INTERACT [$current_interact_mode]
[d] SYNC DELETES [$current_sync_delete]
[h] DIFFERENCE [$current_difference_mode]
[e] DISCONNECT
""")
        try:
            index = int(index_msg := C.receive())
        except:
            if not index_msg in ['s', 'm', 'i', 'd', 'h', 'e']:
                C.send('not ok')
                return
            else:
                C.send('ok')
                return
        if index > 2:
            item = get_folder(C)[index - 2]
            if type(item) == dict:
                C.send(item['type'])
            else:
                C.send('ok')
        else:
            C.send('ok')
    elif msg == 'upload':
        C.send('ok')
        filename = C.receive()
        folder = get_folder(C)
        C.send('ok')
        realname = sha256(f'{folder[0]["name"]}-{filename}'.encode()).hexdigest()
        reupload = False
        for i, item in enumerate(folder):
            if type(item) != dict: continue
            elif item['name'] == filename:
                reupload = True
                folder[i]['time_changed'] = time.time()
                break

        if not reupload:
            C.encrypted_file(realname, C.receive(skip_str=True))
            folder.append({'name': filename, 'realname': realname, 'type': 'file', 'time_changed': time.time()})
        else:
            C.encrypted_file(folder[i]['realname'], C.receive(skip_str=True))
        C.send('ok')
    elif msg.startswith('download'):
        folder = get_folder(C)
        index = int(msg.split(':')[1])
        fill_details(folder, index)
        file = folder[index]
        C.send_objects(file['name'], C.decrypted_file(file['realname']))
    elif msg == 'sync':
        C.datasync()
        C.send('ok')
    elif msg == 'ls':
        folder = get_folder(C)
        for i, item in enumerate(folder):
            if type(item) == dict:
                fill_details(folder, i)
        C.send_objects(*[item if type(item) == dict else [item[0]] for i, item in enumerate(folder) if i > 0])
    elif msg == 'cd:..':
        if len(C.room) > 0:
            del C.room[-1]
        C.send('ok')
    elif msg.startswith('cd'):
        C.room.append(int(msg.split(':')[1]))
        C.send('ok')
    elif msg == 'path':
        C.send_objects(*get_path(C))
    elif msg.startswith('make_folder'):
        C.send('ok')
        name = C.receive()
        get_folder(C).append([{'type': 'folder', 'name': name, 'realname': '_folder'}])
        C.send('ok')
    elif msg.startswith('delete'):
        folder = get_folder(C)
        index = int(msg.split(':')[1])
        item = folder[index]
        if type(item) == dict:
            path = os.path.join('users', sha256(C.username.encode()).hexdigest(), item['realname'])
            if os.path.exists(path):
                os.remove(path)
        else:
            # TODO: make it so it clears everything in the folder and sub-folders in terms of files :3
            pass
        del folder[index]
        C.send('ok')
    elif msg.startswith('rename'):
        C.send('ok')
        filename = C.receive()
        folder = get_folder(C)
        folder[int(msg.split(':')[1])]['name'] = filename
        C.send('ok')


server.run()