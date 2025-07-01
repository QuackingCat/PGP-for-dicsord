from mitmproxy import http, websocket, ctx
from pgpy import PGPKey, PGPMessage, constants
from threading import Thread
from time import sleep
import re, json, os, zlib, queue, asyncio

decompressors = {}
compressors = {}
ws_buffers = {}
ZLIB_SUFFIX = b"\x00\x00\xff\xff"

PRIVATE_KEYS = [] # [...,{key:PGPKeyObject, "pass":"<password>"},...]
PUBLIC_KEYS = {} # {...,"<channel id>":[...,PGPKeyObject,...],...}

event_queue = queue.Queue()

file_path = "my_file.txt"

if not os.path.exists('keys.json'):
    with open('keys.json', 'w') as f:
        f.write('{"private":[], "public":{}}')

def loadkeys(path: str):
    global PRIVATE_KEYS
    global PUBLIC_KEYS
    with open(path, "r") as f:
        keys = json.loads(f.read())
        TEMP_PRIVATE_KEYS = []
        for key in keys["private"]:
            try:
                TEMP_PRIVATE_KEYS.append({"key":PGPKey.from_blob(key['key'])[0], "pass":""})
            except:
                pass#event_queue.put(("error", f"Couldn't parse PRIVATE key: {key['name']}"))
        TEMP_PUBLIC_KEYS = {} 
        for chan in keys["public"].keys():
            if not TEMP_PUBLIC_KEYS.get(chan):
                TEMP_PUBLIC_KEYS[chan] = []
            for key in keys['public'][chan]:
                try:
                    TEMP_PUBLIC_KEYS[chan].append(PGPKey.from_blob(key['key'])[0])
                except:
                    pass#event_queue.put(("error", f"Couldn't parse PUBLIC key: {key['name']}"))
        PRIVATE_KEYS = TEMP_PRIVATE_KEYS
        PUBLIC_KEYS = TEMP_PUBLIC_KEYS

def filewatcher(path: str):
    keysmtime = 0
    while True:
        try:
            m = os.path.getmtime(path)
            if keysmtime < m:
                event_queue.put(("info", f'Loading {path}'))
                keysmtime = m
                loadkeys(path)
        except Exception as e:
            event_queue.put(("error", str(e)))
        sleep(1)

class AsyncioPeriodicTaskAddon:
    def __init__(self):
        pass

    async def _my_periodic_task(self):
        while True:
            try:
                while not event_queue.empty():
                    event_type, message = event_queue.get_nowait()
                    if event_type == "info":
                        ctx.log.info(message)
                    elif event_type == "error":
                        ctx.log.error(message)
            except Exception as e:
                ctx.log.error(e)
            await asyncio.sleep(1)

    def load(self, entrypoint):
        asyncio.create_task(self._my_periodic_task())

    def done(self):
        pass

addons = [
    AsyncioPeriodicTaskAddon()
]

filewatcherthread = Thread(target=filewatcher, args=("keys.json",), daemon=True)
filewatcherthread.start()

PGP_BLOCK_RE = re.compile(
    r"(-----BEGIN PGP MESSAGE-----(?:\\n|\n)(?:.*?(?:\\n|\n))*?-----END PGP MESSAGE-----)",
    re.DOTALL
)

def decrypt_pgp_block(pgp_block: str) -> str:
    try:
        msg = PGPMessage.from_blob(pgp_block.replace('\\n', '\n'))
        
        for key in PRIVATE_KEYS:
            if key['key'].is_unlocked:
                try:
                    decrypted = key['key'].decrypt(msg)
                    return str(decrypted.message)
                except:
                    continue
    except Exception as e:
        ctx.log.error(f"PGP Decryption failed: {e}")
    return pgp_block  # fallback

def encrypt_message(plaintext: str, channel: str) -> str:
    try:
        if plaintext == "":
            return ""
        msg = PGPMessage.new(plaintext)
        cipher = constants.SymmetricKeyAlgorithm.AES256
        sessionkey = cipher.gen_key()
        
        for key in PUBLIC_KEYS[channel]:
            msg = key.encrypt(msg, cipher=cipher, sessionkey=sessionkey)
        
        del sessionkey

        return str(msg)
    except Exception as e:
        ctx.log.error(f"PGP Encryption failed: {e}")
        return plaintext

def replace_pgp_in_text(text: str) -> str:
    return PGP_BLOCK_RE.sub(lambda m: decrypt_pgp_block(m.group(1)), text)

def response(flow: http.HTTPFlow):
    if "discord.com" in flow.request.pretty_host or "discord.gg" in flow.request.pretty_host:
        try:
            content_type = flow.response.headers.get("content-type", "")
            if "application/json" in content_type:
                content = flow.response.get_text()
                modified = replace_pgp_in_text(content)
                if content != modified:
                    ctx.log.info("[*] Replaced PGP block in HTTP response")
                    flow.response.set_text(modified)
        except Exception as e:
            ctx.log.error("Error in HTTP response:", e)

def request(flow: http.HTTPFlow):
    m = re.search(r"/channels/(\d+)/messages", flow.request.path)
    if ("discord.com" in flow.request.pretty_host or "discord.gg" in flow.request.pretty_host) and (flow.request.method == "POST" or flow.request.method == "PATCH") and m:
        try:
            content_type = flow.request.headers.get("content-type", "")
            if "application/json" in content_type:
                chan = m.group(1)
                data = json.loads(flow.request.get_text())
                if "content" in data and not data["content"].startswith("-----BEGIN PGP") and PUBLIC_KEYS.get(chan):
                    plaintext = data["content"]
                    encrypted = encrypt_message(plaintext, chan)
                    data["content"] = encrypted
                    flow.request.set_text(json.dumps(data))
                    ctx.log.info("[*] Encrypted outgoing message")
        except Exception as e:
            ctx.log.error("Error in HTTP request:", e)
         

def websocket_start(flow):
    if flow.server_conn.address[0].startswith("gateway") and flow.server_conn.address[0].endswith(".discord.gg"):
        decompressors[flow.id] = zlib.decompressobj()
        compressors[flow.id] = zlib.compressobj(wbits=15)
        ws_buffers[flow.id] = b""
        ctx.log.info(f"[*] WebSocket started: {flow.id}")

def websocket_end(flow):
    decompressors.pop(flow.id, None)
    compressors.pop(flow.id, None)
    ws_buffers.pop(flow.id, None)
    ctx.log.info(f"[*] WebSocket ended: {flow.id}")

def websocket_message(flow):
    msg = flow.websocket.messages[-1]
    decompressor = decompressors.get(flow.id)
    compressor = compressors.get(flow.id)
    
    if not (flow.request.pretty_host.endswith('.discord.gg') and flow.request.pretty_host.startswith('gateway')):
        return
    
    if not decompressor:
        return
    
    # Server → Client
    if not msg.from_client:
        ws_buffers[flow.id] += msg.content
        if not ws_buffers[flow.id].endswith(ZLIB_SUFFIX):
            return
        try:
            data = decompressor.decompress(ws_buffers[flow.id])
            ws_buffers[flow.id] = b""
            try:
                text = data.decode("utf-8")
                if "-----BEGIN PGP MESSAGE-----" in text:
                    text = replace_pgp_in_text(text)
                recompressed = compressor.compress(text.encode("utf-8"))
                recompressed += compressor.flush(zlib.Z_SYNC_FLUSH)
                msg.content = recompressed
                #ctx.log.info("[*] Relayed WebSocket message")
            except UnicodeDecodeError:
                pass  # Not text
        except Exception as e:
            ctx.log.error("WebSocket decompression failed:", e)
        return
    # Client → Server
    else: #msg.from_client
        # currently the client doesn't send any msg content using websockets
        return
    ctx.log.error("what the hell")
