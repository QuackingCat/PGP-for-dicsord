import tkinter as tk
import subprocess, os, signal, sys, json, webbrowser

MITM_SCRIPT = "dishook.py"
mitmpid = 0
interact_button = None

if not os.path.exists('keys.json'):
    with open('keys.json', 'w') as f:
        f.write('{"private":[], "public":{}}')

with open('keys.json', "r") as f:
    keys = json.loads(f.read())

def save_keys():
    with open('keys.json', 'w') as f:
        json.dump(keys, f)
    

root = tk.Tk()
root.title("Discord PGP Keys Manager")

def interact_with_mitmproxy():
    global mitmpid
    global interact_button
    if mitmpid == 0:
        command = ["mitmdump", "-s", f"{MITM_SCRIPT}", "--set", "websocket=true"]
        
        try:
            mitmpid = subprocess.Popen(command).pid
        except FileNotFoundError:
            error("mitmpdump not in path.")
            return
        except Exception as e:
            print(f"Error: {e}")
            return
        
        print("MITMProxy started.")
        
        interact_button.config(text="Stop MITMProxy", bg="red")
    else:
        try:
            os.kill(mitmpid, signal.SIGKILL)
        except:
            pass
        mitmpid = 0
        print("Killed MITMProxy.")
        interact_button.config(text="Start MITMProxy", bg="green")


def on_closing():
    if mitmpid != 0:
        interact_with_mitmproxy()
    root.destroy()

secwin = None
trdwin = None

def trdwin_closed(event):
    global trdwin
    trdwin = None
def secwin_closed(event):
    global secwin
    secwin = None

def privateselection(event):
    global secwin
    if not event.widget.curselection() or secwin:
        return
    i = event.widget.curselection()[0]
    key = keys['private'][i]
    
    editprikeywin = tk.Toplevel(root)
    editprikeywin.bind("<Destroy>", secwin_closed)
    secwin = editprikeywin
    editprikeywin.title("Edit Private Key")
    
    frame_pri_name = tk.Frame(editprikeywin)
    tk.Label(frame_pri_name, text="Name:").grid(row=0,column=0)
    prikeyname = tk.Entry(frame_pri_name)
    prikeyname.insert(tk.END, key['name'])
    prikeyname.grid(row=0,column=1)
    frame_pri_name.pack(anchor=tk.W)
    
    frame_pri_key = tk.Frame(editprikeywin)
    tk.Label(frame_pri_key, text="Private Key:").pack()
    prikey = tk.Text(frame_pri_key)
    prikey.insert(tk.END, key['key'])
    prikey.pack()
    frame_pri_key.pack()
    
    def save_key_btn():
        if (key['name'] == prikeyname.get() or key['key'] == prikey.get('1.0', 'end-1c')):
            key['name'] = prikeyname.get()
            key['key'] = prikey.get('1.0', 'end-1c')
            prikeyslist.delete(i)
            prikeyslist.insert(i, key['name'])
            save_keys()
            editprikeywin.destroy()
    def del_key_btn():
        del keys['private'][i]
        prikeyslist.delete(i)
        save_keys()
        editprikeywin.destroy()
    
    frame_pri_btn = tk.Frame(editprikeywin, pady=10)
    tk.Button(frame_pri_btn, width=10, text='Save', bg='green', command=save_key_btn).grid(row=0,column=0, ipadx=10, padx=5)
    tk.Button(frame_pri_btn, width=10, text='Delete', bg='red', command=del_key_btn).grid(row=0,column=1,ipadx=10, padx=5)
    frame_pri_btn.pack()
    return

def chanselection(event):
    global secwin
    if not event.widget.curselection() or secwin:
        return
    i = event.widget.curselection()[0]
    chanid = event.widget.get(i)
    chan = keys['public'][chanid]
    
    chanwin = tk.Toplevel(root)
    chanwin.bind("<Destroy>", secwin_closed)
    secwin = chanwin
    chanwin.title("Edit Channel Public Key")
    
    frame_chan_id = tk.Frame(chanwin)
    tk.Label(frame_chan_id, text="Channel ID:").grid(row=0,column=0)
    lbl_chan_id = tk.Label(frame_chan_id, text=chanid, fg="blue", cursor="hand2")
    lbl_chan_id.grid(row=0,column=1)
    lbl_chan_id.bind("<Button-1>", lambda e: webbrowser.open_new(f"https://discord.com/channels/@me/{chanid}"))
    frame_chan_id.pack(anchor=tk.W)
    
    frame_pubkeys = tk.Frame(chanwin)
    tk.Label(frame_pubkeys, text="Public Keys:").pack()
    pubkeyslist = tk.Listbox(frame_pubkeys)
    
    def publicselection(event):
        global secwin, trdwin
        if not event.widget.curselection() or not secwin or trdwin:
            return
        j = event.widget.curselection()[0]
        key = chan[j]
        
        editpubkeywin = tk.Toplevel(chanwin)
        editpubkeywin.bind("<Destroy>", trdwin_closed)
        trdwin = editpubkeywin
        editpubkeywin.title("Edit Public Key")
        
        frame_pub_name = tk.Frame(editpubkeywin)
        tk.Label(frame_pub_name, text="Name:").grid(row=0,column=0)
        pubkeyname = tk.Entry(frame_pub_name)
        pubkeyname.insert(tk.END, key['name'])
        pubkeyname.grid(row=0,column=1)
        frame_pub_name.pack(anchor=tk.W)
        
        frame_pub_key = tk.Frame(editpubkeywin)
        tk.Label(frame_pub_key, text="Private Key:").pack()
        pubkey = tk.Text(frame_pub_key)
        pubkey.insert(tk.END, key['key'])
        pubkey.pack()
        frame_pub_key.pack()
        
        def save_key_btn():
            if (key['name'] == pubkeyname.get() or key['key'] == pubkey.get('1.0', 'end-1c')):
                key['name'] = pubkeyname.get()
                key['key'] = pubkey.get('1.0', 'end-1c')
                pubkeyslist.delete(i)
                pubkeyslist.insert(i, key['name'])
                save_keys()
                editpubkeywin.destroy()
        def del_key_btn():
            del chan[j]
            pubkeyslist.delete(i)
            save_keys()
            editpubkeywin.destroy()
        
        frame_pub_btn = tk.Frame(editpubkeywin, pady=10)
        tk.Button(frame_pub_btn, width=10, text='Save', bg='green', command=save_key_btn).grid(row=0,column=0, ipadx=10, padx=5)
        tk.Button(frame_pub_btn, width=10, text='Delete', bg='red', command=del_key_btn).grid(row=0,column=1,ipadx=10, padx=5)
        frame_pub_btn.pack()
    
    pubkeyslist.bind('<<ListboxSelect>>', publicselection)
    for key in chan:
        pubkeyslist.insert(tk.END, key['name'] if key['name'] != "" else "Untitled")
    pubkeyslist.pack(fill='x')
    
    def addprivate():
        global secwin, trdwin
        if not secwin or trdwin:
            return
        key = {'name':'', 'key':''}
        
        addpubwin = tk.Toplevel(chanwin)
        addpubwin.bind("<Destroy>", trdwin_closed)
        trdwin = addpubwin
        addpubwin.title("Add Public Key")
        
        frame_pub_name = tk.Frame(addpubwin)
        tk.Label(frame_pub_name, text="Name:").grid(row=0,column=0)
        pubkeyname = tk.Entry(frame_pub_name)
        pubkeyname.insert(tk.END, key['name'])
        pubkeyname.grid(row=0,column=1)
        frame_pub_name.pack(anchor=tk.W)
        
        frame_pub_key = tk.Frame(addpubwin)
        tk.Label(frame_pub_key, text="Private Key:").pack()
        pubkey = tk.Text(frame_pub_key)
        pubkey.insert(tk.END, key['key'])
        pubkey.pack()
        frame_pub_key.pack()
        
        def save_key_btn():
            if (pubkey.get('1.0', 'end-1c') != ''):
                key['name'] = pubkeyname.get()
                key['key'] = pubkey.get('1.0', 'end-1c')
                pubkeyslist.insert(tk.END, key['name'] if key['name'] != "" else "Untitled")
                chan.append(key)
                save_keys()
                addpubwin.destroy()
        
        frame_pub_btn = tk.Frame(addpubwin, pady=10)
        tk.Button(frame_pub_btn, width=10, text='Save', bg='green', command=save_key_btn).pack()
        frame_pub_btn.pack()
        return
    
    def delchan():
        del keys['public'][chanid]
        chanslist.delete(i)
        save_keys()
        chanwin.destroy()
    
    frame_chan_keys_btns = tk.Frame(frame_pubkeys)
    tk.Button(frame_chan_keys_btns, width=10, text='Add Key', bg="lightblue", command=addprivate).grid(row=0, column=0)
    tk.Button(frame_chan_keys_btns, width=10, text='Delete Channel', bg="red", command=delchan).grid(row=0, column=1)
    frame_chan_keys_btns.pack()
    
    frame_pubkeys.pack()
    return

frame1 = tk.Frame(root, padx=20)
interact_button = tk.Button(frame1, bg='green', text="Start mitmproxy", command=interact_with_mitmproxy)
interact_button.pack(pady=5)
import tkinter.font as tkfont
custom_font = tkfont.Font(size=15)
lbl_discord = tk.Label(frame1, pady=5, text="Open Discord", font=custom_font, fg="blue", cursor="hand2")
lbl_discord.bind("<Button-1>", lambda e: webbrowser.open_new(f"https://discord.com/app"))
lbl_discord.pack()
frame1.pack()

frame2 = tk.Frame(root, padx=20, pady=5)

frameL = tk.Frame(frame2, padx=20)
tk.Label(frameL, text="Private Keys").pack()
prikeyslist = tk.Listbox(frameL)
prikeyslist.bind('<<ListboxSelect>>', privateselection)
for key in keys['private']:
    prikeyslist.insert(tk.END, key['name'] if key['name'] != "" else "Untitled")
prikeyslist.pack()

def addprivate():
    global secwin
    if secwin:
        return
    key = {'name':'', 'key':''}
    
    addpriwin = tk.Toplevel(root)
    addpriwin.bind("<Destroy>", secwin_closed)
    secwin = addpriwin
    addpriwin.title("Add Private Key")
    
    frame_pri_name = tk.Frame(addpriwin)
    tk.Label(frame_pri_name, text="Name:").grid(row=0,column=0)
    prikeyname = tk.Entry(frame_pri_name)
    prikeyname.grid(row=0,column=1)
    frame_pri_name.pack(anchor=tk.W)
    
    frame_pri_key = tk.Frame(addpriwin)
    tk.Label(frame_pri_key, text="Private Key:").pack()
    prikey = tk.Text(frame_pri_key)
    prikey.pack()
    frame_pri_key.pack()
    
    def save_key_btn():
        if (prikey.get('1.0', 'end-1c') != ''):
            key['name'] = prikeyname.get()
            key['key'] = prikey.get('1.0', 'end-1c')
            prikeyslist.insert(tk.END, key['name'] if key['name'] != "" else "Untitled")
            keys['private'].append(key)
            save_keys()
            addpriwin.destroy()
    
    frame_pri_btn = tk.Frame(addpriwin, pady=10)
    tk.Button(frame_pri_btn, width=10, text='Save', bg='green', command=save_key_btn).grid(row=0,column=0, ipadx=10, padx=5)
    frame_pri_btn.pack()
    return

tk.Button(frameL, text='Add Key', bg="lightblue", command=addprivate).pack(pady=10)
frameL.grid(row=0, column=0, sticky=tk.N)

frameR = tk.Frame(frame2, padx=20)
tk.Label(frameR, text="Channels' IDs").pack()
chanslist = tk.Listbox(frameR)
chanslist.bind('<<ListboxSelect>>', chanselection)
for chan in keys['public']:
    chanslist.insert(tk.END, chan)
chanslist.pack()

def addchan():
    global secwin
    if secwin:
        return
    
    addchanwin = tk.Toplevel(root)
    addchanwin.bind("<Destroy>", secwin_closed)
    secwin = addchanwin
    addchanwin.title("New Channel")
    
    frame_chan_id = tk.Frame(addchanwin)
    tk.Label(frame_chan_id, text="Channel's ID:").grid(row=0,column=0)
    chanid = tk.Entry(frame_chan_id)
    chanid.grid(row=0,column=1)
    frame_chan_id.pack(anchor=tk.W)
    
    def save_chan_btn():
        chan = chanid.get()
        if (chan != '' and chan.isdigit()):
            chan = chanid.get()
            chanslist.insert(tk.END, chan)
            keys['public'][chan] = []
            save_keys()
            addchanwin.destroy()
    
    frame_chan_btn = tk.Frame(addchanwin, pady=10)
    tk.Button(frame_chan_btn, width=10, text='Save', bg='green', command=save_chan_btn).grid(row=0,column=0, ipadx=10, padx=5)
    frame_chan_btn.pack()
    return
tk.Button(frameR, text='New Channel', bg="lightgreen", command=addchan).pack(pady=10)
frameR.grid(row=0, column=1, sticky=tk.N)

frame2.pack()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
