# Source this script to add these extensions to 

_helpersdir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo SPACK_ROOT: ${SPACK_ROOT}
echo spack exe: $(which spack)
if [ $? != 0 ]; then echo "spack executable not found"; fi

spack config add "config:extensions:[$_helpersdir]"
spack commands --update-completion
. $SPACK_ROOT/share/spack/setup-env.sh
