import os.path
import atexit
from hexicapi import client

client.port = 1234
client.basic_on_calf()

C = client.run('explorer', input("Username: "), input("Password: "))
if not os.path.exists('explore'):
    os.mkdir('explore')
if not os.path.exists(os.path.join('explore', C.username)):
    os.mkdir(os.path.join('explore', C.username))
C.send('init')
C.receive()

code = 'not ok'

mode = 'server'
interact_mode = 'download'
sorting_method = 'name'
difference_mode = 'ask'
modes = {
    'server': '<- server',
    'local': 'local ->',
    'both': '<-both ways->'
}
difference_modes = {
    'server': 'server',
    'local': 'local',
    'ask': 'ask user',
}
interact_modes = {
    'download': 'download',
    'remove': 'delete',
    'rename': 'rename'
}
sync_delete = False

def get_path():
    C.send('path')
    path = list(C.receive_objects())
    del path[0]
    return tuple(path)

def ls():
    C.send('ls')
    return C.receive_objects()

def download(i: int):
    C.send(f'download:{i - 2}')
    filename, data = C.receive_objects()
    directory = os.path.join('explore', C.username, *get_path())
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, filename), 'wb') as f:
        f.write(data)

def delete(i: int):
    C.send(f'delete:{i-2}')
    C.receive()

def run():
    global code, mode, sync_delete, difference_mode, interact_mode
    while code == 'not ok':
        print('\n\n\n')
        C.send(f'prompt:{sorting_method}')
        print(C.receive().replace('$current_mode', modes[mode])
                         .replace('$current_sync_delete', 'ON' if sync_delete else 'OFF')
                         .replace('$current_difference_mode', difference_modes[difference_mode])
                         .replace('$current_interact_mode', interact_modes[interact_mode])
             )
        C.send(i := input("Select: "))
        code = C.receive()
    try: i = int(i)
    except: pass
    if i == 0:
        C.send('upload')
        C.receive()
        C.send(input('Filename: '))
        C.receive()
        loc = input('Actual file: ')
        while not os.path.isfile(loc):
            print('Try again')
            loc = input('Actual file: ')
        with open(loc, 'rb') as f:
            C.send(f.read())
        C.receive()
    elif i == 1:
        C.send('make_folder')
        C.receive()
        C.send(input('Folder name: '))
        C.receive()
    elif i == 2:
        C.send('cd:..')
        C.receive()
    elif i == 's':
        if mode == 'server':
            files = ls()
            path = os.path.join('explore', C.username, *get_path())
            my_files = os.listdir(path)
            my_files = [file for file in my_files if os.path.isfile(os.path.join(path, file))]
            for index, file in [(i, file) for i, file in enumerate(files) if type(file) == dict]:
                download(index+3)
            if sync_delete:
                server_files = [file['name'] for i, file in enumerate(files) if type(file) == dict]
                for file in my_files:
                    if not file in server_files:
                        os.remove(os.path.join(path, file))
        elif mode == 'local':
            directory = os.path.join('explore', C.username, *get_path())
            files = os.listdir(directory)
            server = ls()
            my_files = [(file, path) for file in files if os.path.isfile(path := os.path.join(directory, file))]
            for filename, path in my_files:
                C.send('upload')
                C.receive()
                C.send(filename)
                C.receive()
                with open(path, 'rb') as f:
                    C.send(f.read())
                C.receive()
            if sync_delete:
                to_delete = []
                for file in server:
                    if type(file) == dict and not file['name'] in my_files:
                        to_delete.append(file['name'])
                for deleted in to_delete:
                    server = ls()
                    for i, file in enumerate(server):
                        if type(file) == dict and file['name'] in deleted:
                            delete(i)
                            break
    elif i == 'm':
        if mode == 'server':
            mode = 'local'
        elif mode == 'local':
            mode = 'both'
        else:
            mode = 'server'
    elif i == 'i':
        if interact_mode == 'download':
            interact_mode = 'remove'
        elif interact_mode == 'remove':
            interact_mode = 'rename'
        else:
            interact_mode = 'download'
    elif i == 'd':
        sync_delete = not sync_delete
    elif i == 'h':
        if difference_mode == 'ask':
            difference_mode = 'local'
        elif difference_mode == 'local':
            difference_mode = 'server'
        else:
            difference_mode = 'ask'
    elif i == 'e':
        C.disconnect()
        C.id = None
    elif type(i) == int and i > 2:
        files = ls()
        if type(files[i - 3]) == dict:
            if interact_mode == 'download':
                download(i)
            elif interact_mode == 'remove':
                delete(i)
            elif interact_mode == 'rename':
                files = ls()
                path = os.path.join('explore', C.username, *get_path(), files[i-3]['name'])
                C.send(f'rename:{i-2}')
                C.receive()
                print(f'Original filename: "{os.path.basename(path)}"')
                C.send(new_name := input('Filename: '))
                if os.path.isfile(path):
                    os.rename(path, os.path.join(os.path.dirname(path), new_name))
                C.receive()
        else:
            C.send(f'cd:{i - 2}')
            C.receive()


    # sync and display prompt again
    C.send('sync')
    C.receive()
    code = 'not ok'

while C.id:
    try:
        run()
    except KeyboardInterrupt:
        C.send('e')
        C.receive()
        C.disconnect()

C.disconnect()
