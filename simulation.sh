#!/bin/bash
#SBATCH --nodes=1
#SBATCH --partition=gpu1,gpu2,gpu3,gpu4,gpu5,gpu6,cpu1
#SBATCH --cpus-per-task=40
#SBATCH --gres=gpu:0
#SBATCH --job-name=ANSYS
#SBATCH -o ./log/SLURM.%N.%j.out         # STDOUT
#SBATCH -e ./log/SLURM.%N.%j.err         # STDERR


module purge

source ~/miniconda3/etc/profile.d/conda.sh
conda activate pyaedt2026v1

module load ansys-electronics/v252

# export ANSYSEM_ROOT242=/opt/ohpc/pub/Electronics/v242/Linux64
# export PATH=$ANSYSEM_ROOT242/ansysedt/bin:$PATH
# export ANSYSLMD_LICENSE_FILE=1055@172.16.10.81

# unset DISPLAY
# export QT_QPA_PLATFORM=offscreen


# export HOME=/gpfs/home1/r1jae262
# cd /gpfs/home1/r1jae262/ANSYS

# 현재 디렉토리 확인 및 로깅
echo "Current directory: $(pwd)" >&2
echo "Python path: $(which python)" >&2
echo "Python version: $(python --version)" >&2
echo "Starting run.py..." >&2

# run.py 실행 (에러도 stderr로 출력)
python run.py 2>&1

# 종료 코드 확인
exit_code=$?
echo "run.py finished with exit code: $exit_code" >&2
exit $exit_code