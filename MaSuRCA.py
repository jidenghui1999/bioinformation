#!/usr/bin/env python
#-*- coding utf-8 -*-
#creat the config file
#usage: python --qc_path --list_qc --masurca_path --bampath 
import os
import sys
import re
import argparse
#############################################################################
#parse the arguments
root_cwd = os.getcwd()
parser = argparse.ArgumentParser(description="correct the pacbio with short reads by MaSuRCA")
parser.add_argument('-q','--qc_path',help='the QC path of small insert size(=<700)',required=True)
parser.add_argument('-l','--list_qc',help='the QC list of small insert size(=<700)',required= True)
parser.add_argument('-m','--masurca_path',help='the path of masurca for superreads(optional,default path is current path)',default='%s'%root_cwd)
parser.add_argument('-i','--bampath',help='the path of pacbio data',required=True)
parser.add_argument('-o','--fasta_path',help='the path of bam2fasta (optional,default path is current path)',default='%s'%root_cwd)

argv=vars(parser.parse_args())
QC_path = argv['qc_path']
list = argv['list_qc']
goalpath = argv['masurca_path']
os.chdir(goalpath)
config_file = open(r'./config','a')

bamfile_path =argv['bampath']
out_path_list = argv['fasta_path'].strip().rstrip('/').split('/')
out_path_list.append('bamlist')
out_path = '/'.join(out_path_list)
os.mkdir(out_path)
os.system('cp /TJPROJ1/DENOVO/PROJECT/yangxinchao_3485/scripts/masurca/create_masurca2pacbio.py ./')

begin = '''
# example configuration file 
# DATA is specified as type {PE,JUMP,OTHER,PACBIO} and 5 fields:
# 1)two_letter_prefix 2)mean 3)stdev 4)fastq(.gz)_fwd_reads
# 5)fastq(.gz)_rev_reads. The PE reads are always assumed to be
# innies, i.e. --->.<---, and JUMP are assumed to be outties
# <---.--->. If there are any jump libraries that are innies, such as
# longjump, specify them as JUMP and specify NEGATIVE mean. Reverse reads
# are optional for PE libraries and mandatory for JUMP libraries. Any
# OTHER sequence data (454, Sanger, Ion torrent, etc) must be first
# converted into Celera Assembler compatible .frg files (see
# http://wgs-assembler.sourceforge.com)
DATA
'''
end = '''
#pacbio reads must be in a single fasta file! make sure you provide absolute path
END

PARAMETERS
#this is k-mer size for deBruijn graph values between 25 and 127 are supported, auto will compute the optimal size based on the read data and GC content
GRAPH_KMER_SIZE = auto
#set this to 1 for all Illumina-only assemblies
#set this to 1 if you have less than 20x long reads (454, Sanger, Pacbio) and less than 50x CLONE coverage by Illumina, Sanger or 454 mate pairs
#otherwise keep at 0
USE_LINKING_MATES = 0
#this parameter is useful if you have too many Illumina jumping library mates. Typically set it to 60 for bacteria and 300 for the other organisms 
LIMIT_JUMP_COVERAGE = 300
#these are the additional parameters to Celera Assembler.  do not worry about performance, number or processors or batch sizes -- these are computed automatically. 
#set cgwErrorRate=0.25 for bacteria and 0.1<=cgwErrorRate<=0.15 for other organisms.
CA_PARAMETERS =  cgwErrorRate=0.15
#minimum count k-mers used in error correction 1 means all k-mers are used.  one can increase to 2 if Illumina coverage >100
KMER_COUNT_THRESHOLD = 1
#auto-detected number of cpus to use
NUM_THREADS = 40
#this is mandatory jellyfish hash size -- a safe value is estimated_genome_size*estimated_coverage
JF_SIZE = 44000000000
#set this to 1 to use SOAPdenovo contigging/scaffolding module.  Assembly will be worse but will run faster. Useful for very large (>5Gbp) genomes
SOAP_ASSEMBLY=1
END
'''
config_file.write(begin)
f = open(QC_path + '/' + list ,'r')
count = 1
for eachlib in f:
    file_name = eachlib.strip().split()[0]
    insert_size = int(eachlib.strip().split()[1])
    if insert_size <= 700:
        config_file.write('PE= p%d %d %d %s/%s/03.Qc/%s_1_clean.fq.gz %s/%s/03.Qc/%s_2_clean.fq.gz\n'%(count,insert_size,insert_size/10,QC_path,file_name,file_name,QC_path,file_name,file_name))
        count = count + 1
config_file.write(end)
f.close()
config_file.close()
os.system('ln -s /TJPROJ1/DENOVO/PROJECT/libenping/Software/MaSuRCA-3.2/bin/masurca ./')
os.system('masurca config')

os.chdir(bamfile_path)
command1 = "find -L %s -name '*subreads.bam'|sed 's#%s#ln -s %s#g'|sed 's#subreads.bam#subreads.bam ./#g' > %s/bam.txt"%(bamfile_path,bamfile_path,bamfile_path,out_path)
command2 = "find -L %s -name '*subreads.bam.pbi'|sed 's#%s#ln -s %s#g'|sed 's#subreads.bam.pbi#subreads.bam.pbi ./#g' > %s/pbi.txt"%(bamfile_path,bamfile_path,bamfile_path,out_path)
os.system(command1)
os.system(command2)
os.chdir(out_path)
os.system('sh bam.txt')
os.system('sh pbi.txt')

list = os.popen('ls|grep \'bam$\'').read().split('\n')
for name in list:
    if name.endswith('.bam'):
        with open(name+'.sh','w') as trans:
            trans.write('/PUBLIC/software/DENOVO/bio/software/assemble/bam2fastx/build/bam2fasta -u '+name+' -o '+name)
        cmd = 'qsub -cwd -l vf=1G,p=1 '+name+'.sh'
        os.system(cmd)
#os.system('cp /TJPROJ1/DENOVO/PROJECT/yangxinchao_3485/scripts/masurca/creat_bam2fa.py creat_bam2fa.py')
#os.system('python creat_bam2fa.py %s'%out_path)
