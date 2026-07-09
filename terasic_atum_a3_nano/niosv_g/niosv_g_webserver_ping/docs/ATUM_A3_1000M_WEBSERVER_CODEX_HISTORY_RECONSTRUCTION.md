# Atum A3 Nano 1000M Webserver Codex History Reconstruction

Date: 2026-07-09

This report reconstructs the working Atum A3 Nano 1000M FreeRTOS/TSE webserver
design from the Codex session history, working backward from passing hardware
results.  It intentionally does not use Git commits as authoritative evidence,
because the working hardware design was not fully captured by the commit
history.

Primary Codex history source:

```text
/home/dev/.codex/sessions/2026/07/09/rollout-2026-07-09T02-26-51-019f44b3-080d-7cb1-b2bb-5ff5afe6e6ff.jsonl
```

Primary design tree:

```text
/home/dev/Atum/agilex3c-nios-ed-hw-baseline/terasic_atum_a3_nano/niosv_g/niosv_g_webserver_ping
```

## Bottom Line

The working design was the local `agilex3c-nios-ed-hw-baseline` FreeRTOS/TSE
webserver project, not the clean AEW2015 clone and not a state proven by Git
history alone.

The passing trail in Codex history is:

```text
041523Z_ag3_bg_host       Altera XRDP background website served, 200 OK
040646Z_desktop_bg_inline First inline background website served, 200 OK
033909Z_colorbars         Color-bar website served, 200 OK
032245Z                   Simple HTTP server served, 200 OK
030902Z                   UDP host->FPGA->host loopback passed 5/5
023408Z                   FreeRTOS 1000M network smoke partly passed, clean MAC errors
02:29-02:32               Held-open eval programmer wrappers created
```

The necessary ingredients, as reconstructed from the transcript and logs, were:

```text
1. Hold quartus_pgm open at the eval prompt during hardware tests.
2. Use the hw-baseline SOF:
   sources/hw/output_files/top_time_limited.sof
3. Use the hw-baseline app ELF built from the local FreeRTOS app sources.
4. Keep TSE in 1000M mode: set_1000=1, ena_10=0, eth_mode=1.
5. Clear stale DP83867 diagnostic/loopback state before autoneg.
6. Configure DP83867 1000M full-duplex autoneg and RGMII delays.
7. Clear normal TSE MAC loopback before enabling TX/RX.
8. Add FreeRTOS UDP loopback and then TCP HTTP server tasks.
9. Embed page assets directly in HTML for single-request reliability.
10. Validate each hardware run with manifest hashes, UART, ping/ARP, HTTP, and MAC counters.
```

## Chunk 1: Latest Passing Background Website

Codex history lines:

```text
1415  Hosted Altera XRDP-background website
1440  Rendered PNG of hosted Altera XRDP-background page
1525  Reset made curl work again
```

Passing run:

```text
RUN_ID: 20260709T041523Z_ag3_bg_host
Page:   http://10.0.0.2/
Asset:  /usr/share/backgrounds/ag3-wallpaper.png
Mode:   image compressed and embedded directly in HTML
```

Evidence:

```text
logs/tse_eval_http_server_20260709T041523Z_ag3_bg_host.log
logs/tse_eval_http_server_20260709T041523Z_ag3_bg_host_http.log
logs/tse_eval_http_server_20260709T041523Z_ag3_bg_host_juart.log
logs/tse_eval_http_server_20260709T041523Z_ag3_bg_host.html
logs/tse_eval_http_server_20260709T041523Z_ag3_bg_host.png
```

Codex recorded this hardware result:

```text
HTTP/1.1 200 OK
response 22112 bytes
body 21986 bytes
firmware sent body 21986
frames_check_sequence_errors = 0x0
alignment_errors = 0x0
JTAG clock 6 MHz
Eval programmer still held open
```

The page was rendered into:

```text
logs/tse_eval_http_server_20260709T041523Z_ag3_bg_host.png
```

Later, when the host path stopped answering fresh HTTP, Codex checked that the
FPGA was still running from JTAG/UART evidence and then reset/relaunched the
held-open wrapper.  The reset run made this curl command work:

```sh
curl --interface enp5s0 --connect-timeout 5 --max-time 15 \
  -D /tmp/atum_reset_curl_headers.txt \
  -o /tmp/atum_reset_page.html \
  http://10.0.0.2/
```

Reset verification:

```text
HTTP/1.1 200 OK
Content-Length: 21986
Eval programmer still held open
JTAG clock 6 MHz
JTAG nodes visible: Source/Probe, Nios V, JTAG UART
Run ID: 20260709T043913Z_ag3_bg_reset_host
```

## Chunk 2: How The XRDP Background Was Chosen

Codex history lines:

```text
1360  Identified /usr/share/backgrounds/ag3-wallpaper.png
1366  Switched served page to the Altera XRDP background
1415  Hosted AG3/XRDP background website
```

The history shows Codex searched the container for desktop/XRDP backgrounds and
identified:

```text
/usr/share/backgrounds/ag3-wallpaper.png
```

It was a `1920 x 1080` PNG labeled:

```text
Agilex 3 Development Workspace / Quartus Prime Pro / FPGA AI Suite / Nios V / XRDP
```

The transcript then says the page was changed to embed a compressed version of
that image directly in the HTML.  In the current source tree, the app references:

```text
sources/sw/app_freertos/desktop_background_image.h
sources/sw/app_freertos/main.c
```

The current app ELF also contains strings for:

```text
Atum A3 Nano
FreeRTOS + TSE small MAC is serving the Altera XRDP background.
GET /bg.jpg
[HTTP] serving simple HTML on FPGA port %u
[UDP] loopback task bound on FPGA port %u
DP83867 diag clear: BMCR=0x%04X BISCR=0x%04X LOOPCR=0x%04X
```

## Chunk 3: Previous Inline Background Pass

Codex history lines:

```text
1313  Hosted desktop background embedded directly in HTML
1339  Rendered latest hosted desktop-background page to PNG
```

Passing run:

```text
RUN_ID: 20260709T040646Z_desktop_bg_inline_host
Source: /usr/share/desktop-base/emerald-theme/wallpaper/contents/images/5120x2880.svg
```

Codex recorded:

```text
HTTP/1.1 200 OK
body 5927 bytes
FCS errors 0
alignment errors 0
Eval programmer still held open
JTAG clock 6 MHz
```

This is the immediate predecessor to the Altera XRDP-background version.  The
important design lesson from this chunk is that embedding the background in the
HTML made the page single-request and reliable enough for the small server.

## Chunk 4: Color Bars Website Pass

Codex history lines:

```text
1036  Color-bars page served on hardware
1083  Color-bars page hosted live for one hour
1109  Color-bars PNG rendered
```

Passing run:

```text
RUN_ID: 20260709T033909Z_colorbars
```

Evidence:

```text
logs/tse_eval_http_server_20260709T033909Z_colorbars.html
logs/tse_eval_http_server_20260709T033909Z_colorbars.log
logs/tse_eval_http_server_20260709T033909Z_colorbars_http.log
logs/tse_eval_http_server_20260709T033909Z_colorbars_juart.log
logs/tse_eval_http_server_20260709T033909Z_colorbars.png
```

Codex recorded:

```text
HTTP/1.1 200 OK
response 772 bytes
body 648 bytes
MAC FCS errors 0
alignment errors 0
JTAG clock 6 MHz
programmer closed cleanly after short test
```

Then a long-held run hosted it for one hour:

```text
RUN_ID: 20260709T035122Z_colorbars_host
HTTP/1.1 200 OK
body 648 bytes
JTAG clock 6 MHz
FCS errors 0
alignment errors 0
```

This chunk proves the HTTP server was already working before any background
image payload was added.

## Chunk 5: First Simple HTTP Server Pass

Codex history lines:

```text
683-724  TCP options and reset/debug attempts
737-889  rebuild, rerun, pass
892      final summary of simple HTTP server pass
```

Passing run:

```text
RUN_ID: 20260709T032245Z
```

Codex recorded:

```text
HTTP fetch: HTTP/1.1 200 OK
response: 304 bytes total
HTML body: 180 bytes
host ping: 4/4, 0% packet loss
MAC FCS errors: 0
alignment errors: 0
JTAG clock: 6 MHz
debug nodes: Source/Probe, Nios V, JTAG UART
```

Files changed in this chunk according to the history:

```text
sources/sw/app_freertos/main.c
run_tse_eval_http_server.sh
```

Behavior added:

```text
FreeRTOS TCP HTTP server on FPGA port 80.
Static HTML body containing "Atum A3 Nano".
Held-open eval wrapper HTTP test that programs, downloads ELF, pings, fetches,
logs, and optionally holds the server alive with HTTP_HOLD_SECONDS.
```

Important debugging trail:

```text
Earlier HTTP attempts reached ping but saw TCP reset or fetch timeout.
The wrapper was changed to retry HTTP and keep a UART tail after failures.
The app/server was changed until the host fetch returned HTTP/1.1 200 OK.
```

## Chunk 6: UDP Loopback Pass

Codex history lines:

```text
533  UDP loopback implemented and tested
```

Passing run:

```text
RUN_ID: 20260709T030902Z
SOF SHA256: 40b92e2259a97a7d141d390675e3537186fe3b1bf84b2fcb62c1968e309a07b4
ELF SHA256: 7e3ce8f79b9916121151f5fa467bd3b7e5f90d8b8d32f085ebd3558b7be74aab
```

Evidence:

```text
logs/tse_eval_udp_loopback_20260709T030902Z_manifest.txt
logs/tse_eval_udp_loopback_20260709T030902Z_host.log
logs/tse_eval_udp_loopback_20260709T030902Z_udp.log
logs/tse_eval_udp_loopback_20260709T030902Z_juart.log
logs/tse_eval_udp_loopback_20260709T030902Z.log
```

Codex recorded:

```text
Host ping: 4/4, 0% packet loss
UDP loopback: ok=5 count=5
All datagrams succeeded on first attempt
FPGA echoed 20-byte packets with echo result 20
1000M mode: ena_10=0 eth_mode=1
JTAG clock: 6 MHz
frames_check_sequence_errors = 0x0
alignment_errors = 0x0
```

Files changed in this chunk according to the history:

```text
sources/sw/app_freertos/main.c
run_tse_eval_udp_loopback.sh
```

Behavior added:

```text
Dedicated FreeRTOS UDP loopback task on FPGA port 5002.
Host sends to 10.0.0.2:5002 from 10.0.0.1:5002.
FPGA echoes exact payload back to host source port.
```

This is the first clean host-to-FPGA-to-host application proof in the backward
chain.  HTTP was built on top of this known-working network path.

## Chunk 7: FreeRTOS 1000M Network Smoke

Codex history lines:

```text
273  Comparison of programmer-off versus held-open eval wrapper
385  Full FreeRTOS 1000M stack report
```

Important run:

```text
RUN_ID: 20260709T023408Z
SOF SHA256: 40b92e2259a97a7d141d390675e3537186fe3b1bf84b2fcb62c1968e309a07b4
ELF SHA256: ae3acfa0ab9f0298bbfb5a1ea31d1198fdfaa7a90251fabd4fa5ad4fe7a624d1
```

Evidence:

```text
logs/tse_eval_network_smoke_20260709T023408Z_manifest.txt
logs/tse_eval_network_smoke_20260709T023408Z_host.log
logs/tse_eval_network_smoke_20260709T023408Z_juart.log
logs/tse_eval_network_smoke_20260709T023408Z.log
logs/freertos_1000m_full_stack_report_20260709T024659Z.md
```

Codex recorded:

```text
Eval prompt held open: PASS
JTAG clock: 6 MHz
JTAG nodes: 08086E00, 00486E00, 08986E00, 0C006E00
1000M ISSP mode: ena_10=0, eth_mode=1
PHY/link/IP bring-up: PASS
FPGA IP: 10.0.0.2
FPGA-originated ping to host: PASS
FPGA UDP proof datagrams to host: PASS, 3 datagrams received
Host ping to FPGA: PARTIAL, improved from INCOMPLETE to reachable/partial replies
Host UDP echo to FPGA: FAIL at that stage
MAC errors: frames_check_sequence_errors=0x0, alignment_errors=0x0
```

The host log for `023408Z` showed:

```text
8 transmitted, 3 received
10.0.0.2 lladdr 02:cf:46:29:04:b4 STALE
```

The UART log showed the key hardware/software bring-up features that later
website runs also depended on:

```text
Hello FreeRTOS from main...
DP83867 diag clear: BMCR=0x1140 BISCR=0x0000 LOOPCR=0xE721
Configuring DP83867 for 10/100/1000 autonegotiation
Link up successful
PHY link is UP.
IP Address: 10.0.0.2
UDP proof task active
Ping replies received
MAC counters increasing
frames_check_sequence_errors = 0x0
alignment_errors = 0x0
```

This chunk establishes that the 1000M FreeRTOS stack was alive before UDP
loopback and HTTP were added.

## Chunk 8: Held-open Eval Programmer Scripts

Codex history lines:

```text
86-169  Creation and validation of held-open eval scripts
```

Files added or changed according to the history:

```text
terasic_atum_a3_nano/tse_jtag_maconly/scripts/with_eval_programmer.py
terasic_atum_a3_nano/tse_jtag_maconly/scripts/run_eval_boundary_compare.sh
terasic_atum_a3_nano/niosv_g/niosv_g_webserver_ping/run_tse_eval_network_smoke.sh
terasic_atum_a3_nano/tse_jtag_maconly/TSE_25_3_1_FULL_TEST_PLAN.md
```

Behavior added:

```text
Program time-limited SOF.
Wait until quartus_pgm reaches the OpenCore eval prompt.
Keep quartus_pgm alive while the hardware test runs.
Set JTAG clock to 6M.
Run the supplied test command.
Send q only during cleanup.
```

Validation recorded in history:

```text
python3 -m py_compile with_eval_programmer.py passed.
bash -n on shell wrappers passed.
Vendor TSE simulation passed with RESULT: PASS and TB_PACKET_DONE PASS.
The test plan was updated to stop piping q before the hardware test.
The test plan was updated to avoid --program when the wrapper owns programming.
```

This was necessary for the FreeRTOS/TSE eval design.  Codex later recorded that
the held-open wrapper improved the Nios-V path from `INCOMPLETE`/no host replies
to learned ARP and partial/full host replies, while it did not fix the separate
processor-free MAC/RGMII boundary failure.

## File-level Changes Inferred From History And Current Tree

The following are not inferred from Git commits.  They come from the Codex
history summaries, current file contents, strings in the current ELF, and the
hardware logs.

### `sources/sw/AlteraTSE/tse_driver.c`

Required behavior:

```text
Clear DP83867 diagnostics before autoneg:
  BMCR loopback bit cleared.
  BISCR loopback-mode bits cleared.
  DP83867 LOOPCR MMD register written to normal value 0xE721.

Configure 1000M:
  Advertise 1000 full-duplex.
  Restart autonegotiation.
  Poll BMSR/PHYSTS until link and speed/duplex resolve.
  Program DP83867 RGMII RX/TX clock delay controls.

Configure TSE MAC:
  Set MAC_CMDCFG_ETH_SPEED.
  Clear MAC_CMDCFG_ENA_10.
  Clear MAC_CMDCFG_HD_ENA.
  Clear MAC_CMDCFG_LOOP_ENA for normal operation.
  Enable TX and RX after reset.
```

Proof that this behavior was present in passing runs:

```text
DP83867 diag clear: BMCR=0x1140 BISCR=0x0000 LOOPCR=0xE721
Link up successful
Speed and duplex resolved
PHY link is UP.
frames_check_sequence_errors = 0x0
alignment_errors = 0x0
```

### `sources/sw/app_freertos/main.c`

Required behavior added in successive chunks:

```text
Lower ping task priority enough for network service tasks to run.
Create UDP loopback task on port 5002.
Create HTTP server task on port 80.
Serve simple static HTML.
Serve color-bars HTML.
Serve background-image HTML with embedded data URI.
Use desktop_background_image.h for the embedded XRDP/background asset.
Optionally handle GET /bg.jpg.
Track net_proof_status counters in a dedicated section.
```

Proof from history:

```text
UDP_LOOPBACK_RESULT ok=5 count=5
[UDP] loopback task bound on FPGA port 5002
[HTTP] serving simple HTML on FPGA port 80
HTTP/1.1 200 OK
body 180 -> 648 -> 5927 -> 21986 bytes as page content evolved
```

### Test wrappers

Required wrappers:

```text
run_tse_eval_network_smoke.sh
run_tse_eval_udp_loopback.sh
run_tse_eval_http_server.sh
../../tse_jtag_maconly/scripts/with_eval_programmer.py
```

Required wrapper behavior:

```text
Write manifest with SOF and ELF SHA256.
Hold quartus_pgm open at eval prompt.
Set JTAG clock to 6M.
Run jtagconfig --debug.
Read/toggle ISSP for 1000M mode.
Download ELF with niosv-download --use_openocd -g -r.
Capture JTAG UART.
Flush host neighbor entry.
Run host ping/ARP check.
Run UDP or HTTP socket test bound to host IP 10.0.0.1.
Keep HTTP server alive with HTTP_HOLD_SECONDS when requested.
Clean up by sending q to the eval prompt.
```

## Clean Clone Warning From History

Codex history lines:

```text
1802  Pushed color-bar test to AEW2015 fork, but hardware note says local artifacts still differ
1918  Clean clone Quartus rebuild succeeded
2117  New clean-clone SOF/ELF did not produce live HTTP; FCS errors rose
2167  User correctly challenged missing 1000M working changes
2322  Codex identified hw-baseline as the working background HTML design
```

The clean clone can build, but the history says it did not reproduce the proven
working hardware behavior.  The missing piece called out in the history was the
local DP83867 diagnostic clear:

```text
DP83867 diag clear: BMCR=0x1140 BISCR=0x0000 LOOPCR=0xE721
```

The clean rebuilt run showed FreeRTOS boot and an HTTP server start, but live
curl reset/failed and FCS errors climbed.  Therefore, do not use the clean clone
or Git commit state as the definition of the working design.

## Reproduction Checklist

To reproduce the passing hardware result from this history:

```text
1. Work in:
   /home/dev/Atum/agilex3c-nios-ed-hw-baseline/terasic_atum_a3_nano/niosv_g/niosv_g_webserver_ping

2. Build or use:
   sources/hw/output_files/top_time_limited.sof

3. Build or use an app ELF that prints:
   DP83867 diag clear: ...
   [HTTP] serving simple HTML on FPGA port 80
   [UDP] loopback task bound on FPGA port 5002

4. Run with held-open eval programmer:
   HTTP_HOLD_SECONDS=3600 ./run_tse_eval_http_server.sh

5. Confirm:
   Eval prompt detected; programmer remains open
   JTAG clock speed 6 MHz
   eth_mode=1
   ena_10=0
   rxclk_count nonzero
   PHY link is UP.
   ping 10.0.0.2 works
   ARP resolves to 02:cf:46:29:04:b4
   HTTP/1.1 200 OK
   frames_check_sequence_errors = 0x0
   alignment_errors = 0x0
```

Known useful curl command:

```sh
curl --interface enp5s0 http://10.0.0.2/
```

More verbose fetch:

```sh
curl --interface enp5s0 -v http://10.0.0.2/
```

## Open Risk

The exact source state for every passing ELF hash is not recoverable from the
current Git history.  The Codex history and manifests preserve the behavioral
trail and hashes, but not every intermediate source snapshot.

Important hashes from the history/logs:

```text
SOF used repeatedly by passing hw-baseline runs:
40b92e2259a97a7d141d390675e3537186fe3b1bf84b2fcb62c1968e309a07b4

Network smoke ELF:
ae3acfa0ab9f0298bbfb5a1ea31d1198fdfaa7a90251fabd4fa5ad4fe7a624d1

UDP loopback ELF:
7e3ce8f79b9916121151f5fa467bd3b7e5f90d8b8d32f085ebd3558b7be74aab

Simple screenshot HTTP ELF:
e602150317b0f5aa2f0f12207f6e06b0433f526f2a5db584da4f6ae235cb3685

Earlier desktop/background host ELF from manifest:
0412d4b81099c375b706fa8384768977df0874a72a35d5e12ffbf342c6c5c2d9

Later rerun ELF that failed to boot normally:
3a22bc503ef4f0601ba57973f486bfbbdaa680acf8e9a7d3deffc5a6efc527b2
```

For any future squashed commit or clean rebuild, the acceptance criterion should
be a fresh hardware run matching the checklist above, not matching any Git
commit message.
