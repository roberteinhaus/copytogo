import web
import os
from os.path import basename
from os.path import getsize
from os.path import join
import json
import subprocess
import shutil
import errno
import pushbullet

import ctgconfig

web.config.debug = True
render = web.template.render('templates/')

urls = (
    '/(.*)/', 'redirect',
    '/favicon.ico', 'icon',
    '/', 'index',
    '/dirtree', 'dirtree',
    '/usbdrives', 'usbdrives',
    '/usbdrives/(\w+)', 'usbdrives',
    '/copy', 'copyFiles'
)

config = ctgconfig.CTGConfig()
if config.getboolean('PUSHBULLET', 'send_pushes'):
    pb = pushbullet.PushBullet(config.get('PUSHBULLET', 'api_key'))


def add_global_hook():
    g = web.storage(
        {
            "copy_status": {
                "running": False,
                "files": 0,
                "files_completed": 0,
                "size": 0,
                "size_completed": 0
            }
        }
    )

    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper


class redirect:

    def GET(self, path):
        web.seeother('/' + path)


class icon:

    def GET(self):
        raise web.seeother("/static/favicon.ico")


class index:

    def GET(self):
        return render.index()


class dirtree:

    def path_to_dict(self, path, root=False):
        d = {'text': basename(path) or 'Music'}
        if os.path.isdir(path):
            d['type'] = 'directory'
            d['children'] = []
            for x in os.listdir(path):
                # exclude images
                if not x.endswith(('.jpg', '.png', '.gif')):
                    d['children'].append(self.path_to_dict(join(path, x)))
        else:
            d['type'] = 'file'
            d['size'] = getsize(path)
            d['path'] = path
        if root:
            d['state'] = {'opened': True}
            d['type'] = 'root'
        return d

    def GET(self):
        return json.dumps(self.path_to_dict(config.get('AUDIO', 'dir'), True))


class usbdrives:

    def get_lsblk(self):
        lsblk = subprocess.check_output(
            ["lsblk", "-Jo", "name,tran,label,mountpoint,size,fstype"]
        )
        return json.loads(lsblk)

    def get_space_information(self, parts):
        newparts = []
        for part in parts:
            if not part['mountpoint']:
                mountpoint = "/mnt/ctg"
                subprocess.call(["mount", "/dev/" + part['name'], mountpoint])
            else:
                mountpoint = part['mountpoint']
            freespace = subprocess.check_output(
                ["df", "--output=size,used,avail", mountpoint]
            )
            spaces = freespace.split('\n')[1].split()
            part['size'] = spaces[0]
            part['used'] = spaces[1]
            part['free'] = spaces[2]
            newparts.append(part)
            if not part['mountpoint']:
                subprocess.call(["umount", mountpoint])
        return newparts

    def get_usb_drives(self):
        parts = []
        for dev in self.get_lsblk()['blockdevices']:
            if(dev['tran'] == 'usb'):
                for part in dev['children']:
                    parts.append(part)
        return parts

    def GET(self, param=None):
        drives = self.get_usb_drives()
        drives = self.get_space_information(drives)
        return json.dumps(drives)


class copyFiles:

    def GET(self):
        return json.dumps(web.ctx.globals.copy_status)

    def POST(self):
        if web.ctx.globals.copy_status['running']:
            return
        web.ctx.globals.copy_status['running'] = True
        data = json.loads(web.data())
        web.ctx.globals.copy_status['files'] = len(data['files'])
        ud = usbdrives()
        drives = ud.get_usb_drives()
        for drive in drives:
            if drive['name'] == data['drive']:
                if not drive['mountpoint']:
                    mountpoint = "/mnt/ctg"
                    mount = subprocess.call(
                        ["mount", "/dev/" + drive['name'], mountpoint])
                else:
                    mountpoint = drive['mountpoint']
                break

        if data['erase']:
            for x in os.listdir(mountpoint):
                delpath = os.path.join(mountpoint, x)
                print("rm " + delpath)
                shutil.rmtree(delpath)

        files = data['files']
        for f in files:
            web.ctx.globals.copy_status['files_completed'] += 1
            srcfile = f.replace(config.get('AUDIO', 'dir'), '')

            assert not os.path.isabs(srcfile)
            dstdir = os.path.join(mountpoint, os.path.dirname(srcfile))
            try:
                os.makedirs(dstdir)
                print("mkdir " + dstdir)
            except OSError as exception:
                if exception.errno != errno.EEXIST or not os.path.isdir(dstdir):
                    raise
            subprocess.call(["cp", f, dstdir])
            print("copy " + f + " to " + dstdir)

        mount = subprocess.call(["umount", mountpoint])
        pb = pushbullet.PushBullet('o.gtkUhglh8LacwQTrJ51ytGECuXy0OfkB')
        pb.push_note('Copy To-Go', 'Copy finished!')
        web.ctx.globals.copy_status['running'] = False
        web.ctx.globals.copy_status['files'] = 0
        web.ctx.globals.copy_status['files_completed'] = 0
        web.ctx.globals.copy_status['size'] = 0
        web.ctx.globals.copy_status['size_completed'] = 0

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.add_processor(add_global_hook())
    app.run()
