# (C) 2001-2024 Intel Corporation. All rights reserved.
# Your use of Intel Corporation's design tools, logic functions and other 
# software and tools, and its AMPP partner logic functions, and any output 
# files from any of the foregoing (including device programming or simulation 
# files), and any associated documentation or information are expressly subject 
# to the terms and conditions of the Intel Program License Subscription 
# Agreement, Intel FPGA IP License Agreement, or other applicable 
# license agreement, including, without limitation, that your use is for the 
# sole purpose of programming logic devices manufactured by Intel and sold by 
# Intel or its authorized distributors.  Please refer to the applicable 
# agreement for further details.
 
 
# (C) 2001-2024 Intel Corporation. All rights reserved.
# Your use of Intel Corporation's design tools, logic functions and other 
# software and tools, and its AMPP partner logic functions, and any output 
# files from any of the foregoing (including device programming or simulation 
# files), and any associated documentation or information are expressly subject 
# to the terms and conditions of the Intel Program License Subscription 
# Agreement, Intel FPGA IP License Agreement, or other applicable 
# license agreement, including, without limitation, that your use is for the 
# sole purpose of programming logic devices manufactured by Intel and sold by 
# Intel or its authorized distributors.  Please refer to the applicable 
# agreement for further details.
 
 
#
##################################################################################
# Python code to generate the .sof file from qsys and qpf tcl files
 
# Requirements to successfully run this script:
# Python version >= 3.5
# Quartus environment
 
#author: Altera
#version: 14 SEPT 2025
####################################################################################
# import libraries
import subprocess
import sys
import os, glob, re, shutil
 
# define directories
cwd_1 = "./hw"
cwd_2 = "./scripts"
 
# Find project name & qpf, qsys tcl directories
os.chdir(cwd_2)
cntr=0
qpf_name = ''
qsys_tcl = ''
qpf_tcl = ''
qpf_tcl_dir = ''
qsys_tcl_dir = ''

# Prefer canonical script names when available.
script_files = sorted(glob.glob("*.tcl*"))
if "top.tcl" in script_files:
    qpf_tcl = "top.tcl"
    qpf_tcl_dir = "../scripts/" + qpf_tcl
if "design_export.tcl" in script_files:
    qsys_tcl = "design_export.tcl"
    qsys_tcl_dir = "../scripts/" + qsys_tcl

for file in script_files:
    if ".gz" in file:
        gz_unzip = subprocess.Popen("gzip -d {}".format(file),shell=True)
        gz_unzip.wait()
        sep_qproj = '.gz'
        file = file.split(sep_qproj,1)[0]
    with open (file,'r') as f1:
        line_f1 = f1.readlines()
        for i,line in enumerate(line_f1):
            if 'project_exists ' in line:
                if not qpf_tcl:
                    qpf_tcl = file
                    qpf_tcl_dir = "../scripts/" + qpf_tcl
                qpf_name = line_f1[i].replace(" ","").split("project_exists",1)[1]
                qpf_name = re.sub(r"[{}]",'',qpf_name).replace(']','').rstrip()
            elif 'project_new -overwrite' in line:
                if not qpf_tcl:
                    qpf_tcl = file
                    qpf_tcl_dir = "../scripts/" + qpf_tcl
                qpf_name = line_f1[i].replace(" ","").split("project_new-overwrite",1)[1].rstrip()             
            elif ('create_system ' in line) or ('set sys_name ' in line):
                if not qsys_tcl:
                    qsys_tcl = file
                    qsys_tcl_dir = "../scripts/" + qsys_tcl
                #qsys_name = line_f1[i].replace(" ","").split("create_system",1)[1]
 
qpf_dir = qpf_name +".qpf"
 
# print(qpf_name)
# print(qpf_dir)
# print(qsys_tcl_dir)
os.chdir("../")
 
logfile = open('logfile.txt', 'wb')
 
# Generate qpf file

custom_logic_dir = os.path.join("custom_logic", "core_sdram_axi")
for filename in [
    "core_sdram_axi4_hw.tcl",
    "sdram_axi.v",
    "sdram_axi_core.v",
    "sdram_axi_pmem.v",
]:
    shutil.copy2(os.path.join(custom_logic_dir, filename), os.path.join(cwd_1, filename))

generate_qpf = subprocess.Popen(["quartus_sh","-t",str(qpf_tcl_dir)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
for line in generate_qpf.stdout:
    logfile.write(line)
generate_qpf.wait()

vds_system_dir = os.path.join(cwd_1, "src", "vds", "qsys_top")
vds_ip_names = [
    "qsys_top_core_sdram_axi4_0.ip",
    "qsys_top_intel_niosv_g_4.ip",
    "qsys_top_proc_clk.ip",
    "qsys_top_proc_rst.ip",
    "qsys_top_sdram_clock.ip",
    "qsys_top_sdram_reset.ip",
    "qsys_top_sys_cpu_ram.ip",
    "qsys_top_sys_desc_mem.ip",
    "qsys_top_sys_jtag_uart.ip",
    "qsys_top_sys_tse.ip",
    "qsys_top_sys_tse_msgdma_rx.ip",
    "qsys_top_sys_tse_msgdma_tx.ip",
]
vds_ip_files = [os.path.join(vds_system_dir, "ip", name) for name in vds_ip_names]
if any(not os.path.exists(path) for path in vds_ip_files):
    generate_vds_ip = subprocess.Popen(
        [
            "qsys-script",
            "--script=qsys_top.tcl",
            "--quartus-project=../../../{}".format(qpf_dir),
            "--rev={}".format(qpf_name),
            "--search-path=../../../../custom_logic/core_sdram_axi/**/*,$",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=vds_system_dir,
    )
    for line in generate_vds_ip.stdout:
        logfile.write(line)
    generate_vds_ip.wait()
    if generate_vds_ip.returncode != 0:
        logfile.close()
        sys.exit(generate_vds_ip.returncode)
    qsf_path = os.path.join(cwd_1, "{}.qsf".format(qpf_name))
    with open(qsf_path, "r") as qsf:
        qsf_lines = qsf.readlines()
    with open(qsf_path, "w") as qsf:
        for line in qsf_lines:
            if "QSYS_FILE src/vds/qsys_top/qsys_top.qsys" not in line:
                qsf.write(line)
else:
    logfile.write(b"INFO: Existing qsys_top VDS IP descriptors detected. Skipping qsys_top.tcl step.\n")
 
# Open a project
# quartus_sh --flow compile <project_name>
# open_qpf = subprocess.Popen(["quartus_sh","--flow","compile",str(qpf_name)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
# for line in open_qpf.stdout:
#     logfile.write(line)
# open_qpf.wait()
 
# Generate qsys file only when the VDS system file is not already present.
existing_vds = os.path.join(cwd_1, "src", "vds", "qsys_top", "qsys_top.vds")
if (qsys_tcl_dir != '') and (not os.path.exists(existing_vds)):
    generate_qsys = subprocess.Popen(["quartus_sh","-t",str(qsys_tcl_dir)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
    for line in generate_qsys.stdout:
        logfile.write(line)
    generate_qsys.wait()
else:
    logfile.write(b"INFO: Existing qsys_top.vds detected. Skipping design_export step.\n")
 
# # Generate qsys file
# generate_qsys = subprocess.Popen(["qsys-script","--script={}".format(qsys_tcl_dir),"--quartus-project={}".format(qpf_dir)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
# for line in generate_qsys.stdout:
#     logfile.write(line)
# generate_qsys.wait()
 
# Generate ip
generate_ip = subprocess.Popen(["quartus_ipgenerate","{}".format(qpf_dir)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
for line in generate_ip.stdout:
    logfile.write(line)
generate_ip.wait()

for name in vds_ip_names:
    ip_base = os.path.splitext(name)[0]
    generated_dir = os.path.abspath(os.path.join(cwd_1, "gen", "vds", "qsys_top", "ip", ip_base))
    source_dir = os.path.join(vds_system_dir, "ip", ip_base)
    if os.path.isdir(generated_dir) and not os.path.exists(source_dir):
        os.symlink(os.path.relpath(generated_dir, os.path.dirname(source_dir)), source_dir)
 
# quartus_sh --flow compile ${design_top}.qpf
 
# Generate hex file only if helper script is available.
niosv_app_script = "scripts/niosv_app_creation.sh"
if os.path.exists(niosv_app_script):
    app_creation = subprocess.Popen(["niosv-shell < {}".format(niosv_app_script)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell= True)
    for line in app_creation.stdout:
        logfile.write(line)
    app_creation.wait()
else:
    logfile.write(b"WARNING: scripts/niosv_app_creation.sh not found. Skipping niosv-shell step.\n")
 
 
# # Compile Flow
# compile_flow = subprocess.Popen(["quartus_sh", "--flow", "compile","{}".format(qpf_dir)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
# for line in compile_flow.stdout:
#     logfile.write(line)
# compile_flow.wait()
 
# Synthesis
quartus_sync = subprocess.Popen(["quartus_syn","{}".format(qpf_dir)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
for line in quartus_sync.stdout:
    logfile.write(line)
quartus_sync.wait()
 
# Fitting
quartus_fit = subprocess.Popen(["quartus_fit","{}".format(qpf_dir)],stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
for line in quartus_fit.stdout:
    logfile.write(line)
quartus_fit.wait()
 
# Timing analysis
quartus_sta = subprocess.Popen(["quartus_sta","{}".format(qpf_name),"-c","{}".format(qpf_name), "--mode=finalize"],stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
for line in quartus_sta.stdout:
    logfile.write(line)
quartus_sta.wait()
 
# Assembly
quartus_asm = subprocess.Popen(["quartus_asm","{}".format(qpf_dir)],stdout=subprocess.PIPE, stderr=subprocess.STDOUT,cwd=cwd_1)
for line in quartus_asm.stdout:
    logfile.write(line)
quartus_asm.wait()
