#!/usr/bin/env bash
set -euo pipefail

# Check ONIOM output files, generate continuation inputs when needed,
# unfreeze successful frozen optimizations, and move successful unfrozen
# jobs to the next workflow step.
#
# Inputs:
#   ONIOM .out and matching .com files
#   optional frozen.txt constraint file
#
# Outputs:
#   continuation .com files for failed jobs
#   unfrozen .com files for successful frozen jobs
#   successful outputs moved to the next workflow step
#   summary printed to screen

next_step_dir="../step7"

touch rerun.txt unfreeze.txt ready.txt

shopt -s nullglob

for file in *.out; do
    newname="${file%.out}"

    if grep -q "Normal termination" "$file"; then
        if [[ "$file" == *"-freeze"* ]]; then
            base="${newname%-freeze}"

            oniomlog.pl -oi -t "$newname.com" -i "$file" -fo "$base-temp.com" -fn
            sed -e "s/modredundant/ts/g" -i "$base-temp.com"

            if [[ ! -f frozen.txt ]]; then
                cp ../step5/frozen.txt ./frozen.txt
            fi

            python3 remove_frozen_coords.py "$base-temp.com" "$base-unfreeze.com" frozen.txt
            rm -f "$base-temp.com"

            echo "$file unfrozen and saved to $base-unfreeze.com." >> unfreeze.txt
            continue
        else
       		mv "$file" "$next_step_dir/"
        	mv "$newname.com" "$next_step_dir/"
        	echo "$file transferred to next step." >> ready.txt
	fi
    else
        oniomlog.pl -oi -t "$newname.com" -i "$file" -fo "$newname-cont.com" -fn
        echo "$file had a problem. Check output file. Continuation job $newname-cont.com created." >> rerun.txt
    fi
done

echo "===================="
echo "File manip.:"
echo ""
echo "RERUN:"
echo ""
cat rerun.txt
echo ""
echo "UNFREEZE:"
echo ""
cat unfreeze.txt
echo ""
echo "READY:"
echo ""
cat ready.txt
echo ""
echo "===================="

rm -f rerun.txt unfreeze.txt ready.txt
