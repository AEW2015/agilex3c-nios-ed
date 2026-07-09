#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCES_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

export PATH=/opt/altera/niosv/bin:/opt/altera/riscfree/toolchain/riscv32-unknown-elf/bin:/opt/altera/questa_fse/bin:/opt/altera/quartus/bin:/opt/altera/quartus/sopc_builder/bin:$PATH
export LM_LICENSE_FILE="${LM_LICENSE_FILE:-/home/dev/License.dat}"
export SALT_LICENSE_SERVER="${SALT_LICENSE_SERVER:-/home/dev/License.dat}"

cd "$SOURCES_DIR"

for file in core_sdram_axi4_hw.tcl sdram_axi.v sdram_axi_core.v sdram_axi_pmem.v; do
  cp "custom_logic/core_sdram_axi/$file" "hw/$file"
done

if [[ ! -f hw/top.qpf || ! -f hw/top.qsf ]]; then
  (cd hw && quartus_sh -t ../scripts/top.tcl)
fi

VDS_DIR="hw/src/vds/qsys_top"
VDS_IP_FILES=(
  qsys_top_core_sdram_axi4_0.ip
  qsys_top_intel_niosv_g_4.ip
  qsys_top_proc_clk.ip
  qsys_top_proc_rst.ip
  qsys_top_sdram_clock.ip
  qsys_top_sdram_reset.ip
  qsys_top_sys_cpu_ram.ip
  qsys_top_sys_desc_mem.ip
  qsys_top_sys_jtag_uart.ip
  qsys_top_sys_tse.ip
  qsys_top_sys_tse_msgdma_rx.ip
  qsys_top_sys_tse_msgdma_tx.ip
)

missing_vds_ip=0
for file in "${VDS_IP_FILES[@]}"; do
  if [[ ! -f "$VDS_DIR/ip/$file" ]]; then
    missing_vds_ip=1
    break
  fi
done

if [[ "$missing_vds_ip" == "1" ]]; then
  (
    cd "$VDS_DIR"
    qsys-script \
      --script=qsys_top.tcl \
      --quartus-project=../../../top.qpf \
      --rev=top \
      '--search-path=../../../../custom_logic/core_sdram_axi/**/*,$'
  )
  tmp_qsf="$(mktemp)"
  grep -v 'QSYS_FILE src/vds/qsys_top/qsys_top.qsys' hw/top.qsf > "$tmp_qsf"
  mv "$tmp_qsf" hw/top.qsf
fi

BSP_DIR="sw/bsp_freertos"
BSP_SETTINGS="$BSP_DIR/settings.bsp"
APP_DIR="sw/app_freertos"
PATCHED_TSE_DIR="sw/AlteraTSE"
BSP_TSE_DIR="$BSP_DIR/FreeRTOS_TCP_IP/source/portable/NetworkInterface/AlteraTSE"

if [[ "${FORCE_REGENERATE_BSP:-0}" == "1" ]]; then
  rm -rf "$BSP_DIR"
fi

if [[ ! -f "$BSP_SETTINGS" || ! -f "$BSP_DIR/CMakeLists.txt" ]]; then
  rm -rf "$BSP_DIR"
  niosv-bsp \
    --create \
    --no-default \
    --system=./hw/src/vds/qsys_top/qsys_top.vds \
    --quartus_project=./hw/top.qpf \
    --type=freertos \
    -cmd="enable_sw_package altera_freertos_tcpip" \
    "$BSP_SETTINGS" \
    --script=./sw/bsp_settings.tcl
fi

rm -rf "$BSP_TSE_DIR"
mkdir -p "$BSP_TSE_DIR"
cp -a "$PATCHED_TSE_DIR/." "$BSP_TSE_DIR/"

cmake -S "$APP_DIR" -B "$APP_DIR/build"
cmake --build "$APP_DIR/build" -- -j"${JOBS:-$(nproc)}"
