#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

# Generate ONIOM Gaussian input files from centered Amber topology/restart files.
#
# Inputs:
#   *-cen.pdb
#   matching *-cen.parm7 and *-cen.rst7 files
#   freeze_threshold
#   corelist.txt
#   pdb2oniom installation directory
#   theory
#   basis
#   overall_mult
#   ligand_charge
#   ligand_mult
#
# Optional Arguments:
#   --mix
#   --mix-only
#   --ts
#   --freeze <constraints_file>
#   --rigid
#
# Outputs:
#   *-oniom.com
#   optional *-mix.com, *-freeze.com, and *-rigid.com variants

usage() {
    echo "Usage:"
    echo "  $0 <freeze_threshold> <corelist.txt> <pdb2oniom_dir> <theory> <basis> <overall_mult> <ligand_charge> <ligand_mult> [options]"
    echo
    echo "Options:"
    echo "  --mix                  Create guess=mix copies while keeping regular inputs"
    echo "  --mix-only             Replace regular inputs with guess=mix versions"
    echo "  --ts                   Use transition-state optimization keywords"
    echo "  --freeze <file>        Create frozen-coordinate variants using constraints file"
    echo "  --rigid                Create rigid-residue variants"
    echo
    echo "Example:"
    echo "  $0 5 corelist.txt ~/software/pdb2oniom uwb97xd def2svp 1 -1 1 --mix --ts --freeze frozen.txt --rigid"
}

if [ "$#" -lt 8 ]; then
    usage
    exit 1
fi

freeze_threshold="$1"
corelist="$2"
pdb2oniom_dir="$3"
theory="$4"
basis="$5"
overall_mult="$6"
ligand_charge="$7"
ligand_mult="$8"
shift 8

make_mix=false
mix_only=false
is_ts=false
freeze_file=""
make_rigid=false

while [ "$#" -gt 0 ]; do
    case "$1" in
        --mix)
            make_mix=true
            ;;
        --mix-only)
            make_mix=true
            mix_only=true
            ;;
        --ts)
            is_ts=true
            ;;
        --freeze)
            if [ "$#" -lt 2 ]; then
                echo "Error: --freeze requires a constraints file."
                exit 1
            fi
            freeze_file="$2"
            shift
            ;;
        --rigid)
            make_rigid=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

if [[ -n "$freeze_file" && "$is_ts" != true ]]; then
    echo "Error: --freeze requires --ts."
    exit 1
fi

if [[ -n "$freeze_file" && ! -f "$freeze_file" ]]; then
    echo "Error: freeze constraints file not found: $freeze_file"
    exit 1
fi

if [[ "$make_mix" == true && ! "$theory" =~ ^u ]]; then
    echo "Calculations with guess=mix should be unrestricted."
    echo "Using unrestricted theory: u${theory}"
    theory="u${theory}"
fi

rm -f *-mix.com *-freeze.com *-rigid.com *-f-temp.com

for file in *-cen.pdb; do
    newname="${file%.pdb}"
    bash base_oniom_file_builder.sh "$newname" "$freeze_threshold" "$corelist" "$pdb2oniom_dir"
done

oniom_files=( *-oniom.com )

if [ "${#oniom_files[@]}" -eq 0 ]; then
    echo "Error: no *-oniom.com files were generated."
    exit 1
fi

echo "All base ONIOM input files generated."

sed -i "s/#p/#/g" "${oniom_files[@]}"

if [[ "$make_mix" == true ]]; then
    for file in *-oniom.com; do
        newname="${file%.com}"

        if [[ "$mix_only" == true ]]; then
            mv "$file" "$newname-mix.com"
        else
            cp "$file" "$newname-mix.com"
        fi
    done

    sed -i "s/Amber=(FirstEquiv)/Amber=(FirstEquiv) guess=mix/g" *-mix.com
fi

if [[ "$is_ts" == true ]]; then
    sed -i \
        "s/opt=(quadmac,calcfc,maxstep=5)/opt=(quadmac,calcfc,ts,maxstep=5,noeigentest) freq=noraman/g" \
        *-oniom*.com
fi

if [[ -n "$freeze_file" ]]; then
    for file in *-oniom*.com; do
        newname="${file%.com}"
        cp "$file" "$newname-f-temp.com"
    done

    sed -i \
        "s/opt=(quadmac,calcfc,ts,maxstep=5,noeigentest) freq=noraman/opt=(quadmac,calcfc,modredundant,maxstep=5,noeigentest) freq=noraman/g" \
        *-oniom*-f-temp.com

    for file in *-f-temp.com; do
        newname="${file%-f-temp.com}"
        python3 freeze_coords.py "$file" "$newname-freeze.com" "$freeze_file"
        rm -f "$file"
    done
fi

sed -i "s/b3lyp/$theory/g" *oniom*.com
sed -i "s/6-31g(d,p)/$basis/g" *oniom*.com

sed -i \
    "s/1 0 1 0 1/$overall_mult $ligand_charge $ligand_mult $ligand_charge $ligand_mult/g" \
    *oniom*.com

if [[ "$make_rigid" == true ]]; then
    bash rigid_batch.sh
fi

for file in *oniom*.com; do
    printf "\n\n" >> "$file"
done

echo "All ONIOM input files created successfully."
