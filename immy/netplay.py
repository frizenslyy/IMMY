"""IMMY — битва с другом по локальной сети: обнаружение компьютеров (UDP) и синхронизация боя (TCP)."""

import json
import socket
import threading
import time
import uuid

from .config import NET_DISCOVER_PORT, NET_FIGHT_PORT, NET_SCAN_TIMEOUT

REQ = "IMMY_DISCOVER:"
ANS = "IMMY_HERE:"


def host_name():
    try:
        return (socket.gethostname() or "PC").split(".")[0][:22] or "PC"
    except Exception:
        return "PC"


def _send(conn, obj):
    try:
        conn.sendall((json.dumps(obj) + "\n").encode())
        return True
    except OSError:
        return False


class Discovery:
    """Фоновое обнаружение компьютеров в локальной сети через UDP-широковещание."""

    def __init__(self):
        self.sid = uuid.uuid4().hex[:8]
        self.peers = {}
        self.hosting = False
        self._lock = threading.Lock()
        self._run = True
        self.sock = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except OSError:
                pass
            s.bind(("", NET_DISCOVER_PORT))
            s.settimeout(0.25)
            self.sock = s
            self.hosting = True
        except OSError:
            self.sock = None
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        while self._run:
            sock = self.sock
            if sock is None:
                break
            try:
                data, addr = sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break
            msg = data.decode("utf-8", "ignore")
            if msg.startswith(REQ):
                rest = msg[len(REQ):]
                sid, _, name = rest.partition("|")
                if sid != self.sid:
                    with self._lock:
                        self.peers[addr[0]] = (name[:22] or "PC", time.time())
                    self._reply(addr)
            elif msg.startswith(ANS):
                sid, _, name = msg[len(ANS):].partition("|")
                if sid != self.sid:
                    with self._lock:
                        self.peers[addr[0]] = (name[:22] or "PC", time.time())

    def _reply(self, addr):
        try:
            self.sock.sendto((ANS + self.sid + "|" + host_name()).encode(), addr)
        except OSError:
            pass

    def scan(self):
        out = {}
        msg = (REQ + self.sid + "|" + host_name()).encode()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(0.1)
            for tgt in (("<broadcast>", NET_DISCOVER_PORT), ("127.0.0.1", NET_DISCOVER_PORT)):
                try:
                    s.sendto(msg, tgt)
                except OSError:
                    pass
            deadline = time.time() + NET_SCAN_TIMEOUT
            while time.time() < deadline:
                try:
                    data, addr = s.recvfrom(2048)
                except socket.timeout:
                    continue
                except OSError:
                    break
                m = data.decode("utf-8", "ignore")
                if m.startswith(ANS):
                    sid, _, name = m[len(ANS):].partition("|")
                    if sid != self.sid:
                        out[addr[0]] = name[:22] or "PC"
            s.close()
        except OSError:
            pass
        with self._lock:
            now = time.time()
            for ip, (name, t) in list(self.peers.items()):
                if now - t < 8.0:
                    out.setdefault(ip, name)
                else:
                    del self.peers[ip]
        return sorted(out.items(), key=lambda kv: kv[1].lower())

    def close(self):
        self._run = False
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None


class _LineConn:
    """Приём newline-JSON сообщений с неблокирующего сокета."""

    def __init__(self):
        self.conn = None
        self._buf = b""
        self.queue = []
        self._lock = threading.Lock()

    @property
    def connected(self):
        return self.conn is not None

    def _recv_loop(self):
        while self.conn is not None:
            try:
                data = self.conn.recv(65536)
            except BlockingIOError:
                return
            except OSError:
                self.drop()
                return
            if not data:
                self.drop()
                return
            self._buf += data
            while b"\n" in self._buf:
                line, self._buf = self._buf.split(b"\n", 1)
                try:
                    msg = json.loads(line.decode("utf-8", "ignore"))
                except ValueError:
                    continue
                with self._lock:
                    self.queue.append(msg)

    def poll(self):
        conn = self.conn
        if conn is None:
            return []
        self._recv_loop()
        with self._lock:
            q = self.queue
            self.queue = []
        return q

    def send(self, obj):
        return self.conn is not None and _send(self.conn, obj)

    def drop(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except OSError:
                pass
            self.conn = None


class Host(_LineConn):
    """Хост: принимает подключение гостя, получает его ввод, отдаёт снапшоты боя."""

    def __init__(self):
        super().__init__()
        self.addr = None
        self.alive = True
        self.srv = None
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("", NET_FIGHT_PORT))
            srv.listen(1)
            srv.settimeout(0.2)
            self.srv = srv
        except OSError:
            self.srv = None
            self.alive = False
            return
        self._thread = threading.Thread(target=self._accept, daemon=True)
        self._thread.start()

    def _accept(self):
        while self.alive and self.conn is None:
            try:
                conn, addr = self.srv.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            conn.settimeout(0.0)
            self.addr = addr[0]
            self.conn = conn

    def close(self):
        self.alive = False
        self.drop()
        if self.srv is not None:
            try:
                self.srv.close()
            except OSError:
                pass
            self.srv = None


class Client(_LineConn):
    """Гость: подключается к хосту, шлёт свой ввод, получает снапшоты боя."""

    def __init__(self):
        super().__init__()
        self.sock = None

    def connect(self, ip, timeout=2.5):
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, NET_FIGHT_PORT))
            s.settimeout(0.0)
            self.sock = s
            self.conn = s
            return True
        except OSError:
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
            return False

    def drop(self):
        super().drop()
        self.sock = None

    def close(self):
        self.drop()
