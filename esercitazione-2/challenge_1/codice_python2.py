import subprocess, re
from collections import defaultdict

streams = {7,28,29,35,37,48,69,84,88,112,121,122,137,140,161,170,173,174,177,181,197,198,214,222}

out = subprocess.run(
    ["tshark", "-r", "capture-7.pcap", "-Y", "http.request",
     "-T", "fields", "-e", "tcp.stream", "-e", "http.request.line"],
    capture_output=True, text=True).stdout

pieces = defaultdict(set)
for line in out.splitlines():
    s, _, rest = line.partition("\t")
    if not s.isdigit() or int(s) not in streams:
        continue
    for n, h in re.findall(r"X-Trace:\s*(\d)-([0-9a-fA-F]{6})", rest):
        pieces[int(n)].add(h.lower())

for n in sorted(pieces):
    print(n, pieces[n])

if sorted(pieces) == list(range(1, 9)) and all(len(v) == 1 for v in pieces.values()):
    token = "".join(next(iter(pieces[n])) for n in range(1, 9))
    print(len(token), "netsec{%s}" % token)
